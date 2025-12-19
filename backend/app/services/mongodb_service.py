"""
MongoDB Service for Document Storage

Stores document metadata and text chunks from the ingestion pipeline.
Vector search has been consolidated to pgvector (see vector_service.py).

This service handles:
- Document metadata storage
- Text chunk storage (without embeddings)
- Document retrieval for RAG context
"""

import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/dsrp_knowledge")

# Lazy imports
_client = None


def _get_client():
    """Get or create MongoDB client."""
    global _client
    if _client is None:
        try:
            from pymongo import MongoClient
            _client = MongoClient(MONGODB_URL)
            # Test connection
            _client.admin.command('ping')
            logger.info(f"Connected to MongoDB")
        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB: {e}")
            _client = None
    return _client


class MongoDBDocumentService:
    """Service for document and chunk storage in MongoDB (no vector search)."""

    def __init__(self):
        self.db_name = MONGODB_URL.split("/")[-1].split("?")[0] or "dsrp_knowledge"

    def _get_db(self):
        """Get database instance."""
        client = _get_client()
        if client:
            return client[self.db_name]
        return None

    async def store_document(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        total_chunks: int,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Store document metadata."""
        db = self._get_db()
        if not db:
            return False

        try:
            db.documents.update_one(
                {"_id": document_id},
                {
                    "$set": {
                        "filename": filename,
                        "file_type": file_type,
                        "total_chunks": total_chunks,
                        "status": "processing",
                        "metadata": metadata or {},
                        "updated_at": datetime.utcnow(),
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()},
                },
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            return False

    async def store_chunk(
        self,
        chunk_id: str,
        document_id: str,
        chunk_number: int,
        text: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Store a text chunk (embeddings stored in pgvector separately)."""
        db = self._get_db()
        if not db:
            return False

        try:
            db.chunks.update_one(
                {"_id": chunk_id},
                {
                    "$set": {
                        "document_id": document_id,
                        "chunk_number": chunk_number,
                        "text": text,
                        "metadata": metadata or {},
                        "updated_at": datetime.utcnow(),
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()},
                },
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store chunk: {e}")
            return False

    async def get_chunk_text(self, chunk_id: str) -> Optional[str]:
        """Get text content for a chunk by ID."""
        db = self._get_db()
        if not db:
            return None

        try:
            chunk = db.chunks.find_one({"_id": chunk_id}, {"text": 1})
            return chunk.get("text") if chunk else None
        except Exception as e:
            logger.error(f"Failed to get chunk text: {e}")
            return None

    async def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[dict]:
        """Get multiple chunks by their IDs."""
        db = self._get_db()
        if not db:
            return []

        try:
            chunks = list(db.chunks.find(
                {"_id": {"$in": chunk_ids}},
                {"_id": 1, "document_id": 1, "chunk_number": 1, "text": 1, "metadata": 1}
            ))
            return [
                {
                    "chunk_id": str(chunk["_id"]),
                    "document_id": chunk["document_id"],
                    "chunk_number": chunk["chunk_number"],
                    "text": chunk["text"],
                    "metadata": chunk.get("metadata", {}),
                }
                for chunk in chunks
            ]
        except Exception as e:
            logger.error(f"Failed to get chunks: {e}")
            return []

    async def mark_document_completed(self, document_id: str) -> bool:
        """Mark a document as fully processed."""
        db = self._get_db()
        if not db:
            return False

        try:
            db.documents.update_one(
                {"_id": document_id},
                {"$set": {"status": "completed", "updated_at": datetime.utcnow()}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark document completed: {e}")
            return False

    async def get_documents(self) -> list[dict]:
        """Get list of all ingested documents."""
        db = self._get_db()
        if not db:
            return []

        try:
            docs = list(db.documents.find({}, {"_id": 1, "filename": 1, "total_chunks": 1, "status": 1, "created_at": 1}))
            return [
                {
                    "document_id": str(doc["_id"]),
                    "filename": doc.get("filename", "Unknown"),
                    "total_chunks": doc.get("total_chunks", 0),
                    "status": doc.get("status", "unknown"),
                    "created_at": doc.get("created_at"),
                }
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []

    async def get_document_chunks(self, document_id: str) -> list[dict]:
        """Get all chunks for a specific document."""
        db = self._get_db()
        if not db:
            return []

        try:
            chunks = list(
                db.chunks.find(
                    {"document_id": document_id},
                    {"_id": 1, "chunk_number": 1, "text": 1, "dsrp_extracted": 1, "metadata": 1}
                ).sort("chunk_number", 1)
            )
            return [
                {
                    "chunk_id": str(chunk["_id"]),
                    "chunk_number": chunk["chunk_number"],
                    "text": chunk["text"],
                    "dsrp_extracted": chunk.get("dsrp_extracted", False),
                    "metadata": chunk.get("metadata", {}),
                }
                for chunk in chunks
            ]
        except Exception as e:
            logger.error(f"Failed to get document chunks: {e}")
            return []

    async def get_stats(self) -> dict:
        """Get statistics about the knowledge base."""
        db = self._get_db()
        if not db:
            return {"connected": False}

        try:
            doc_count = db.documents.count_documents({})
            chunk_count = db.chunks.count_documents({})
            extracted_count = db.chunks.count_documents({"dsrp_extracted": True})

            return {
                "connected": True,
                "documents": doc_count,
                "chunks": chunk_count,
                "dsrp_extracted": extracted_count,
                "embedding_dimensions": 384,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"connected": False, "error": str(e)}


# Singleton instance
_mongodb_service: Optional[MongoDBDocumentService] = None


def get_mongodb_service() -> MongoDBDocumentService:
    """Get the singleton MongoDB document service instance."""
    global _mongodb_service
    if _mongodb_service is None:
        _mongodb_service = MongoDBDocumentService()
    return _mongodb_service
