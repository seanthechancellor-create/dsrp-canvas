"""
Study Guide Ingestor for DSRP RAG Pipeline

This script:
1. Parses Study Guide PDFs to extract question blocks
2. Uses pgvector for semantic search to find "Source Truth" answers
3. Generates DSRP-based explanations using Ollama/Llama3
4. Exports to RemNote-compatible Markdown format

Usage:
    python study_guide_ingestor.py <path_to_study_guide.pdf> [--output remnote_export.md]
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Optional
from pathlib import Path

# LangChain components
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# PostgreSQL with pgvector
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://dsrp:dsrp_password@localhost:5432/dsrp_canvas")

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# OpenAI fallback (if Ollama unavailable)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

# Number of source chunks to retrieve per question
TOP_K_CHUNKS = 3

# Minimum similarity threshold for relevant chunks
SIMILARITY_THRESHOLD = 0.5


# =============================================================================
# PGVECTOR SEARCH (Consolidated Vector Store)
# =============================================================================

class PgVectorStore:
    """Handles pgvector connection and similarity search."""

    def __init__(self):
        self._pool = None
        self._embeddings = None
        self._use_openai = False
        self._initialize()

    def _initialize(self):
        """Initialize database connection and embedding model."""
        # Try pgvector connection
        try:
            import psycopg_pool
            self._pool = psycopg_pool.ConnectionPool(POSTGRES_URL, min_size=1, max_size=5)
            logger.info("Connected to PostgreSQL with pgvector")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self._pool = None

        # Try Ollama embeddings first
        try:
            self._embeddings = OllamaEmbeddings(
                model=EMBEDDING_MODEL,
                base_url=OLLAMA_BASE_URL
            )
            # Test embedding
            self._embeddings.embed_query("test")
            logger.info(f"Using Ollama embeddings: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Ollama embeddings unavailable: {e}")
            # Fall back to OpenAI
            if OPENAI_API_KEY:
                try:
                    from openai import OpenAI
                    self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
                    self._use_openai = True
                    logger.info("Using OpenAI embeddings as fallback")
                except Exception as e2:
                    logger.error(f"OpenAI also unavailable: {e2}")

    def _get_embedding(self, text: str) -> Optional[list[float]]:
        """Get embedding vector for text."""
        if self._use_openai:
            try:
                response = self._openai_client.embeddings.create(
                    model=OPENAI_EMBEDDING_MODEL,
                    input=text,
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}")
                return None
        elif self._embeddings:
            try:
                return self._embeddings.embed_query(text)
            except Exception as e:
                logger.error(f"Ollama embedding failed: {e}")
                return None
        return None

    def similarity_search(self, query: str, k: int = TOP_K_CHUNKS) -> list[dict]:
        """
        Perform semantic similarity search against Source Truth documents in pgvector.

        Args:
            query: The question text to search for
            k: Number of top results to return

        Returns:
            List of matching chunks with text, similarity score, and source
        """
        if not self._pool:
            logger.warning("pgvector not available")
            return []

        query_embedding = self._get_embedding(query)
        if not query_embedding:
            logger.warning("Failed to generate query embedding")
            return []

        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    # Search document_embeddings table (RAG source truth)
                    cur.execute("""
                        SELECT
                            document_id,
                            chunk_id,
                            filename,
                            content,
                            metadata,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM document_embeddings
                        WHERE 1 - (embedding <=> %s::vector) >= %s
                        ORDER BY similarity DESC
                        LIMIT %s;
                    """, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, k))

                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "text": row[3],
                            "similarity": float(row[5]),
                            "source": row[2] or row[0],  # filename or document_id
                            "metadata": row[4] or {},
                            "document_id": row[0],
                            "chunk_id": row[1],
                        })

                    # Also search source_embeddings for additional context
                    if len(results) < k:
                        cur.execute("""
                            SELECT
                                source_id,
                                chunk_index,
                                content,
                                1 - (embedding <=> %s::vector) as similarity
                            FROM source_embeddings
                            WHERE 1 - (embedding <=> %s::vector) >= %s
                            ORDER BY similarity DESC
                            LIMIT %s;
                        """, (query_embedding, query_embedding, SIMILARITY_THRESHOLD, k - len(results)))

                        for row in cur.fetchall():
                            results.append({
                                "text": row[2],
                                "similarity": float(row[3]),
                                "source": row[0],
                                "metadata": {"chunk_index": row[1]},
                            })

                    # Sort combined results by similarity
                    results.sort(key=lambda x: x["similarity"], reverse=True)
                    return results[:k]

        except Exception as e:
            logger.error(f"pgvector search failed: {e}")
            return []

    def close(self):
        """Close database connection."""
        if self._pool:
            self._pool.close()


# =============================================================================
# PDF PARSING & QUESTION EXTRACTION
# =============================================================================

class StudyGuideParser:
    """Parses study guide PDFs and extracts question blocks using LLM."""

    def __init__(self):
        self.llm = Ollama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1  # Low temperature for consistent extraction
        )

    def load_pdf(self, pdf_path: str) -> str:
        """
        Load and extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If PDF doesn't exist
            Exception: If PDF parsing fails
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if not path.suffix.lower() == ".pdf":
            raise ValueError(f"File is not a PDF: {pdf_path}")

        try:
            logger.info(f"Loading PDF: {pdf_path}")
            loader = PyPDFLoader(str(path))
            pages = loader.load()

            # Combine all pages into single text
            full_text = "\n\n".join([page.page_content for page in pages])
            logger.info(f"Extracted {len(pages)} pages, {len(full_text)} characters")
            return full_text

        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise

    def extract_questions(self, text: str) -> list[dict]:
        """
        Use LLM to identify and extract question blocks from study guide text.

        Args:
            text: Raw text from the study guide PDF

        Returns:
            List of question blocks with question text and options
        """
        extraction_prompt = f"""You are a question extraction assistant. Analyze the following study guide text and extract ALL questions with their multiple choice options.

For each question found, output a JSON object with:
- "question": The full question text
- "options": A list of the answer choices (A, B, C, D, etc.)

Output ONLY a JSON array of question objects. No other text.

If no questions are found, output an empty array: []

Study Guide Text:
---
{text[:15000]}
---

JSON Output:"""

        try:
            logger.info("Extracting questions using LLM...")
            response = self.llm.invoke(extraction_prompt)

            # Parse the JSON response
            # Handle cases where LLM adds markdown code blocks
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            questions = json.loads(response.strip())

            if not isinstance(questions, list):
                questions = [questions] if questions else []

            logger.info(f"Extracted {len(questions)} questions")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response}")
            return []
        except Exception as e:
            logger.error(f"Question extraction failed: {e}")
            return []


