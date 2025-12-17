#!/usr/bin/env python3
"""
DSRP Knowledge Ingestion Pipeline

This is the main entry point for ingesting documents into the DSRP knowledge system.
It processes documents through these stages:

1. INGEST: Load PDF or text files from the inbox folder
2. CHUNK: Split text into manageable pieces (500 tokens each)
3. EMBED: Generate vector embeddings for semantic search
4. STORE EPISODIC: Save chunks + embeddings to MongoDB
5. EXTRACT DSRP: Use Claude to identify DSRP patterns in each chunk
6. STORE SEMANTIC: Save structured DSRP knowledge to TypeDB

Usage:
    python ingest.py                     # Process all files in ./documents/inbox
    python ingest.py --file my_doc.pdf   # Process a specific file
    python ingest.py --watch             # Watch folder for new files

Author: DSRP Canvas Team
"""

import os
import sys
import json
import uuid
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# PDF processing
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    print("Warning: pypdf not installed. PDF support disabled. Run: pip install pypdf")

# Text chunking
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Embeddings (local, no API key needed)
from sentence_transformers import SentenceTransformer

# LLM for DSRP extraction
import anthropic

# Our services
from services.mongodb_service import MongoDBService
from services.typedb_service import TypeDBService
from prompts.dsrp_extraction import get_extraction_prompt, DSRP_OUTPUT_SCHEMA

# JSON validation
import jsonschema

# =============================================================================
# CONFIGURATION
# =============================================================================

# Set up logging with nice formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent  # dsrp-canvas root
INBOX_DIR = BASE_DIR / "documents" / "inbox"
PROCESSED_DIR = BASE_DIR / "documents" / "processed"

# Chunking settings
CHUNK_SIZE = 1500  # Characters (roughly 375 tokens)
CHUNK_OVERLAP = 200  # Characters of overlap between chunks

# Embedding model (runs locally, no API needed)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions, fast and good

# LLM settings
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Good balance of speed and quality


# =============================================================================
# PIPELINE CLASS
# =============================================================================

