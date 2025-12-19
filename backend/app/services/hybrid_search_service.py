"""
Hybrid Search Service

Combines vector similarity search with keyword/BM25 search
for improved RAG retrieval quality.

Hybrid search addresses the weaknesses of pure vector search:
- Better handling of exact matches and rare terms
- More consistent results for factual queries
- Improved performance on keyword-specific searches

Supports multiple embedding providers: Ollama (default), OpenAI.
"""

import os
import re
import math
import logging
from typing import Optional
from collections import Counter
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://localhost:5432/dsrp_canvas")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENAI = bool(OPENAI_API_KEY)

# Lazy imports
_pool = None


def _get_pool():
    """Get or create connection pool."""
    global _pool
    if _pool is None:
        try:
            import psycopg_pool
            _pool = psycopg_pool.ConnectionPool(POSTGRES_URL, min_size=1, max_size=10)
            logger.info("Connected to PostgreSQL for hybrid search")
        except Exception as e:
            logger.warning(f"Failed to connect to PostgreSQL: {e}")
            _pool = None
    return _pool


@dataclass
class SearchResult:
    """A search result with combined score."""
    id: str
    content: str
    vector_score: float
    keyword_score: float
    combined_score: float
    source: Optional[str] = None
    metadata: Optional[dict] = None