# =============================================================================
# DSRP SYNTHESIS
# =============================================================================

class DSRPSynthesizer:
    """Generates DSRP-based explanations using Source Truth context."""

    def __init__(self):
        self.llm = Ollama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.3
        )

    def synthesize_answer(
        self,
        question: dict,
        source_chunks: list[dict]
    ) -> dict:
        """
        Generate a DSRP-based answer using retrieved Source Truth.

        Args:
            question: The question block (question + options)
            source_chunks: Retrieved relevant chunks from Source Truth

        Returns:
            Analysis dict with correct_answer, dsrp_logic, and source_citation
        """
        # Format the source context
        source_context = "\n\n".join([
            f"[Source: {chunk['source']}]\n{chunk['text']}"
            for chunk in source_chunks
        ])

        # Format question with options
        question_text = question.get("question", "")
        options = question.get("options", [])
        options_text = "\n".join(options) if options else ""

        synthesis_prompt = f"""You are a DSRP (Distinctions, Systems, Relationships, Perspectives) analysis expert.

Given a study guide question and authoritative Source Truth documents, determine the correct answer and explain using DSRP thinking patterns.

QUESTION:
{question_text}

OPTIONS:
{options_text}

SOURCE TRUTH (Authoritative Reference Material):
{source_context}

Analyze the question and provide your response as a JSON object with these exact fields:
{{
  "question": "The original question text",
  "correct_answer": "The correct option (e.g., 'A. The answer text') based on Source Truth",
  "dsrp_logic": "A brief DSRP explanation (use patterns like 'The Distinction between X and Y...', 'From a Systems perspective...', 'The Relationship between...', 'From the Perspective of...')",
  "source_citation": "The name of the Source Truth document that supports this answer"
}}

Output ONLY the JSON object, no other text.

JSON:"""

        try:
            response = self.llm.invoke(synthesis_prompt)

            # Clean and parse JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            result = json.loads(response.strip())

            # Ensure all required fields exist
            result.setdefault("question", question_text)
            result.setdefault("correct_answer", "Unable to determine")
            result.setdefault("dsrp_logic", "Analysis unavailable")
            result.setdefault("source_citation", source_chunks[0]["source"] if source_chunks else "No source found")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse synthesis response: {e}")
            return {
                "question": question_text,
                "correct_answer": "Unable to determine",
                "dsrp_logic": "JSON parsing error during synthesis",
                "source_citation": source_chunks[0]["source"] if source_chunks else "No source found"
            }
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {
                "question": question_text,
                "correct_answer": "Error during synthesis",
                "dsrp_logic": str(e),
                "source_citation": "N/A"
            }


