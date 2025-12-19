"""
PostgreSQL + pgvector Service for DSRP Knowledge Pipeline

This service handles storing text chunks and their vector embeddings in PostgreSQL
with the pgvector extension. pgvector provides native vector similarity search,
making it perfect for RAG applications.

Replaces the previous MongoDB service for a unified database architecture.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

# PostgreSQL with connection pooling
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PgVectorService:
    """
    Handles all PostgreSQL + pgvector operations for the DSRP knowledge pipeline.

    This class manages:
    - Storing text chunks with their vector embeddings
    - Creating vector search indexes
    - Performing similarity searches for RAG
    """

    def __init__(self, connection_url: Optional[str] = None):
        """
        Initialize connection to PostgreSQL.

        Args:
            connection_url: PostgreSQL connection string.
                           If not provided, uses POSTGRES_URL environment variable.
                           Default: postgresql://dsrp:dsrp_password@localhost:5432/dsrp_canvas
        """
        self.connection_url = connection_url or os.getenv(
            "POSTGRES_URL",
            "postgresql://dsrp:dsrp_password@localhost:5432/dsrp_canvas"
        )

        # Log connection (hide password)
        safe_url = self.connection_url.split("@")[-1] if "@" in self.connection_url else self.connection_url
        logger.info(f"Connecting to PostgreSQL at: {safe_url}")

        # Create connection pool
        self.pool = ConnectionPool(
            conninfo=self.connection_url,
            min_size=2,
            max_size=10,
            kwargs={"row_factory": dict_row}
        )

        # Initialize schema
        self._ensure_schema()
        logger.info("Connected to PostgreSQL with pgvector")

    @contextmanager
    def _get_conn(self):
        """Get a connection from the pool."""
        with self.pool.connection() as conn:
            yield conn

    def _ensure_schema(self):
        """
        Create necessary tables and indexes for efficient querying.
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # Documents table - metadata about ingested documents
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pipeline_documents (
                        id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        file_path TEXT,
                        file_type TEXT NOT NULL,
                        total_chunks INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'processing',
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)

                # Chunks table - text chunks with embeddings
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pipeline_chunks (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL REFERENCES pipeline_documents(id) ON DELETE CASCADE,
                        chunk_number INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        embedding vector(384),
                        dsrp_extracted BOOLEAN DEFAULT FALSE,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)

                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_pipeline_chunks_document
                    ON pipeline_chunks(document_id);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_pipeline_chunks_dsrp
                    ON pipeline_chunks(dsrp_extracted);
                """)

                # Create HNSW index for fast vector similarity search
                # HNSW is much faster than IVFFlat for similarity search
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_pipeline_chunks_embedding
                    ON pipeline_chunks
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                """)

                # Full-text search index
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_pipeline_chunks_text
                    ON pipeline_chunks
                    USING gin (to_tsvector('english', text));
                """)

                conn.commit()
                logger.info("PostgreSQL schema ensured")

    def store_document(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        total_chunks: int,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Store metadata about an ingested document.

        Args:
            document_id: Unique identifier for the document
            filename: Original filename
            file_path: Path where the file was stored
            file_type: Type of file (pdf, txt, etc.)
            total_chunks: Number of chunks the document was split into
            metadata: Any additional metadata

        Returns:
            The inserted document record
        """
        import json

        document = {
            "id": document_id,
            "filename": filename,
            "file_path": file_path,
            "file_type": file_type,
            "total_chunks": total_chunks,
            "status": "processing",
            "metadata": metadata or {},
        }

        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO pipeline_documents (id, filename, file_path, file_type, total_chunks, status, metadata)
                    VALUES (%(id)s, %(filename)s, %(file_path)s, %(file_type)s, %(total_chunks)s, %(status)s, %(metadata)s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        file_path = EXCLUDED.file_path,
                        file_type = EXCLUDED.file_type,
                        total_chunks = EXCLUDED.total_chunks,
                        status = EXCLUDED.status,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    RETURNING *;
                """, {**document, "metadata": json.dumps(document["metadata"])})
                result = cur.fetchone()
                conn.commit()

        logger.info(f"Stored document metadata: {filename} ({document_id})")
        return dict(result) if result else document

    def store_chunk(
        self,
        chunk_id: str,
        document_id: str,
        chunk_number: int,
        text: str,
        embedding: list[float],
        dsrp_extracted: bool = False,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Store a text chunk with its vector embedding.

        This is the core of the "Episodic Memory" - raw text + vectors
        that enable semantic search.

        Args:
            chunk_id: Unique identifier for this chunk
            document_id: ID of the parent document
            chunk_number: Position of this chunk in the document (1-indexed)
            text: The actual text content
            embedding: Vector embedding as a list of floats
            dsrp_extracted: Whether DSRP has been extracted from this chunk
            metadata: Additional metadata (page number, etc.)

        Returns:
            The inserted chunk record
        """
        import json

        chunk = {
            "id": chunk_id,
            "document_id": document_id,
            "chunk_number": chunk_number,
            "text": text,
            "embedding": embedding,
            "dsrp_extracted": dsrp_extracted,
            "metadata": metadata or {},
        }

        with self._get_conn() as conn:
            with conn.cursor() as cur:
                # Format embedding as pgvector string
                embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

                cur.execute("""
                    INSERT INTO pipeline_chunks (id, document_id, chunk_number, text, embedding, dsrp_extracted, metadata)
                    VALUES (%(id)s, %(document_id)s, %(chunk_number)s, %(text)s, %(embedding)s::vector, %(dsrp_extracted)s, %(metadata)s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        embedding = EXCLUDED.embedding,
                        dsrp_extracted = EXCLUDED.dsrp_extracted,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    RETURNING id, document_id, chunk_number, text, dsrp_extracted, metadata, created_at;
                """, {**chunk, "embedding": embedding_str, "metadata": json.dumps(chunk["metadata"])})
                result = cur.fetchone()
                conn.commit()

        logger.debug(f"Stored chunk {chunk_number} for document {document_id}")
        return dict(result) if result else chunk

    def mark_chunk_dsrp_extracted(self, chunk_id: str):
        """
        Mark a chunk as having DSRP extraction completed.

        Args:
            chunk_id: The chunk to update
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE pipeline_chunks
                    SET dsrp_extracted = TRUE, updated_at = NOW()
                    WHERE id = %s;
                """, (chunk_id,))
                conn.commit()

    def mark_document_completed(self, document_id: str):
        """
        Mark a document as fully processed.

        Args:
            document_id: The document to update
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE pipeline_documents
                    SET status = 'completed', updated_at = NOW()
                    WHERE id = %s;
                """, (document_id,))
                conn.commit()
        logger.info(f"Document {document_id} marked as completed")

    def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 5,
        document_id: Optional[str] = None
    ) -> list[dict]:
        """
        Find chunks similar to the query embedding using cosine similarity.

        This is used for RAG - finding relevant context for a question.
        Uses pgvector's native similarity search for efficiency.

        Args:
            query_embedding: The vector to search for
            limit: Maximum number of results
            document_id: Optionally filter to a specific document

        Returns:
            List of similar chunks with similarity scores
        """
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if document_id:
                    cur.execute("""
                        SELECT
                            id as chunk_id,
                            document_id,
                            chunk_number,
                            text,
                            metadata,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM pipeline_chunks
                        WHERE document_id = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s;
                    """, (embedding_str, document_id, embedding_str, limit))
                else:
                    cur.execute("""
                        SELECT
                            id as chunk_id,
                            document_id,
                            chunk_number,
                            text,
                            metadata,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM pipeline_chunks
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s;
                    """, (embedding_str, embedding_str, limit))

                results = cur.fetchall()
                return [dict(r) for r in results]

    def get_document_chunks(self, document_id: str) -> list[dict]:
        """
        Get all chunks for a document in order.

        Args:
            document_id: The document to get chunks for

        Returns:
            List of chunks sorted by chunk_number
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, document_id, chunk_number, text, dsrp_extracted, metadata, created_at
                    FROM pipeline_chunks
                    WHERE document_id = %s
                    ORDER BY chunk_number;
                """, (document_id,))
                return [dict(r) for r in cur.fetchall()]

    def get_unprocessed_chunks(self, document_id: Optional[str] = None) -> list[dict]:
        """
        Get chunks that haven't had DSRP extraction yet.

        Args:
            document_id: Optionally filter to a specific document

        Returns:
            List of chunks needing DSRP processing
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if document_id:
                    cur.execute("""
                        SELECT id, document_id, chunk_number, text, dsrp_extracted, metadata
                        FROM pipeline_chunks
                        WHERE dsrp_extracted = FALSE AND document_id = %s;
                    """, (document_id,))
                else:
                    cur.execute("""
                        SELECT id, document_id, chunk_number, text, dsrp_extracted, metadata
                        FROM pipeline_chunks
                        WHERE dsrp_extracted = FALSE;
                    """)
                return [dict(r) for r in cur.fetchall()]

    def get_documents(self) -> list[dict]:
        """Get all documents with their metadata."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, filename, file_type, total_chunks, status, metadata, created_at
                    FROM pipeline_documents
                    ORDER BY created_at DESC;
                """)
                return [dict(r) for r in cur.fetchall()]

    def get_stats(self) -> dict:
        """Get statistics about the knowledge base."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM pipeline_documents;")
                doc_count = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) as count FROM pipeline_chunks;")
                chunk_count = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) as count FROM pipeline_chunks WHERE dsrp_extracted = TRUE;")
                extracted_count = cur.fetchone()["count"]

                return {
                    "connected": True,
                    "documents": doc_count,
                    "chunks": chunk_count,
                    "dsrp_extracted": extracted_count,
                    "embedding_dimensions": 384,
                }

    def close(self):
        """Close the PostgreSQL connection pool."""
        self.pool.close()
        logger.info("PostgreSQL connection closed")