class HybridSearchService:
    """
    Hybrid search combining vector similarity and keyword matching.

    Uses Reciprocal Rank Fusion (RRF) to combine results from:
    1. pgvector cosine similarity search
    2. PostgreSQL full-text search (ts_rank)
    """

    def __init__(
        self,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        rrf_k: int = 60,
    ):
        """
        Initialize hybrid search.

        Args:
            vector_weight: Weight for vector similarity scores (0-1)
            keyword_weight: Weight for keyword match scores (0-1)
            rrf_k: Reciprocal Rank Fusion constant (higher = smoother)
        """
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.rrf_k = rrf_k
        self._openai_client = None

    def _get_openai(self):
        """Get or create OpenAI client (only if API key is set)."""
        if not USE_OPENAI:
            return None
        if self._openai_client is None:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to create OpenAI client: {e}")
        return self._openai_client

    async def _get_ollama_embedding(self, text: str) -> Optional[list[float]]:
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

    async def _get_embedding(self, text: str) -> Optional[list[float]]:
        """Get embedding vector for text using configured provider (Ollama or OpenAI)."""
        if USE_OPENAI:
            client = self._get_openai()
            if not client:
                logger.warning("OpenAI client not available, falling back to Ollama")
                return await self._get_ollama_embedding(text)

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
            return await self._get_ollama_embedding(text)

    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for full-text search."""
        # Remove special characters, keep alphanumeric and spaces
        clean = re.sub(r'[^\w\s]', ' ', query)
        # Convert to tsquery format with OR between words
        words = [w.strip() for w in clean.split() if w.strip()]
        return ' | '.join(words)

    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        vector_threshold: float = 0.4,
        use_reranking: bool = True,
    ) -> list[SearchResult]:
        """
        Perform hybrid search on document embeddings.

        Args:
            query: Search query text
            limit: Maximum results to return
            vector_threshold: Minimum vector similarity score
            use_reranking: Whether to rerank with RRF

        Returns:
            List of SearchResult objects sorted by combined score
        """
        pool = _get_pool()
        if not pool:
            logger.warning("Database not available for hybrid search")
            return []

        # Get vector results
        vector_results = await self._vector_search(
            query, limit * 2, vector_threshold
        )

        # Get keyword results
        keyword_results = await self._keyword_search(
            query, limit * 2
        )

        if not vector_results and not keyword_results:
            return []

        # Combine results using RRF
        if use_reranking:
            combined = self._reciprocal_rank_fusion(
                vector_results, keyword_results
            )
        else:
            # Simple weighted combination
            combined = self._weighted_combination(
                vector_results, keyword_results
            )

        # Sort by combined score and limit
        combined.sort(key=lambda x: x.combined_score, reverse=True)
        return combined[:limit]

    async def _vector_search(
        self,
        query: str,
        limit: int,
        threshold: float,
    ) -> list[SearchResult]:
        """Perform vector similarity search."""
        pool = _get_pool()
        if not pool:
            return []

        embedding = await self._get_embedding(query)
        if not embedding:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            chunk_id,
                            content,
                            filename,
                            metadata,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM document_embeddings
                        WHERE 1 - (embedding <=> %s::vector) >= %s
                        ORDER BY similarity DESC
                        LIMIT %s;
                    """, (embedding, embedding, threshold, limit))

                    results = []
                    for row in cur.fetchall():
                        results.append(SearchResult(
                            id=row[0],
                            content=row[1],
                            source=row[2],
                            metadata=row[3] or {},
                            vector_score=float(row[4]),
                            keyword_score=0.0,
                            combined_score=0.0,
                        ))
                    return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def _keyword_search(
        self,
        query: str,
        limit: int,
    ) -> list[SearchResult]:
        """Perform full-text keyword search."""
        pool = _get_pool()
        if not pool:
            return []

        ts_query = self._preprocess_query(query)
        if not ts_query:
            return []

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    # Use PostgreSQL full-text search with ts_rank
                    cur.execute("""
                        SELECT
                            chunk_id,
                            content,
                            filename,
                            metadata,
                            ts_rank(
                                to_tsvector('english', content),
                                to_tsquery('english', %s)
                            ) as rank
                        FROM document_embeddings
                        WHERE to_tsvector('english', content) @@ to_tsquery('english', %s)
                        ORDER BY rank DESC
                        LIMIT %s;
                    """, (ts_query, ts_query, limit))

                    results = []
                    for row in cur.fetchall():
                        results.append(SearchResult(
                            id=row[0],
                            content=row[1],
                            source=row[2],
                            metadata=row[3] or {},
                            vector_score=0.0,
                            keyword_score=float(row[4]),
                            combined_score=0.0,
                        ))
                    return results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[SearchResult],
        keyword_results: list[SearchResult],
    ) -> list[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion.

        RRF score = sum(1 / (k + rank_i)) for each list
        """
        # Create lookup by ID
        results_by_id: dict[str, SearchResult] = {}

        # Process vector results
        for rank, result in enumerate(vector_results, 1):
            if result.id not in results_by_id:
                results_by_id[result.id] = result
            results_by_id[result.id].combined_score += (
                self.vector_weight / (self.rrf_k + rank)
            )
            results_by_id[result.id].vector_score = result.vector_score

        # Process keyword results
        for rank, result in enumerate(keyword_results, 1):
            if result.id not in results_by_id:
                results_by_id[result.id] = result
            results_by_id[result.id].combined_score += (
                self.keyword_weight / (self.rrf_k + rank)
            )
            results_by_id[result.id].keyword_score = result.keyword_score

        return list(results_by_id.values())

    def _weighted_combination(
        self,
        vector_results: list[SearchResult],
        keyword_results: list[SearchResult],
    ) -> list[SearchResult]:
        """Simple weighted score combination."""
        results_by_id: dict[str, SearchResult] = {}

        # Normalize and add vector scores
        if vector_results:
            max_vec = max(r.vector_score for r in vector_results)
            for result in vector_results:
                norm_score = result.vector_score / max_vec if max_vec > 0 else 0
                if result.id not in results_by_id:
                    results_by_id[result.id] = result
                results_by_id[result.id].combined_score += (
                    self.vector_weight * norm_score
                )
                results_by_id[result.id].vector_score = result.vector_score

        # Normalize and add keyword scores
        if keyword_results:
            max_kw = max(r.keyword_score for r in keyword_results)
            for result in keyword_results:
                norm_score = result.keyword_score / max_kw if max_kw > 0 else 0
                if result.id not in results_by_id:
                    results_by_id[result.id] = result
                results_by_id[result.id].combined_score += (
                    self.keyword_weight * norm_score
                )
                results_by_id[result.id].keyword_score = result.keyword_score

        return list(results_by_id.values())


# Singleton instance
_hybrid_service: Optional[HybridSearchService] = None


def get_hybrid_search_service() -> HybridSearchService:
    """Get the singleton hybrid search service."""
    global _hybrid_service
    if _hybrid_service is None:
        _hybrid_service = HybridSearchService()
    return _hybrid_service