class DSRPIngestionPipeline:
    """
    The main pipeline class that orchestrates document ingestion.

    Think of this as an assembly line:
    Document -> Chunks -> Embeddings -> MongoDB -> DSRP Extraction -> TypeDB
    """

    def __init__(self):
        """Initialize all the components of the pipeline."""
        logger.info("=" * 60)
        logger.info("DSRP Knowledge Ingestion Pipeline")
        logger.info("=" * 60)

        # Create directories if they don't exist
        INBOX_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize the text splitter (for chunking)
        # RecursiveCharacterTextSplitter tries to split on paragraphs, then
        # sentences, then words - keeping semantic units together
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Priority order
        )
        logger.info(f"Text splitter: chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")

        # Initialize the embedding model (downloads on first run, ~90MB)
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Embedding dimensions: {self.embedding_model.get_sentence_embedding_dimension()}")

        # Initialize MongoDB (episodic memory)
        logger.info("Connecting to MongoDB...")
        self.mongodb = MongoDBService()

        # Initialize TypeDB (semantic memory)
        logger.info("Connecting to TypeDB...")
        self.typedb = TypeDBService()

        # Initialize Claude client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set! DSRP extraction will be skipped.")
            self.claude = None
        else:
            self.claude = anthropic.Anthropic(api_key=api_key)
            logger.info("Claude client initialized")

        logger.info("Pipeline initialization complete!")
        logger.info("-" * 60)

    def process_file(self, file_path: Path) -> dict:
        """
        Process a single document through the entire pipeline.

        Args:
            file_path: Path to the PDF or text file

        Returns:
            Summary of processing results
        """
        logger.info(f"Processing: {file_path.name}")

        # Generate a unique ID for this document
        document_id = str(uuid.uuid4())

        # Determine file type and extract text
        file_type = file_path.suffix.lower()

        if file_type == ".pdf":
            text = self._extract_pdf_text(file_path)
        elif file_type in [".txt", ".md", ".text"]:
            text = file_path.read_text(encoding="utf-8")
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return {"error": f"Unsupported file type: {file_type}"}

        if not text or len(text.strip()) < 50:
            logger.error("No text extracted from document")
            return {"error": "No text extracted"}

        logger.info(f"Extracted {len(text):,} characters of text")

        # STEP 1: Chunk the text
        chunks = self.text_splitter.split_text(text)
        logger.info(f"Split into {len(chunks)} chunks")

        # Store document metadata in MongoDB
        self.mongodb.store_document(
            document_id=document_id,
            filename=file_path.name,
            file_path=str(file_path),
            file_type=file_type,
            total_chunks=len(chunks),
            metadata={"original_length": len(text)}
        )

        # STEP 2 & 3: Embed and store each chunk
        previous_summary = ""
        results = {
            "document_id": document_id,
            "filename": file_path.name,
            "total_chunks": len(chunks),
            "chunks_processed": 0,
            "dsrp_extractions": 0,
            "total_distinctions": 0,
            "total_systems": 0,
            "total_relationships": 0,
            "total_perspectives": 0,
            "errors": []
        }

        for i, chunk_text in enumerate(chunks, 1):
            chunk_id = f"{document_id}_chunk_{i}"

            logger.info(f"Processing chunk {i}/{len(chunks)} ({len(chunk_text)} chars)")

            # STEP 2: Generate embedding
            embedding = self.embedding_model.encode(chunk_text).tolist()

            # STEP 3: Store in MongoDB (episodic memory)
            self.mongodb.store_chunk(
                chunk_id=chunk_id,
                document_id=document_id,
                chunk_number=i,
                text=chunk_text,
                embedding=embedding,
                metadata={"char_count": len(chunk_text)}
            )

            results["chunks_processed"] += 1

            # STEP 4: Extract DSRP patterns using Claude
            if self.claude:
                dsrp_data = self._extract_dsrp(
                    text=chunk_text,
                    chunk_number=i,
                    total_chunks=len(chunks),
                    document_name=file_path.name,
                    previous_summary=previous_summary
                )

                if dsrp_data:
                    # STEP 5: Store DSRP in TypeDB (semantic memory)
                    store_results = self.typedb.store_dsrp_extraction(
                        dsrp_data=dsrp_data,
                        source_chunk_id=chunk_id
                    )

                    results["dsrp_extractions"] += 1
                    results["total_distinctions"] += store_results["distinctions"]
                    results["total_systems"] += store_results["systems"]
                    results["total_relationships"] += store_results["relationships"]
                    results["total_perspectives"] += store_results["perspectives"]
                    results["errors"].extend(store_results["errors"])

                    # Update context for next chunk
                    previous_summary = dsrp_data.get("summary", "")

                    # Mark chunk as processed
                    self.mongodb.mark_chunk_dsrp_extracted(chunk_id)

        # Mark document as complete
        self.mongodb.mark_document_completed(document_id)

        # Move file to processed folder
        processed_path = PROCESSED_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
        shutil.move(str(file_path), str(processed_path))
        logger.info(f"Moved to: {processed_path}")

        # Log summary
        logger.info("-" * 40)
        logger.info(f"COMPLETED: {file_path.name}")
        logger.info(f"  Chunks: {results['chunks_processed']}")
        logger.info(f"  DSRP Extractions: {results['dsrp_extractions']}")
        logger.info(f"  Distinctions (D): {results['total_distinctions']}")
        logger.info(f"  Systems (S): {results['total_systems']}")
        logger.info(f"  Relationships (R): {results['total_relationships']}")
        logger.info(f"  Perspectives (P): {results['total_perspectives']}")
        if results["errors"]:
            logger.warning(f"  Errors: {len(results['errors'])}")
        logger.info("-" * 40)

        return results

    def _extract_pdf_text(self, file_path: Path) -> str:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to the PDF

        Returns:
            Extracted text as a string
        """
        if not HAS_PYPDF:
            logger.error("pypdf not installed. Cannot process PDFs.")
            return ""

        try:
            text_parts = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                logger.info(f"PDF has {len(reader.pages)} pages")

                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    if page_num % 10 == 0:
                        logger.debug(f"Processed page {page_num}")

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""

    def _extract_dsrp(
        self,
        text: str,
        chunk_number: int,
        total_chunks: int,
        document_name: str,
        previous_summary: str
    ) -> Optional[dict]:
        """
        Use Claude to extract DSRP patterns from a text chunk.

        Args:
            text: The text to analyze
            chunk_number: Which chunk this is
            total_chunks: Total chunks in document
            document_name: Name of source document
            previous_summary: Summary from previous chunk

        Returns:
            Parsed JSON with DSRP patterns, or None on error
        """
        try:
            # Build the prompt
            prompt = get_extraction_prompt(
                text=text,
                chunk_number=chunk_number,
                total_chunks=total_chunks,
                document_name=document_name,
                previous_summary=previous_summary
            )

            # Call Claude
            response = self.claude.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract the response text
            response_text = response.content[0].text.strip()

            # Try to parse as JSON
            # Sometimes Claude wraps in markdown code blocks
            if response_text.startswith("```"):
                # Remove markdown code fence
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            dsrp_data = json.loads(response_text)

            # Validate against schema
            try:
                jsonschema.validate(dsrp_data, DSRP_OUTPUT_SCHEMA)
            except jsonschema.ValidationError as e:
                logger.warning(f"DSRP output validation warning: {e.message}")
                # Continue anyway - partial data is better than none

            logger.debug(f"Extracted DSRP: {len(dsrp_data.get('distinctions', []))}D, "
                        f"{len(dsrp_data.get('systems', []))}S, "
                        f"{len(dsrp_data.get('relationships', []))}R, "
                        f"{len(dsrp_data.get('perspectives', []))}P")

            return dsrp_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DSRP JSON: {e}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            return None

        except Exception as e:
            logger.error(f"DSRP extraction error: {e}")
            return None

    def process_inbox(self) -> list[dict]:
        """
        Process all files in the inbox folder.

        Returns:
            List of results for each processed file
        """
        results = []

        # Find all supported files
        supported_extensions = [".pdf", ".txt", ".md", ".text"]
        files = [
            f for f in INBOX_DIR.iterdir()
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]

        if not files:
            logger.info(f"No files found in {INBOX_DIR}")
            logger.info(f"Supported formats: {', '.join(supported_extensions)}")
            return results

        logger.info(f"Found {len(files)} file(s) to process")

        for file_path in sorted(files):
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                results.append({"filename": file_path.name, "error": str(e)})

        return results

    def close(self):
        """Clean up resources."""
        self.mongodb.close()
        self.typedb.close()
        logger.info("Pipeline shutdown complete")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="DSRP Knowledge Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ingest.py                     # Process all files in inbox
  python ingest.py --file doc.pdf      # Process a specific file
  python ingest.py --verbose           # Show debug output

Supported file types: .pdf, .txt, .md
        """
    )

    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Process a specific file instead of the inbox"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run the pipeline
    pipeline = DSRPIngestionPipeline()

    try:
        if args.file:
            # Process specific file
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error(f"File not found: {args.file}")
                sys.exit(1)
            pipeline.process_file(file_path)
        else:
            # Process all files in inbox
            results = pipeline.process_inbox()

            # Print summary
            if results:
                print("\n" + "=" * 60)
                print("PIPELINE SUMMARY")
                print("=" * 60)
                for r in results:
                    if "error" in r:
                        print(f"  FAILED: {r.get('filename', 'unknown')} - {r['error']}")
                    else:
                        print(f"  OK: {r['filename']} - "
                              f"{r['total_chunks']} chunks, "
                              f"{r['total_distinctions']}D/{r['total_systems']}S/"
                              f"{r['total_relationships']}R/{r['total_perspectives']}P")
                print("=" * 60)

    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
