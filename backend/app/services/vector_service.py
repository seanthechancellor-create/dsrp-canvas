"""
Vector Search Service using pgvector

Unified storage for DSRP knowledge base:
- Document storage (replaces MongoDB)
- Vector embeddings for semantic search
- RAG retrieval for document chunks

Supports multiple embedding providers: Ollama (default), OpenAI.

Setup:
    1. Install PostgreSQL with pgvector extension
    2. Run: CREATE EXTENSION vector;
    3. Set POSTGRES_URL environment variable
"""

import os
import logging
import json
from typing import Optional
from datetime import datetime
import hashlib
import httpx

logger = logging.getLogger(__name__)

# Configuration
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://localhost:5432/dsrp_canvas")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Embedding dimensions by provider
OLLAMA_EMBEDDING_DIMENSIONS = 768  # nomic-embed-text
OPENAI_EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small

# Use OpenAI if API key is set, otherwise use Ollama
USE_OPENAI = bool(OPENAI_API_KEY)
EMBEDDING_DIMENSIONS = OPENAI_EMBEDDING_DIMENSIONS if USE_OPENAI else OLLAMA_EMBEDDING_DIMENSIONS

# Lazy imports to avoid startup failures
_pool = None
_openai_client = None


def _get_pool():
    """Get or create connection pool."""
    global _pool
    if _pool is None:
        try:
            import psycopg_pool
            _pool = psycopg_pool.ConnectionPool(POSTGRES_URL, min_size=1, max_size=10)
            logger.info("Connected to PostgreSQL with pgvector")
        except Exception as e:
            logger.warning(f"Failed to connect to PostgreSQL: {e}")
            _pool = None
    return _pool


def _get_openai():
    """Get or create OpenAI client (only if API key is set)."""
    global _openai_client
    if not USE_OPENAI:
        return None
    if _openai_client is None:
        try:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to create OpenAI client: {e}")
            _openai_client = None
    return _openai_client