# =============================================================================
# REMNOTE EXPORT
# =============================================================================

class RemNoteExporter:
    """Exports analysis results to RemNote-compatible Markdown format."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self._initialize_file()

    def _initialize_file(self):
        """Create or clear the output file with a header."""
        header = f"""# Study Guide Analysis
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Framework: DSRP 4-8-3

---

"""
        self.output_path.write_text(header)
        logger.info(f"Initialized export file: {self.output_path}")

    def append_analysis(self, analysis: dict):
        """
        Append a single analysis to the RemNote export file.

        Args:
            analysis: Dict with question, correct_answer, dsrp_logic, source_citation
        """
        # RemNote format uses :: for flashcard delimiter
        entry = f"""
**Question:** {analysis['question']} ::
**Answer:** {analysis['correct_answer']}
**Logic:** {analysis['dsrp_logic']}
**Source:** {analysis['source_citation']}

---
"""
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def finalize(self, total_questions: int):
        """Add summary footer to the export."""
        footer = f"""
## Summary
- Total Questions Processed: {total_questions}
- Export Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(footer)

        logger.info(f"Export finalized: {self.output_path}")


# =============================================================================
# MAIN PIPELINE
# =============================================================================

class ProgressTracker:
    """Tracks and reports job progress to Redis/backend."""

    def __init__(self, job_id: Optional[str] = None):
        self.job_id = job_id
        self._redis = None
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection for progress tracking."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
        except Exception as e:
            logger.warning(f"Redis unavailable for progress tracking: {e}")
            self._redis = None

    def update(
        self,
        progress: int,
        stage: str,
        message: Optional[str] = None,
        current: Optional[int] = None,
        total: Optional[int] = None,
    ):
        """Update job progress."""
        if not self.job_id or not self._redis:
            return

        try:
            import json
            key = f"dsrp:job:{self.job_id}"
            data = self._redis.get(key)
            if data:
                job = json.loads(data)
                job["progress"] = progress
                job["stage"] = stage
                job["message"] = message
                job["status"] = "running"
                if current is not None:
                    job["current"] = current
                if total is not None:
                    job["total"] = total
                self._redis.setex(key, 86400, json.dumps(job))
        except Exception as e:
            logger.debug(f"Could not update progress: {e}")

    def complete(self, result: dict):
        """Mark job as completed."""
        if not self.job_id or not self._redis:
            return

        try:
            import json
            key = f"dsrp:job:{self.job_id}"
            data = self._redis.get(key)
            if data:
                job = json.loads(data)
                job["progress"] = 100
                job["stage"] = "completed"
                job["status"] = "completed"
                job["result"] = result
                self._redis.setex(key, 86400, json.dumps(job))
        except Exception as e:
            logger.debug(f"Could not mark complete: {e}")

    def fail(self, error: str):
        """Mark job as failed."""
        if not self.job_id or not self._redis:
            return

        try:
            import json
            key = f"dsrp:job:{self.job_id}"
            data = self._redis.get(key)
            if data:
                job = json.loads(data)
                job["stage"] = "failed"
                job["status"] = "failed"
                job["error"] = error
                self._redis.setex(key, 86400, json.dumps(job))
        except Exception as e:
            logger.debug(f"Could not mark failed: {e}")


