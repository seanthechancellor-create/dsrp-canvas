"""
MongoDB Service for DSRP Knowledge Pipeline

This service handles storing text chunks and their vector embeddings in MongoDB.
MongoDB Atlas supports vector search natively, making it perfect for RAG applications.

For local MongoDB (without Atlas), we store vectors as arrays and can do
approximate similarity search using aggregation pipelines.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# Set up logging so we can see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBService:
    """
    Handles all MongoDB operations for the DSRP knowledge pipeline.

    This class manages:
    - Storing text chunks with their vector embeddings
    - Creating vector search indexes
    - Performing similarity searches for RAG
    """

    def __init__(self, connection_url: Optional[str] = None):
        """
        Initialize connection to MongoDB.

        Args:
            connection_url: MongoDB connection string.
                           If not provided, uses MONGODB_URL environment variable.
                           Default: mongodb://localhost:27017/dsrp_knowledge
        """
        # Get the connection URL from environment or use the provided one
        self.connection_url = connection_url or os.getenv(
            "MONGODB_URL",
            "mongodb://localhost:27017/dsrp_knowledge"
        )

        logger.info(f"Connecting to MongoDB at: {self.connection_url.split('@')[-1]}")  # Hide credentials

        # Create the MongoDB client
        # This doesn't actually connect until we perform an operation
        self.client: MongoClient = MongoClient(self.connection_url)

        # Extract database name from URL or use default
        db_name = self.connection_url.split("/")[-1].split("?")[0] or "dsrp_knowledge"
        self.db: Database = self.client[db_name]

        # Define our collections
        # "chunks" stores the text chunks with their embeddings
        self.chunks_collection: Collection = self.db["chunks"]

        # "documents" stores metadata about ingested documents
        self.documents_collection: Collection = self.db["documents"]

        # Initialize indexes
        self._ensure_indexes()

        logger.info(f"Connected to MongoDB database: {db_name}")

    def _ensure_indexes(self):
        """
        Create necessary indexes for efficient querying.

        Indexes make searches much faster by pre-organizing the data.
        """
        # Index on document_id for fast lookups of all chunks in a document
        self.chunks_collection.create_index("document_id")

        # Index on created_at for time-based queries
        self.chunks_collection.create_index("created_at")

        # Compound index for document + chunk number (for ordered retrieval)
        self.chunks_collection.create_index([
            ("document_id", 1),
            ("chunk_number", 1)
        ])

        # Text index for full-text search (backup for when vectors aren't enough)
        self.chunks_collection.create_index([("text", "text")])

        logger.info("MongoDB indexes ensured")

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
        document = {
            "_id": document_id,
            "filename": filename,
            "file_path": file_path,
            "file_type": file_type,
            "total_chunks": total_chunks,
            "status": "processing",  # Will update to "completed" when done
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Use replace to allow re-processing the same document
        self.documents_collection.replace_one(
            {"_id": document_id},
            document,
            upsert=True
        )

        logger.info(f"Stored document metadata: {filename} ({document_id})")
        return document

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
        chunk = {
            "_id": chunk_id,
            "document_id": document_id,
            "chunk_number": chunk_number,
            "text": text,
            "embedding": embedding,  # The vector for similarity search
            "embedding_dimensions": len(embedding),
            "dsrp_extracted": dsrp_extracted,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }

        # Use replace to allow re-processing
        self.chunks_collection.replace_one(
            {"_id": chunk_id},
            chunk,
            upsert=True
        )

        logger.debug(f"Stored chunk {chunk_number} for document {document_id}")
        return chunk

    def mark_chunk_dsrp_extracted(self, chunk_id: str):
        """
        Mark a chunk as having DSRP extraction completed.

        Args:
            chunk_id: The chunk to update
        """
        self.chunks_collection.update_one(
            {"_id": chunk_id},
            {"$set": {"dsrp_extracted": True, "updated_at": datetime.utcnow()}}
        )

    def mark_document_completed(self, document_id: str):
        """
        Mark a document as fully processed.

        Args:
            document_id: The document to update
        """
        self.documents_collection.update_one(
            {"_id": document_id},
            {"$set": {"status": "completed", "updated_at": datetime.utcnow()}}
        )
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

        Note: For production with large datasets, consider MongoDB Atlas
        with native vector search, or migrate to a dedicated vector DB.

        Args:
            query_embedding: The vector to search for
            limit: Maximum number of results
            document_id: Optionally filter to a specific document

        Returns:
            List of similar chunks with similarity scores
        """
        # Build the match filter
        match_filter = {}
        if document_id:
            match_filter["document_id"] = document_id

        # For local MongoDB, we compute cosine similarity in Python
        # This works fine for small datasets (<100k chunks)
        # For larger datasets, use MongoDB Atlas vector search
        pipeline = [
            {"$match": match_filter},
            {"$limit": 1000}  # Limit candidates for performance
        ]

        candidates = list(self.chunks_collection.aggregate(pipeline))

        # Calculate cosine similarity for each candidate
        import numpy as np

        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)

        results = []
        for chunk in candidates:
            chunk_vec = np.array(chunk["embedding"])
            chunk_norm = np.linalg.norm(chunk_vec)

            if query_norm > 0 and chunk_norm > 0:
                similarity = np.dot(query_vec, chunk_vec) / (query_norm * chunk_norm)
            else:
                similarity = 0.0

            results.append({
                "chunk_id": chunk["_id"],
                "document_id": chunk["document_id"],
                "chunk_number": chunk["chunk_number"],
                "text": chunk["text"],
                "similarity": float(similarity),
                "metadata": chunk.get("metadata", {})
            })

        # Sort by similarity (highest first) and return top results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def get_document_chunks(self, document_id: str) -> list[dict]:
        """
        Get all chunks for a document in order.

        Args:
            document_id: The document to get chunks for

        Returns:
            List of chunks sorted by chunk_number
        """
        return list(
            self.chunks_collection.find(
                {"document_id": document_id}
            ).sort("chunk_number", 1)
        )

    def get_unprocessed_chunks(self, document_id: Optional[str] = None) -> list[dict]:
        """
        Get chunks that haven't had DSRP extraction yet.

        Args:
            document_id: Optionally filter to a specific document

        Returns:
            List of chunks needing DSRP processing
        """
        filter_query = {"dsrp_extracted": False}
        if document_id:
            filter_query["document_id"] = document_id

        return list(self.chunks_collection.find(filter_query))

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
        logger.info("MongoDB connection closed")
