"""
Redis Cache Service

Provides caching layer for DSRP Canvas to improve response times.
Caches TypeDB queries, API responses, and computed results.

Setup:
    1. Install Redis server
    2. Set REDIS_URL environment variable (default: redis://localhost:6379)
"""

import os
import json
import logging
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
from datetime import timedelta

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default

# Cache key prefixes for organization
PREFIX_CONCEPT = "dsrp:concept:"
PREFIX_CONCEPTS_LIST = "dsrp:concepts:list"
PREFIX_ANALYSIS = "dsrp:analysis:"
PREFIX_RELATIONS = "dsrp:relations:"
PREFIX_SOURCE = "dsrp:source:"
PREFIX_SOURCES_LIST = "dsrp:sources:list"
PREFIX_SEARCH = "dsrp:search:"
PREFIX_EXPORT = "dsrp:export:"

# Lazy Redis client
_redis_client = None


def _get_redis():
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info(f"Connected to Redis at {REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Caching disabled.")
            _redis_client = None
    return _redis_client


class CacheService:
    """Service for caching DSRP data in Redis."""

    def __init__(self):
        self.default_ttl = DEFAULT_TTL

    @property
    def redis(self):
        """Get Redis client."""
        return _get_redis()

    @property
    def available(self) -> bool:
        """Check if Redis is available."""
        return self.redis is not None

    def _make_key(self, prefix: str, *parts: str) -> str:
        """Create a cache key from prefix and parts."""
        return prefix + ":".join(str(p) for p in parts)

    def _hash_query(self, query: str) -> str:
        """Create a hash of a query for cache key."""
        return hashlib.md5(query.encode()).hexdigest()[:12]

    # =========================================================================
    # Basic Operations
    # =========================================================================

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.redis:
            return None

        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a value in cache."""
        if not self.redis:
            return False

        try:
            serialized = json.dumps(value, default=str)
            self.redis.setex(key, ttl or self.default_ttl, serialized)
            return True
        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self.redis:
            return False

        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if not self.redis:
            return 0

        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
        except Exception as e:
            logger.debug(f"Cache delete pattern error for {pattern}: {e}")

        return 0

    # =========================================================================
    # Concept Caching
    # =========================================================================

    async def get_concept(self, concept_id: str) -> Optional[dict]:
        """Get a cached concept."""
        key = self._make_key(PREFIX_CONCEPT, concept_id)
        return await self.get(key)

    async def set_concept(self, concept_id: str, concept: dict, ttl: int = 600) -> bool:
        """Cache a concept."""
        key = self._make_key(PREFIX_CONCEPT, concept_id)
        return await self.set(key, concept, ttl)

    async def invalidate_concept(self, concept_id: str) -> bool:
        """Invalidate a concept cache entry."""
        key = self._make_key(PREFIX_CONCEPT, concept_id)
        await self.delete(key)
        # Also invalidate the concepts list
        await self.delete(PREFIX_CONCEPTS_LIST)
        return True

    async def get_concepts_list(self) -> Optional[list]:
        """Get cached concepts list."""
        return await self.get(PREFIX_CONCEPTS_LIST)

    async def set_concepts_list(self, concepts: list, ttl: int = 300) -> bool:
        """Cache concepts list."""
        return await self.set(PREFIX_CONCEPTS_LIST, concepts, ttl)

    # =========================================================================
    # Analysis Caching
    # =========================================================================

    async def get_analysis(self, analysis_id: str) -> Optional[dict]:
        """Get a cached analysis."""
        key = self._make_key(PREFIX_ANALYSIS, analysis_id)
        return await self.get(key)

    async def set_analysis(self, analysis_id: str, analysis: dict, ttl: int = 900) -> bool:
        """Cache an analysis result."""
        key = self._make_key(PREFIX_ANALYSIS, analysis_id)
        return await self.set(key, analysis, ttl)

    async def get_concept_analyses(self, concept_id: str) -> Optional[list]:
        """Get cached analyses for a concept."""
        key = self._make_key(PREFIX_ANALYSIS, "concept", concept_id)
        return await self.get(key)

    async def set_concept_analyses(
        self, concept_id: str, analyses: list, ttl: int = 600
    ) -> bool:
        """Cache analyses for a concept."""
        key = self._make_key(PREFIX_ANALYSIS, "concept", concept_id)
        return await self.set(key, analyses, ttl)

    async def invalidate_concept_analyses(self, concept_id: str) -> bool:
        """Invalidate cached analyses for a concept."""
        key = self._make_key(PREFIX_ANALYSIS, "concept", concept_id)
        return await self.delete(key)

    # =========================================================================
    # Relations Caching
    # =========================================================================

    async def get_concept_relations(self, concept_id: str) -> Optional[dict]:
        """Get cached relations for a concept."""
        key = self._make_key(PREFIX_RELATIONS, concept_id)
        return await self.get(key)

    async def set_concept_relations(
        self, concept_id: str, relations: dict, ttl: int = 600
    ) -> bool:
        """Cache relations for a concept."""
        key = self._make_key(PREFIX_RELATIONS, concept_id)
        return await self.set(key, relations, ttl)

    async def invalidate_concept_relations(self, concept_id: str) -> bool:
        """Invalidate cached relations for a concept."""
        key = self._make_key(PREFIX_RELATIONS, concept_id)
        return await self.delete(key)

    # =========================================================================
    # Source Caching
    # =========================================================================

    async def get_source(self, source_id: str) -> Optional[dict]:
        """Get a cached source."""
        key = self._make_key(PREFIX_SOURCE, source_id)
        return await self.get(key)

    async def set_source(self, source_id: str, source: dict, ttl: int = 600) -> bool:
        """Cache a source."""
        key = self._make_key(PREFIX_SOURCE, source_id)
        return await self.set(key, source, ttl)

    async def get_sources_list(self) -> Optional[list]:
        """Get cached sources list."""
        return await self.get(PREFIX_SOURCES_LIST)

    async def set_sources_list(self, sources: list, ttl: int = 300) -> bool:
        """Cache sources list."""
        return await self.set(PREFIX_SOURCES_LIST, sources, ttl)

    async def invalidate_source(self, source_id: str) -> bool:
        """Invalidate a source cache entry."""
        key = self._make_key(PREFIX_SOURCE, source_id)
        await self.delete(key)
        await self.delete(PREFIX_SOURCES_LIST)
        return True

    # =========================================================================
    # Search Result Caching
    # =========================================================================

    async def get_search_results(self, query: str, search_type: str = "concepts") -> Optional[list]:
        """Get cached search results."""
        query_hash = self._hash_query(query)
        key = self._make_key(PREFIX_SEARCH, search_type, query_hash)
        return await self.get(key)

    async def set_search_results(
        self,
        query: str,
        results: list,
        search_type: str = "concepts",
        ttl: int = 180,  # 3 minutes for search
    ) -> bool:
        """Cache search results."""
        query_hash = self._hash_query(query)
        key = self._make_key(PREFIX_SEARCH, search_type, query_hash)
        return await self.set(key, results, ttl)

    async def invalidate_search_cache(self) -> int:
        """Invalidate all search caches."""
        return await self.delete_pattern(f"{PREFIX_SEARCH}*")

    # =========================================================================
    # Export Caching
    # =========================================================================

    async def get_export(self, export_type: str, concept_ids_hash: str) -> Optional[str]:
        """Get cached export content."""
        key = self._make_key(PREFIX_EXPORT, export_type, concept_ids_hash)
        return await self.get(key)

    async def set_export(
        self,
        export_type: str,
        concept_ids_hash: str,
        content: str,
        ttl: int = 600,
    ) -> bool:
        """Cache export content."""
        key = self._make_key(PREFIX_EXPORT, export_type, concept_ids_hash)
        return await self.set(key, content, ttl)

    # =========================================================================
    # Cache Statistics
    # =========================================================================

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.redis:
            return {"available": False}

        try:
            info = self.redis.info("stats")
            memory = self.redis.info("memory")
            keyspace = self.redis.info("keyspace")

            # Count keys by prefix
            prefix_counts = {}
            for prefix_name, prefix_value in [
                ("concepts", PREFIX_CONCEPT),
                ("analyses", PREFIX_ANALYSIS),
                ("relations", PREFIX_RELATIONS),
                ("sources", PREFIX_SOURCE),
                ("searches", PREFIX_SEARCH),
                ("exports", PREFIX_EXPORT),
            ]:
                keys = self.redis.keys(f"{prefix_value}*")
                prefix_counts[prefix_name] = len(keys)

            return {
                "available": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory_used": memory.get("used_memory_human", "unknown"),
                "total_keys": sum(prefix_counts.values()),
                "keys_by_type": prefix_counts,
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"available": True, "error": str(e)}

    async def clear_all(self) -> bool:
        """Clear all DSRP cache entries (dangerous!)."""
        if not self.redis:
            return False

        try:
            count = await self.delete_pattern("dsrp:*")
            logger.info(f"Cleared {count} cache entries")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get the singleton cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# =========================================================================
# Decorator for caching function results
# =========================================================================


def cached(
    prefix: str,
    ttl: int = DEFAULT_TTL,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator to cache async function results.

    Usage:
        @cached("dsrp:myfunction:", ttl=600)
        async def my_function(arg1, arg2):
            ...

        @cached("dsrp:custom:", key_builder=lambda x: f"key:{x}")
        async def custom_function(x):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            if not cache.available:
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                cache_key = prefix + key_builder(*args, **kwargs)
            else:
                # Default: hash all args
                key_data = json.dumps({"args": args, "kwargs": kwargs}, default=str)
                cache_key = prefix + hashlib.md5(key_data.encode()).hexdigest()[:16]

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Execute function and cache result
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            if result is not None:
                await cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
