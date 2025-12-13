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
