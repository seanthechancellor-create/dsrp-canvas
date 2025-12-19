"""
Semantic Search API

Provides vector-based semantic search across concepts, analyses, and sources.
Uses pgvector for similarity search with OpenAI embeddings.
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.vector_service import get_vector_service
from app.services.cache_service import get_cache_service, cached

router = APIRouter(prefix="/search", tags=["search"])


class UnifiedSearchResult(BaseModel):
    """Unified search result item with type discrimination."""
    id: str
    name: Optional[str] = None
    content: str
    similarity: float
    type: str  # concept, analysis, source
    metadata: Optional[dict] = None


class UnifiedSearchResponse(BaseModel):
    """Unified search response combining all result types."""
    query: str
    results: list[UnifiedSearchResult]
    total: int
    by_type: dict[str, int]


class SearchResult(BaseModel):
    """Search result item."""
    id: str
    name: Optional[str] = None
    content: str
    similarity: float
    type: str  # concept, analysis, source


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    results: list[SearchResult]
    total: int


@router.get("", response_model=UnifiedSearchResponse)
async def unified_search(
    q: str = Query(..., min_length=2, description="Search query"),
    types: Optional[str] = Query(
        None,
        description="Comma-separated types to search: concept,analysis,source. Defaults to all.",
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum total results"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity score"),
):
    """
    Unified semantic search across concepts, analyses, and sources.

    Searches all content types in parallel and returns combined results
    sorted by similarity score.

    Args:
        q: Search query text
        types: Optional filter for specific types (e.g., "concept,analysis")
        limit: Maximum total results to return
        threshold: Minimum similarity threshold (0-1)

    Returns:
        Combined results from all matching types, sorted by similarity
    """
    import asyncio

    vector_service = get_vector_service()
    cache = get_cache_service()

    # Parse requested types
    search_types = {"concept", "analysis", "source"}
    if types:
        requested = {t.strip().lower() for t in types.split(",")}
        search_types = search_types & requested

    # Check cache
    cache_key = f"unified:{q}:{','.join(sorted(search_types))}:{threshold}"
    cached_results = await cache.get_search_results(cache_key, "unified")
    if cached_results:
        by_type = {}
        for r in cached_results:
            by_type[r["type"]] = by_type.get(r["type"], 0) + 1
        return UnifiedSearchResponse(
            query=q,
            results=[UnifiedSearchResult(**r) for r in cached_results],
            total=len(cached_results),
            by_type=by_type,
        )

    # Search all requested types in parallel
    tasks = []
    if "concept" in search_types:
        tasks.append(("concept", vector_service.search_concepts(q, limit=limit, threshold=threshold)))
    if "analysis" in search_types:
        tasks.append(("analysis", vector_service.search_analyses(q, limit=limit, threshold=threshold)))
    if "source" in search_types:
        tasks.append(("source", vector_service.search_sources(q, limit=limit, threshold=threshold)))

    # Execute searches in parallel
    task_results = await asyncio.gather(*[t[1] for t in tasks])

    # Combine and transform results
    all_results: list[UnifiedSearchResult] = []
    by_type: dict[str, int] = {}

    for (type_name, _), results in zip(tasks, task_results):
        by_type[type_name] = len(results)

        for r in results:
            if type_name == "concept":
                all_results.append(UnifiedSearchResult(
                    id=r["concept_id"],
                    name=r["concept_name"],
                    content=r["content"],
                    similarity=r["similarity"],
                    type="concept",
                    metadata=None,
                ))
            elif type_name == "analysis":
                all_results.append(UnifiedSearchResult(
                    id=r["analysis_id"],
                    name=f"{r['move_type']} analysis",
                    content=r["content"],
                    similarity=r["similarity"],
                    type="analysis",
                    metadata={"concept_id": r["concept_id"], "move_type": r["move_type"]},
                ))
            elif type_name == "source":
                all_results.append(UnifiedSearchResult(
                    id=f"{r['source_id']}:{r['chunk_index']}",
                    name=f"Source chunk {r['chunk_index']}",
                    content=r["content"],
                    similarity=r["similarity"],
                    type="source",
                    metadata={"source_id": r["source_id"], "chunk_index": r["chunk_index"]},
                ))

    # Sort by similarity and limit
    all_results.sort(key=lambda x: x.similarity, reverse=True)
    all_results = all_results[:limit]

    # Update by_type counts after limiting
    final_by_type: dict[str, int] = {}
    for r in all_results:
        final_by_type[r.type] = final_by_type.get(r.type, 0) + 1

    # Cache results
    await cache.set_search_results(
        cache_key,
        [r.model_dump() for r in all_results],
        "unified",
    )

    return UnifiedSearchResponse(
        query=q,
        results=all_results,
        total=len(all_results),
        by_type=final_by_type,
    )


@router.get("/concepts", response_model=SearchResponse)
async def search_concepts(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity"),
):
    """
    Search concepts by semantic similarity.

    Uses vector embeddings to find concepts similar to the query text.
    """
    cache = get_cache_service()

    # Check cache first
    cached_results = await cache.get_search_results(q, "concepts")
    if cached_results:
        return SearchResponse(query=q, results=cached_results, total=len(cached_results))

    vector_service = get_vector_service()
    results = await vector_service.search_concepts(q, limit=limit, threshold=threshold)

    search_results = [
        SearchResult(
            id=r["concept_id"],
            name=r["concept_name"],
            content=r["content"],
            similarity=r["similarity"],
            type="concept",
        )
        for r in results
    ]

    # Cache results
    await cache.set_search_results(q, [r.model_dump() for r in search_results], "concepts")

    return SearchResponse(query=q, results=search_results, total=len(search_results))


@router.get("/analyses", response_model=SearchResponse)
async def search_analyses(
    q: str = Query(..., min_length=2, description="Search query"),
    move: Optional[str] = Query(None, description="Filter by DSRP move type"),
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.7, ge=0.0, le=1.0),
):
    """
    Search DSRP analyses by semantic similarity.

    Optionally filter by move type (is-is-not, zoom-in, zoom-out, etc.).
    """
    cache = get_cache_service()
    cache_key = f"{q}:{move}" if move else q

    cached_results = await cache.get_search_results(cache_key, "analyses")
    if cached_results:
        return SearchResponse(query=q, results=cached_results, total=len(cached_results))

    vector_service = get_vector_service()
    results = await vector_service.search_analyses(
        q, move_type=move, limit=limit, threshold=threshold
    )

    search_results = [
        SearchResult(
            id=r["analysis_id"],
            name=f"{r['move_type']} analysis",
            content=r["content"],
            similarity=r["similarity"],
            type="analysis",
        )
        for r in results
    ]

    await cache.set_search_results(cache_key, [r.model_dump() for r in search_results], "analyses")

    return SearchResponse(query=q, results=search_results, total=len(search_results))


@router.get("/sources", response_model=SearchResponse)
async def search_sources(
    q: str = Query(..., min_length=2, description="Search query"),
    source_ids: Optional[str] = Query(None, description="Comma-separated source IDs to filter"),
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.7, ge=0.0, le=1.0),
):
    """
    Search source content by semantic similarity (RAG retrieval).

    Returns relevant chunks from ingested sources.
    """
    vector_service = get_vector_service()

    source_id_list = source_ids.split(",") if source_ids else None

    results = await vector_service.search_sources(
        q, source_ids=source_id_list, limit=limit, threshold=threshold
    )

    search_results = [
        SearchResult(
            id=f"{r['source_id']}:{r['chunk_index']}",
            name=f"Source chunk {r['chunk_index']}",
            content=r["content"],
            similarity=r["similarity"],
            type="source",
        )
        for r in results
    ]

    return SearchResponse(query=q, results=search_results, total=len(search_results))


@router.get("/similar/{concept_id}")
async def find_similar_concepts(
    concept_id: str,
    limit: int = Query(5, ge=1, le=20),
):
    """
    Find concepts similar to a given concept.

    Useful for discovering related concepts in the knowledge graph.
    """
    vector_service = get_vector_service()
    results = await vector_service.find_similar_concepts(concept_id, limit=limit)

    return {
        "concept_id": concept_id,
        "similar": results,
    }


@router.post("/embed/concept/{concept_id}")
async def embed_concept(concept_id: str):
    """
    Create or update embedding for a concept.

    Typically called automatically when concepts are created/updated.
    """
    from app.services.typedb_service import get_typedb_service

    typedb = get_typedb_service()
    concept = await typedb.get_concept(concept_id)

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    vector_service = get_vector_service()
    success = await vector_service.embed_concept(
        concept_id=concept["id"],
        concept_name=concept["name"],
        description=concept.get("description"),
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to create embedding")

    return {"status": "embedded", "concept_id": concept_id}


@router.post("/embed/source/{source_id}")
async def embed_source(source_id: str):
    """
    Embed source content in chunks for RAG.

    Processes the source text and creates embeddings for semantic search.
    """
    from app.services.typedb_service import get_typedb_service

    typedb = get_typedb_service()
    text = await typedb.get_source_text(source_id)

    if not text:
        raise HTTPException(status_code=404, detail="Source text not found")

    vector_service = get_vector_service()
    chunk_count = await vector_service.embed_source_chunks(source_id, text)

    return {
        "status": "embedded",
        "source_id": source_id,
        "chunks": chunk_count,
    }


@router.post("/initialize")
async def initialize_vector_store():
    """
    Initialize the vector store tables.

    Creates necessary PostgreSQL tables and indexes for pgvector.
    """
    vector_service = get_vector_service()
    success = await vector_service.initialize()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to initialize vector store")

    return {"status": "initialized"}


# =============================================================================
# Hybrid Search
# =============================================================================

class HybridSearchResult(BaseModel):
    """Hybrid search result with score breakdown."""
    id: str
    content: str
    source: Optional[str] = None
    vector_score: float
    keyword_score: float
    combined_score: float
    metadata: Optional[dict] = None


class HybridSearchResponse(BaseModel):
    """Hybrid search response."""
    query: str
    results: list[HybridSearchResult]
    total: int
    search_mode: str


@router.get("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    vector_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for vector similarity"),
    keyword_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for keyword matching"),
    threshold: float = Query(0.4, ge=0.0, le=1.0, description="Minimum vector similarity"),
):
    """
    Hybrid search combining vector similarity and keyword matching.

    Uses Reciprocal Rank Fusion (RRF) to combine results from:
    - pgvector cosine similarity search
    - PostgreSQL full-text search

    This typically provides better results than pure vector search
    for queries with specific terminology or exact phrases.

    Args:
        q: Search query text
        limit: Maximum results
        vector_weight: Weight for vector similarity (0-1)
        keyword_weight: Weight for keyword matching (0-1)
        threshold: Minimum vector similarity threshold
    """
    from app.services.hybrid_search_service import get_hybrid_search_service

    service = get_hybrid_search_service()
    service.vector_weight = vector_weight
    service.keyword_weight = keyword_weight

    results = await service.search_documents(
        query=q,
        limit=limit,
        vector_threshold=threshold,
    )

    search_results = [
        HybridSearchResult(
            id=r.id,
            content=r.content,
            source=r.source,
            vector_score=r.vector_score,
            keyword_score=r.keyword_score,
            combined_score=r.combined_score,
            metadata=r.metadata,
        )
        for r in results
    ]

    return HybridSearchResponse(
        query=q,
        results=search_results,
        total=len(search_results),
        search_mode="hybrid_rrf",
    )