async def _get_ollama_embedding(text: str) -> Optional[list[float]]:
    """Get embedding from Ollama."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding")
    except Exception as e:
        logger.error(f"Failed to get Ollama embedding: {e}")
        return None


class VectorService:
    """Service for vector embeddings and semantic search."""

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the vector store tables."""
        pool = _get_pool()
        if not pool:
            logger.warning("Vector service unavailable - PostgreSQL not connected")
            return False

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    # Enable pgvector extension
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                    # Create embeddings table for concepts
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS concept_embeddings (
                            id SERIAL PRIMARY KEY,
                            concept_id VARCHAR(255) UNIQUE NOT NULL,
                            concept_name VARCHAR(500) NOT NULL,
                            content TEXT NOT NULL,
                            content_hash VARCHAR(64) NOT NULL,
                            embedding vector({EMBEDDING_DIMENSIONS}),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)

                    # Create embeddings table for analyses
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS analysis_embeddings (
                            id SERIAL PRIMARY KEY,
                            analysis_id VARCHAR(255) UNIQUE NOT NULL,
                            concept_id VARCHAR(255) NOT NULL,
                            move_type VARCHAR(50) NOT NULL,
                            content TEXT NOT NULL,
                            content_hash VARCHAR(64) NOT NULL,
                            embedding vector({EMBEDDING_DIMENSIONS}),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)

                    # Create embeddings table for source chunks
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS source_embeddings (
                            id SERIAL PRIMARY KEY,
                            source_id VARCHAR(255) NOT NULL,
                            chunk_index INTEGER NOT NULL,
                            content TEXT NOT NULL,
                            content_hash VARCHAR(64) NOT NULL,
                            embedding vector({EMBEDDING_DIMENSIONS}),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(source_id, chunk_index)
                        );
                    """)

                    # Create documents table (replaces MongoDB)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS documents (
                            id SERIAL PRIMARY KEY,
                            document_id VARCHAR(255) UNIQUE NOT NULL,
                            filename VARCHAR(500) NOT NULL,
                            file_type VARCHAR(50),
                            file_size BIGINT,
                            total_chunks INTEGER DEFAULT 0,
                            status VARCHAR(50) DEFAULT 'pending',
                            metadata JSONB DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)

                    # Create embeddings table for document chunks (RAG pipeline)
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS document_embeddings (
                            id SERIAL PRIMARY KEY,
                            document_id VARCHAR(255) NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                            chunk_id VARCHAR(255) UNIQUE NOT NULL,
                            chunk_index INTEGER NOT NULL,
                            filename VARCHAR(500),
                            content TEXT NOT NULL,
                            content_hash VARCHAR(64) NOT NULL,
                            embedding vector({EMBEDDING_DIMENSIONS}),
                            metadata JSONB DEFAULT '{{}}',
                            dsrp_extracted BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)

                    # Create indexes for similarity search
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS concept_embedding_idx
                        ON concept_embeddings
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)

                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS analysis_embedding_idx
                        ON analysis_embeddings
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)

                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS source_embedding_idx
                        ON source_embeddings
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)

                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS document_embedding_idx
                        ON document_embeddings
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)

                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS document_embedding_doc_idx
                        ON document_embeddings (document_id);
                    """)

                    conn.commit()
                    self._initialized = True
                    logger.info("Vector store initialized successfully")
                    return True

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return False

    def _compute_hash(self, content: str) -> str:
        """Compute hash of content for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def _get_embedding(self, text: str) -> Optional[list[float]]:
        """Get embedding vector for text using configured provider (Ollama or OpenAI)."""
        if USE_OPENAI:
            client = _get_openai()
            if not client:
                logger.warning("OpenAI client not available, falling back to Ollama")
                return await _get_ollama_embedding(text)

            try:
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text,
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Failed to get OpenAI embedding: {e}")
                return None
        else:
            # Use Ollama for embeddings
            return await _get_ollama_embedding(text)

    # =========================================================================
    # Concept Embeddings
    # =========================================================================

    async def embed_concept(
        self,
        concept_id: str,
        concept_name: str,
        description: Optional[str] = None,
    ) -> bool:
        """Create or update embedding for a concept."""
        pool = _get_pool()
        if not pool:
            return False

        # Build content for embedding
        content = f"Concept: {concept_name}"
        if description:
            content += f"\nDescription: {description}"

        content_hash = self._compute_hash(content)

        # Check if embedding already exists and is current
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT content_hash FROM concept_embeddings WHERE concept_id = %s",
                        (concept_id,)
                    )
                    row = cur.fetchone()
                    if row and row[0] == content_hash:
                        logger.debug(f"Concept {concept_id} embedding is current")
                        return True
        except Exception as e:
            logger.error(f"Error checking existing embedding: {e}")

        # Get new embedding
        embedding = await self._get_embedding(content)
        if not embedding:
            return False

        # Upsert embedding
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO concept_embeddings
                            (concept_id, concept_name, content, content_hash, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (concept_id) DO UPDATE SET
                            concept_name = EXCLUDED.concept_name,
                            content = EXCLUDED.content,
                            content_hash = EXCLUDED.content_hash,
                            embedding = EXCLUDED.embedding,
                            updated_at = CURRENT_TIMESTAMP;
                    """, (concept_id, concept_name, content, content_hash, embedding))
                    conn.commit()
                    logger.info(f"Embedded concept: {concept_name}")
                    return True
        except Exception as e:
            logger.error(f"Failed to store concept embedding: {e}")
            return False

    async def search_concepts(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[dict]:
        """
        Search concepts by semantic similarity.

        Args:
            query: Search query text
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of matching concepts with similarity scores
        """
        pool = _get_pool()
        if not pool:
            return []

        query_embedding = await self._get_embedding(query)
        if not query_embedding:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            concept_id,
                            concept_name,
                            content,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM concept_embeddings
                        WHERE 1 - (embedding <=> %s::vector) >= %s
                        ORDER BY similarity DESC
                        LIMIT %s;
                    """, (query_embedding, query_embedding, threshold, limit))

                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "concept_id": row[0],
                            "concept_name": row[1],
                            "content": row[2],
                            "similarity": float(row[3]),
                        })
                    return results
        except Exception as e:
            logger.error(f"Failed to search concepts: {e}")
            return []

    # =========================================================================
    # Analysis Embeddings
    # =========================================================================

    async def embed_analysis(
        self,
        analysis_id: str,
        concept_id: str,
        move_type: str,
        reasoning: str,
        elements: Optional[dict] = None,
    ) -> bool:
        """Create embedding for a DSRP analysis."""
        pool = _get_pool()
        if not pool:
            return False

        # Build content for embedding
        content = f"DSRP Analysis ({move_type}):\n{reasoning}"
        if elements:
            content += f"\nElements: {elements}"

        content_hash = self._compute_hash(content)

        # Get embedding
        embedding = await self._get_embedding(content)
        if not embedding:
            return False

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO analysis_embeddings
                            (analysis_id, concept_id, move_type, content, content_hash, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (analysis_id) DO UPDATE SET
                            content = EXCLUDED.content,
                            content_hash = EXCLUDED.content_hash,
                            embedding = EXCLUDED.embedding;
                    """, (analysis_id, concept_id, move_type, content, content_hash, embedding))
                    conn.commit()
                    logger.info(f"Embedded analysis: {analysis_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to store analysis embedding: {e}")
            return False

    async def search_analyses(
        self,
        query: str,
        move_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[dict]:
        """
        Search analyses by semantic similarity.

        Args:
            query: Search query text
            move_type: Optional filter by DSRP move type
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)
        """
        pool = _get_pool()
        if not pool:
            return []

        query_embedding = await self._get_embedding(query)
        if not query_embedding:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    if move_type:
                        cur.execute("""
                            SELECT
                                analysis_id,
                                concept_id,
                                move_type,
                                content,
                                1 - (embedding <=> %s::vector) as similarity
                            FROM analysis_embeddings
                            WHERE move_type = %s
                              AND 1 - (embedding <=> %s::vector) >= %s
                            ORDER BY similarity DESC
                            LIMIT %s;
                        """, (query_embedding, move_type, query_embedding, threshold, limit))
                    else:
                        cur.execute("""
                            SELECT
                                analysis_id,
                                concept_id,
                                move_type,
                                content,
                                1 - (embedding <=> %s::vector) as similarity
                            FROM analysis_embeddings
                            WHERE 1 - (embedding <=> %s::vector) >= %s
                            ORDER BY similarity DESC
                            LIMIT %s;
                        """, (query_embedding, query_embedding, threshold, limit))

                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "analysis_id": row[0],
                            "concept_id": row[1],
                            "move_type": row[2],
                            "content": row[3],
                            "similarity": float(row[4]),
                        })
                    return results
        except Exception as e:
            logger.error(f"Failed to search analyses: {e}")
            return []

    # =========================================================================
    # Source Embeddings (RAG)
    # =========================================================================

    async def embed_source_chunks(
        self,
        source_id: str,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> int:
        """
        Embed source text in chunks for RAG.

        Args:
            source_id: ID of the source
            text: Full text content
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks

        Returns:
            Number of chunks embedded
        """
        pool = _get_pool()
        if not pool:
            return 0

        # Simple chunking (could be improved with sentence boundaries)
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - chunk_overlap

        embedded_count = 0
        for i, chunk in enumerate(chunks):
            content_hash = self._compute_hash(chunk)
            embedding = await self._get_embedding(chunk)

            if embedding:
                try:
                    with pool.connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO source_embeddings
                                    (source_id, chunk_index, content, content_hash, embedding)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (source_id, chunk_index) DO UPDATE SET
                                    content = EXCLUDED.content,
                                    content_hash = EXCLUDED.content_hash,
                                    embedding = EXCLUDED.embedding;
                            """, (source_id, i, chunk, content_hash, embedding))
                            conn.commit()
                            embedded_count += 1
                except Exception as e:
                    logger.error(f"Failed to embed chunk {i}: {e}")

        logger.info(f"Embedded {embedded_count}/{len(chunks)} chunks for source {source_id}")
        return embedded_count

    async def search_sources(
        self,
        query: str,
        source_ids: Optional[list[str]] = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[dict]:
        """
        Search source chunks by semantic similarity (RAG retrieval).

        Args:
            query: Search query text
            source_ids: Optional filter by source IDs
            limit: Maximum results to return
            threshold: Minimum similarity score
        """
        pool = _get_pool()
        if not pool:
            return []

        query_embedding = await self._get_embedding(query)
        if not query_embedding:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    if source_ids:
                        cur.execute("""
                            SELECT
                                source_id,
                                chunk_index,
                                content,
                                1 - (embedding <=> %s::vector) as similarity
                            FROM source_embeddings
                            WHERE source_id = ANY(%s)
                              AND 1 - (embedding <=> %s::vector) >= %s
                            ORDER BY similarity DESC
                            LIMIT %s;
                        """, (query_embedding, source_ids, query_embedding, threshold, limit))
                    else:
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
                        """, (query_embedding, query_embedding, threshold, limit))

                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "source_id": row[0],
                            "chunk_index": row[1],
                            "content": row[2],
                            "similarity": float(row[3]),
                        })
                    return results
        except Exception as e:
            logger.error(f"Failed to search sources: {e}")
            return []

    # =========================================================================
    # Document Embeddings (RAG Pipeline)
    # =========================================================================

    async def embed_document_chunk(
        self,
        document_id: str,
        chunk_id: str,
        chunk_index: int,
        content: str,
        filename: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Embed a document chunk for RAG retrieval.

        Args:
            document_id: ID of the parent document
            chunk_id: Unique ID for this chunk
            chunk_index: Position in document
            content: Text content to embed
            filename: Optional source filename
            metadata: Optional metadata dict
        """
        pool = _get_pool()
        if not pool:
            return False

        content_hash = self._compute_hash(content)

        # Check if already embedded with same content
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT content_hash FROM document_embeddings WHERE chunk_id = %s",
                        (chunk_id,)
                    )
                    row = cur.fetchone()
                    if row and row[0] == content_hash:
                        return True  # Already embedded
        except Exception:
            pass

        embedding = await self._get_embedding(content)
        if not embedding:
            return False

        try:
            import json
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO document_embeddings
                            (document_id, chunk_id, chunk_index, filename, content, content_hash, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            content = EXCLUDED.content,
                            content_hash = EXCLUDED.content_hash,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata;
                    """, (document_id, chunk_id, chunk_index, filename, content, content_hash, embedding, json.dumps(metadata or {})))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to embed document chunk: {e}")
            return False

    async def search_documents(
        self,
        query: str,
        document_ids: Optional[list[str]] = None,
        limit: int = 10,
        threshold: float = 0.5,
    ) -> list[dict]:
        """
        Search document chunks by semantic similarity.

        This is the primary RAG retrieval method for the study guide ingestor.

        Args:
            query: Search query text
            document_ids: Optional filter by document IDs
            limit: Maximum results
            threshold: Minimum similarity score
        """
        pool = _get_pool()
        if not pool:
            return []

        query_embedding = await self._get_embedding(query)
        if not query_embedding:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    if document_ids:
                        cur.execute("""
                            SELECT
                                document_id,
                                chunk_id,
                                chunk_index,
                                filename,
                                content,
                                metadata,
                                1 - (embedding <=> %s::vector) as similarity
                            FROM document_embeddings
                            WHERE document_id = ANY(%s)
                              AND 1 - (embedding <=> %s::vector) >= %s
                            ORDER BY similarity DESC
                            LIMIT %s;
                        """, (query_embedding, document_ids, query_embedding, threshold, limit))
                    else:
                        cur.execute("""
                            SELECT
                                document_id,
                                chunk_id,
                                chunk_index,
                                filename,
                                content,
                                metadata,
                                1 - (embedding <=> %s::vector) as similarity
                            FROM document_embeddings
                            WHERE 1 - (embedding <=> %s::vector) >= %s
                            ORDER BY similarity DESC
                            LIMIT %s;
                        """, (query_embedding, query_embedding, threshold, limit))

                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "document_id": row[0],
                            "chunk_id": row[1],
                            "chunk_index": row[2],
                            "filename": row[3],
                            "content": row[4],
                            "metadata": row[5] or {},
                            "similarity": float(row[6]),
                        })
                    return results
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []

    # =========================================================================
    # Document Management (replaces MongoDB)
    # =========================================================================

    async def store_document(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        file_size: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Store document metadata."""
        pool = _get_pool()
        if not pool:
            return False

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO documents (document_id, filename, file_type, file_size, metadata, status)
                        VALUES (%s, %s, %s, %s, %s, 'processing')
                        ON CONFLICT (document_id) DO UPDATE SET
                            filename = EXCLUDED.filename,
                            file_type = EXCLUDED.file_type,
                            file_size = EXCLUDED.file_size,
                            metadata = EXCLUDED.metadata,
                            updated_at = CURRENT_TIMESTAMP;
                    """, (document_id, filename, file_type, file_size, json.dumps(metadata or {})))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            return False

    async def update_document_chunks(self, document_id: str, total_chunks: int) -> bool:
        """Update document chunk count."""
        pool = _get_pool()
        if not pool:
            return False

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE documents SET total_chunks = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE document_id = %s;
                    """, (total_chunks, document_id))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to update document chunks: {e}")
            return False

    async def mark_document_completed(self, document_id: str) -> bool:
        """Mark document as fully processed."""
        pool = _get_pool()
        if not pool:
            return False

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE documents SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                        WHERE document_id = %s;
                    """, (document_id,))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to mark document completed: {e}")
            return False

    async def get_documents(self) -> list[dict]:
        """Get list of all documents."""
        pool = _get_pool()
        if not pool:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT document_id, filename, file_type, total_chunks, status, created_at, metadata
                        FROM documents ORDER BY created_at DESC;
                    """)
                    return [
                        {
                            "document_id": row[0],
                            "filename": row[1],
                            "file_type": row[2],
                            "total_chunks": row[3],
                            "status": row[4],
                            "created_at": row[5].isoformat() if row[5] else None,
                            "metadata": row[6] or {},
                        }
                        for row in cur.fetchall()
                    ]
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []

    async def get_document(self, document_id: str) -> Optional[dict]:
        """Get single document by ID."""
        pool = _get_pool()
        if not pool:
            return None

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT document_id, filename, file_type, total_chunks, status, created_at, metadata
                        FROM documents WHERE document_id = %s;
                    """, (document_id,))
                    row = cur.fetchone()
                    if row:
                        return {
                            "document_id": row[0],
                            "filename": row[1],
                            "file_type": row[2],
                            "total_chunks": row[3],
                            "status": row[4],
                            "created_at": row[5].isoformat() if row[5] else None,
                            "metadata": row[6] or {},
                        }
                    return None
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete document and all its chunks."""
        pool = _get_pool()
        if not pool:
            return False

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM documents WHERE document_id = %s;", (document_id,))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    async def get_document_chunks(self, document_id: str) -> list[dict]:
        """Get all chunks for a document."""
        pool = _get_pool()
        if not pool:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT chunk_id, chunk_index, content, dsrp_extracted, metadata
                        FROM document_embeddings
                        WHERE document_id = %s
                        ORDER BY chunk_index;
                    """, (document_id,))
                    return [
                        {
                            "chunk_id": row[0],
                            "chunk_index": row[1],
                            "content": row[2],
                            "dsrp_extracted": row[3],
                            "metadata": row[4] or {},
                        }
                        for row in cur.fetchall()
                    ]
        except Exception as e:
            logger.error(f"Failed to get document chunks: {e}")
            return []

    async def get_chunk_by_id(self, chunk_id: str) -> Optional[dict]:
        """Get a specific chunk by ID."""
        pool = _get_pool()
        if not pool:
            return None

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT chunk_id, document_id, chunk_index, content, dsrp_extracted, metadata
                        FROM document_embeddings WHERE chunk_id = %s;
                    """, (chunk_id,))
                    row = cur.fetchone()
                    if row:
                        return {
                            "chunk_id": row[0],
                            "document_id": row[1],
                            "chunk_index": row[2],
                            "content": row[3],
                            "dsrp_extracted": row[4],
                            "metadata": row[5] or {},
                        }
                    return None
        except Exception as e:
            logger.error(f"Failed to get chunk: {e}")
            return None

    async def mark_chunk_extracted(self, chunk_id: str) -> bool:
        """Mark a chunk as having DSRP concepts extracted."""
        pool = _get_pool()
        if not pool:
            return False

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE document_embeddings SET dsrp_extracted = TRUE WHERE chunk_id = %s;
                    """, (chunk_id,))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to mark chunk extracted: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get knowledge base statistics."""
        pool = _get_pool()
        if not pool:
            return {"connected": False}

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM documents;")
                    doc_count = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM document_embeddings;")
                    chunk_count = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM document_embeddings WHERE dsrp_extracted = TRUE;")
                    extracted_count = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM concept_embeddings;")
                    concept_count = cur.fetchone()[0]

                    return {
                        "connected": True,
                        "documents": doc_count,
                        "chunks": chunk_count,
                        "dsrp_extracted": extracted_count,
                        "concepts": concept_count,
                        "embedding_dimensions": EMBEDDING_DIMENSIONS,
                    }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"connected": False, "error": str(e)}

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def find_similar_concepts(
        self,
        concept_id: str,
        limit: int = 5,
    ) -> list[dict]:
        """Find concepts similar to a given concept."""
        pool = _get_pool()
        if not pool:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    # Get the concept's embedding
                    cur.execute(
                        "SELECT embedding FROM concept_embeddings WHERE concept_id = %s",
                        (concept_id,)
                    )
                    row = cur.fetchone()
                    if not row:
                        return []

                    embedding = row[0]

                    # Find similar concepts (excluding self)
                    cur.execute("""
                        SELECT
                            concept_id,
                            concept_name,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM concept_embeddings
                        WHERE concept_id != %s
                        ORDER BY similarity DESC
                        LIMIT %s;
                    """, (embedding, concept_id, limit))

                    results = []
                    for row in cur.fetchall():
                        results.append({
                            "concept_id": row[0],
                            "concept_name": row[1],
                            "similarity": float(row[2]),
                        })
                    return results
        except Exception as e:
            logger.error(f"Failed to find similar concepts: {e}")
            return []


# Singleton instance
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get the singleton vector service instance."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
