import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.typedb_service import get_typedb_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Fallback in-memory store (used when TypeDB unavailable)
concepts_db: dict[str, dict] = {}


class ConceptCreate(BaseModel):
    name: str
    description: str | None = None
    source_ids: list[str] = []


class ConceptResponse(BaseModel):
    id: str
    name: str
    description: str | None
    source_ids: list[str]
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=ConceptResponse)
async def create_concept(concept: ConceptCreate):
    """Create a new concept in the knowledge graph."""
    concept_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Try to create in TypeDB first
    typedb = get_typedb_service()
    try:
        result = await typedb.create_concept(
            concept_id=concept_id,
            name=concept.name,
            description=concept.description,
        )
        logger.info(f"Created concept in TypeDB: {concept_id}")
        return ConceptResponse(
            id=result["id"],
            name=concept.name,
            description=concept.description,
            source_ids=concept.source_ids,
            created_at=now,
            updated_at=now,
        )
    except Exception as e:
        logger.warning(f"TypeDB unavailable, using in-memory: {e}")

    # Fallback to in-memory
    record = {
        "id": concept_id,
        "name": concept.name,
        "description": concept.description,
        "source_ids": concept.source_ids,
        "created_at": now,
        "updated_at": now,
    }
    concepts_db[concept_id] = record

    return ConceptResponse(**record)


@router.get("/{concept_id}", response_model=ConceptResponse)
async def get_concept(concept_id: str):
    """Get a concept by ID."""
    # Try TypeDB first
    typedb = get_typedb_service()
    try:
        result = await typedb.get_concept(concept_id)
        if result:
            return ConceptResponse(
                id=result["id"],
                name=result["name"],
                description=result.get("description"),
                source_ids=[],
                created_at=result.get("created_at", datetime.utcnow()),
                updated_at=result.get("updated_at", datetime.utcnow()),
            )
    except Exception as e:
        logger.debug(f"TypeDB lookup failed: {e}")

    # Fallback to in-memory
    if concept_id not in concepts_db:
        raise HTTPException(status_code=404, detail="Concept not found")
    return ConceptResponse(**concepts_db[concept_id])


@router.get("/")
async def list_concepts(limit: int = 50, offset: int = 0):
    """List all concepts with pagination."""
    # Try TypeDB first
    typedb = get_typedb_service()
    try:
        results = await typedb.list_concepts(limit=limit, offset=offset)
        if results:
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r.get("description"),
                    "source_ids": [],
                    "created_at": r.get("created_at"),
                    "updated_at": r.get("updated_at"),
                }
                for r in results
            ]
    except Exception as e:
        logger.debug(f"TypeDB list failed: {e}")

    # Fallback to in-memory
    all_concepts = list(concepts_db.values())
    return all_concepts[offset : offset + limit]


@router.delete("/{concept_id}")
async def delete_concept(concept_id: str):
    """Delete a concept."""
    # Try TypeDB first
    typedb = get_typedb_service()
    try:
        deleted = await typedb.delete_concept(concept_id)
        if deleted:
            logger.info(f"Deleted concept from TypeDB: {concept_id}")
            return {"deleted": concept_id}
    except Exception as e:
        logger.debug(f"TypeDB delete failed: {e}")

    # Fallback to in-memory
    if concept_id not in concepts_db:
        raise HTTPException(status_code=404, detail="Concept not found")
    del concepts_db[concept_id]
    return {"deleted": concept_id}


@router.get("/graph/stats")
async def get_graph_stats():
    """Get statistics about the knowledge graph."""
    typedb = get_typedb_service()
    try:
        stats = await typedb.get_graph_stats()
        return {
            "success": True,
            "stats": stats,
        }
    except Exception as e:
        logger.warning(f"Failed to get graph stats: {e}")
        # Return in-memory stats as fallback
        return {
            "success": False,
            "stats": {
                "concepts": len(concepts_db),
                "analyses": 0,
                "distinctions": 0,
                "systems": 0,
                "relationships": 0,
                "perspectives": 0,
                "sources": 0,
            },
            "error": str(e),
        }


@router.get("/graph/export")
async def export_concept_graph(limit: int = 100):
    """Export the concept graph for visualization."""
    typedb = get_typedb_service()
    try:
        graph = await typedb.export_concept_graph(limit=limit)
        return {
            "success": True,
            "graph": graph,
        }
    except Exception as e:
        logger.warning(f"Failed to export graph: {e}")
        # Return in-memory concepts as fallback
        nodes = [
            {"id": c["id"], "label": c["name"], "type": "concept"}
            for c in concepts_db.values()
        ]
        return {
            "success": False,
            "graph": {
                "nodes": nodes,
                "edges": [],
                "stats": {"node_count": len(nodes), "edge_count": 0},
            },
            "error": str(e),
        }


@router.get("/{concept_id}/relations")
async def get_concept_relations(concept_id: str):
    """Get all DSRP relations for a concept."""
    typedb = get_typedb_service()
    try:
        relations = await typedb.get_concept_relations(concept_id)
        return {
            "concept_id": concept_id,
            "relations": relations,
        }
    except Exception as e:
        logger.warning(f"Failed to get relations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
