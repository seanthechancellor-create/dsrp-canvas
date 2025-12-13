"""
Cache Management API

Provides endpoints for cache statistics and management.
"""

from fastapi import APIRouter, HTTPException
from app.services.cache_service import get_cache_service

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache statistics.

    Returns hit/miss ratios, memory usage, and key counts by type.
    """
    cache = get_cache_service()
    stats = await cache.get_stats()
    return stats


@router.get("/health")
async def cache_health():
    """
    Check if cache is available and healthy.
    """
    cache = get_cache_service()

    if not cache.available:
        return {
            "status": "unavailable",
            "message": "Redis not connected. Caching disabled.",
        }

    try:
        # Test basic operations
        test_key = "dsrp:health:test"
        await cache.set(test_key, {"test": True}, ttl=10)
        result = await cache.get(test_key)
        await cache.delete(test_key)

        if result and result.get("test"):
            return {
                "status": "healthy",
                "message": "Redis connected and operational",
            }
        else:
            return {
                "status": "degraded",
                "message": "Redis connected but operations failing",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


@router.post("/invalidate/concept/{concept_id}")
async def invalidate_concept_cache(concept_id: str):
    """
    Invalidate all cache entries for a concept.

    Use when a concept is updated or deleted.
    """
    cache = get_cache_service()

    if not cache.available:
        return {"status": "skipped", "message": "Cache not available"}

    await cache.invalidate_concept(concept_id)
    await cache.invalidate_concept_analyses(concept_id)
    await cache.invalidate_concept_relations(concept_id)

    return {
        "status": "invalidated",
        "concept_id": concept_id,
    }


@router.post("/invalidate/source/{source_id}")
async def invalidate_source_cache(source_id: str):
    """
    Invalidate cache entries for a source.
    """
    cache = get_cache_service()

    if not cache.available:
        return {"status": "skipped", "message": "Cache not available"}

    await cache.invalidate_source(source_id)

    return {
        "status": "invalidated",
        "source_id": source_id,
    }


@router.post("/invalidate/search")
async def invalidate_search_cache():
    """
    Invalidate all search result caches.

    Use after significant data changes.
    """
    cache = get_cache_service()

    if not cache.available:
        return {"status": "skipped", "message": "Cache not available"}

    count = await cache.invalidate_search_cache()

    return {
        "status": "invalidated",
        "keys_deleted": count,
    }


@router.post("/clear")
async def clear_all_cache():
    """
    Clear all DSRP cache entries.

    WARNING: This removes all cached data and may temporarily slow down the API.
    """
    cache = get_cache_service()

    if not cache.available:
        return {"status": "skipped", "message": "Cache not available"}

    success = await cache.clear_all()

    if success:
        return {
            "status": "cleared",
            "message": "All DSRP cache entries removed",
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.post("/warmup")
async def warmup_cache():
    """
    Pre-populate cache with commonly accessed data.

    Fetches and caches all concepts and their analyses.
    """
    from app.services.typedb_service import get_typedb_service

    cache = get_cache_service()
    typedb = get_typedb_service()

    if not cache.available:
        return {"status": "skipped", "message": "Cache not available"}

    try:
        # Cache all concepts
        concepts = await typedb.list_concepts(limit=100)
        await cache.set_concepts_list(concepts)

        # Cache individual concepts and their analyses
        cached_count = 0
        for concept in concepts:
            concept_id = concept.get("id")
            if concept_id:
                await cache.set_concept(concept_id, concept)

                analyses = await typedb.get_analyses_for_concept(concept_id)
                await cache.set_concept_analyses(concept_id, analyses)

                relations = await typedb.get_concept_relations(concept_id)
                await cache.set_concept_relations(concept_id, relations)

                cached_count += 1

        # Cache sources list
        sources = await typedb.list_sources(limit=100)
        await cache.set_sources_list(sources)

        return {
            "status": "warmed",
            "concepts_cached": cached_count,
            "sources_cached": len(sources),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Warmup failed: {str(e)}")