class StudyGuideIngestor:
    """
    Main pipeline orchestrator for study guide ingestion.

    Coordinates:
    1. PDF parsing
    2. Question extraction
    3. Vector similarity search (pgvector)
    4. DSRP synthesis
    5. RemNote export
    """

    def __init__(self, output_path: str = "remnote_export.md", job_id: Optional[str] = None):
        self.parser = StudyGuideParser()
        self.vector_store = PgVectorStore()
        self.synthesizer = DSRPSynthesizer()
        self.exporter = RemNoteExporter(output_path)
        self.processed_count = 0
        self.progress = ProgressTracker(job_id)
        self.job_id = job_id

    def process(self, pdf_path: str) -> int:
        """
        Process a study guide PDF through the full pipeline.

        Args:
            pdf_path: Path to the study guide PDF

        Returns:
            Number of questions successfully processed
        """
        logger.info(f"Starting study guide ingestion: {pdf_path}")
        self.progress.update(0, "parsing", "Loading PDF...")

        # Step 1: Parse PDF
        try:
            text = self.parser.load_pdf(pdf_path)
            self.progress.update(10, "parsing", "PDF loaded successfully")
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            self.progress.fail(f"PDF parsing failed: {e}")
            return 0

        # Step 2: Extract questions
        self.progress.update(15, "extracting", "Extracting questions from PDF...")
        questions = self.parser.extract_questions(text)
        if not questions:
            logger.warning("No questions extracted from PDF")
            self.progress.fail("No questions found in PDF")
            return 0

        self.progress.update(25, "extracting", f"Found {len(questions)} questions")
        logger.info(f"Processing {len(questions)} questions...")

        # Step 3-5: For each question, retrieve, synthesize, and export
        total_questions = len(questions)
        for i, question in enumerate(questions, 1):
            question_text = question.get("question", "")
            if not question_text:
                logger.warning(f"Skipping question {i}: empty question text")
                continue

            # Calculate progress (25% to 95% for processing)
            progress_pct = 25 + int((i / total_questions) * 70)
            self.progress.update(
                progress_pct,
                "processing",
                f"Processing question {i}/{total_questions}",
                current=i,
                total=total_questions,
            )

            logger.info(f"[{i}/{total_questions}] Processing: {question_text[:50]}...")

            # Step 3: Vector similarity search
            source_chunks = self.vector_store.similarity_search(
                question_text,
                k=TOP_K_CHUNKS
            )

            if not source_chunks:
                logger.warning(f"No relevant sources found for question {i}")
                source_chunks = [{"text": "No source found", "source": "N/A", "similarity": 0}]

            # Step 4: DSRP synthesis
            analysis = self.synthesizer.synthesize_answer(question, source_chunks)

            # Step 5: Export to RemNote
            self.exporter.append_analysis(analysis)
            self.processed_count += 1

        # Finalize export
        self.progress.update(95, "finalizing", "Generating output file...")
        self.exporter.finalize(self.processed_count)

        # Mark complete
        result = {
            "questions_processed": self.processed_count,
            "questions_total": total_questions,
            "output_file": str(self.exporter.output_path),
        }
        self.progress.complete(result)

        logger.info(f"Ingestion complete: {self.processed_count}/{total_questions} questions processed")
        return self.processed_count

    def close(self):
        """Clean up resources."""
        self.vector_store.close()


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Ingest a Study Guide PDF and generate DSRP-analyzed RemNote flashcards"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the study guide PDF file"
    )
    parser.add_argument(
        "--output", "-o",
        default="remnote_export.md",
        help="Output path for RemNote Markdown file (default: remnote_export.md)"
    )
    parser.add_argument(
        "--model", "-m",
        default=OLLAMA_MODEL,
        help=f"Ollama model to use (default: {OLLAMA_MODEL})"
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=TOP_K_CHUNKS,
        help=f"Number of source chunks to retrieve per question (default: {TOP_K_CHUNKS})"
    )
    parser.add_argument(
        "--job-id", "-j",
        default=None,
        help="Job ID for progress tracking (enables Redis progress updates)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Update globals from args
    global OLLAMA_MODEL, TOP_K_CHUNKS
    OLLAMA_MODEL = args.model
    TOP_K_CHUNKS = args.top_k

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run the pipeline with optional job tracking
    ingestor = StudyGuideIngestor(output_path=args.output, job_id=args.job_id)
    try:
        processed = ingestor.process(args.pdf_path)
        if processed > 0:
            print(f"\n✓ Successfully processed {processed} questions")
            print(f"✓ Output written to: {args.output}")
            if args.job_id:
                print(f"✓ Job ID: {args.job_id}")
            sys.exit(0)
        else:
            print("\n✗ No questions were processed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        if args.job_id:
            ingestor.progress.fail("Cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        if args.job_id:
            ingestor.progress.fail(str(e))
        sys.exit(1)
    finally:
        ingestor.close()


if __name__ == "__main__":
    main()
