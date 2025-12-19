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
    domain: str | None = None  # e.g., "CIPP/E", "CIPP/US", "CIPM"
    topic: str | None = None   # e.g., "Legal Bases", "Data Subject Rights"
    chapter: str | None = None  # e.g., "Chapter 3", "Module 2"
    source_document: str | None = None  # e.g., "CIPP-E-Study-Guide.pdf"
    knowledge_structure: str | None = None  # e.g., "hierarchy", "sequence", "compare-contrast"


class ConceptResponse(BaseModel):
    id: str
    name: str
    description: str | None
    source_ids: list[str]
    domain: str | None = None
    topic: str | None = None
    chapter: str | None = None
    source_document: str | None = None
    knowledge_structure: str | None = None
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
        "domain": concept.domain,
        "topic": concept.topic,
        "chapter": concept.chapter,
        "source_document": concept.source_document,
        "knowledge_structure": concept.knowledge_structure,
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
async def list_concepts(
    limit: int = 50,
    offset: int = 0,
    domain: str | None = None,
    topic: str | None = None,
):
    """List concepts with pagination and optional domain/topic filtering."""
    # Try TypeDB first
    typedb = get_typedb_service()
    try:
        results = await typedb.list_concepts(limit=limit, offset=offset)
        if results:
            concepts = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r.get("description"),
                    "source_ids": [],
                    "domain": r.get("domain"),
                    "topic": r.get("topic"),
                    "chapter": r.get("chapter"),
                    "source_document": r.get("source_document"),
                    "knowledge_structure": r.get("knowledge_structure"),
                    "created_at": r.get("created_at"),
                    "updated_at": r.get("updated_at"),
                }
                for r in results
            ]
            # Filter by domain/topic if specified
            if domain:
                concepts = [c for c in concepts if c.get("domain") == domain]
            if topic:
                concepts = [c for c in concepts if c.get("topic") == topic]
            return concepts
    except Exception as e:
        logger.debug(f"TypeDB list failed: {e}")

    # Fallback to in-memory
    all_concepts = list(concepts_db.values())

    # Filter by domain and topic
    if domain:
        all_concepts = [c for c in all_concepts if c.get("domain") == domain]
    if topic:
        all_concepts = [c for c in all_concepts if c.get("topic") == topic]

    return all_concepts[offset : offset + limit]


@router.get("/domains/list")
async def list_domains():
    """Get all available domains and their topics.

    Merges data from both TypeDB and in-memory stores to ensure
    seeded data is available even when TypeDB has older concepts.
    """
    domains = {}

    # First check in-memory store (where seed data lives)
    for c in concepts_db.values():
        domain = c.get("domain")
        topic = c.get("topic")
        if domain:
            if domain not in domains:
                domains[domain] = {"name": domain, "topics": set(), "count": 0}
            domains[domain]["count"] += 1
            if topic:
                domains[domain]["topics"].add(topic)

    # Also check TypeDB for any additional domain-tagged concepts
    typedb = get_typedb_service()
    try:
        results = await typedb.list_concepts(limit=1000, offset=0)
        if results:
            for r in results:
                domain = r.get("domain")
                topic = r.get("topic")
                if domain:
                    if domain not in domains:
                        domains[domain] = {"name": domain, "topics": set(), "count": 0}
                    domains[domain]["count"] += 1
                    if topic:
                        domains[domain]["topics"].add(topic)
    except Exception as e:
        logger.debug(f"TypeDB domains list failed: {e}")

    # Convert sets to lists for JSON serialization
    for d in domains.values():
        d["topics"] = sorted(list(d["topics"]))

    return {
        "domains": list(domains.values()),
        "total_domains": len(domains),
    }


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


@router.post("/init-database")
async def initialize_database():
    """Initialize TypeDB database with required schema.

    Creates the database if it doesn't exist and defines the schema
    for concepts, analyses, sources, and DSRP relations.
    """
    typedb = get_typedb_service()

    # Schema that matches what the service expects
    schema = """
    define

    # Attributes
    attribute concept_id, value string;
    attribute analysis_id, value string;
    attribute analysis_link_id, value string;
    attribute source_id, value string;
    attribute name, value string;
    attribute description, value string;
    attribute source_type, value string;
    attribute file_path, value string;
    attribute original_filename, value string;
    attribute extracted_text, value string;
    attribute pattern_type, value string;
    attribute move_type, value string;
    attribute reasoning, value string;
    attribute confidence_score, value double;
    attribute created_at, value datetime;
    attribute updated_at, value datetime;

    # DSRP relation IDs and labels
    attribute distinction_id, value string;
    attribute distinction_label, value string;
    attribute system_id, value string;
    attribute system_label, value string;
    attribute relationship_id, value string;
    attribute relationship_type, value string;
    attribute relationship_label, value string;
    attribute perspective_id, value string;
    attribute perspective_label, value string;

    # Entities
    entity dsrp_concept,
        owns concept_id @key,
        owns name,
        owns description,
        owns created_at,
        owns updated_at,
        plays distinction:identity,
        plays distinction:other,
        plays system_structure:whole,
        plays system_structure:part,
        plays relationship_link:action,
        plays relationship_link:reaction,
        plays perspective_view:point,
        plays perspective_view:view,
        plays analysis_rel:subject;

    entity dsrp_analysis,
        owns analysis_id @key,
        owns pattern_type,
        owns move_type,
        owns reasoning,
        owns confidence_score,
        owns created_at,
        plays analysis_rel:result;

    entity source,
        owns source_id @key,
        owns source_type,
        owns file_path,
        owns original_filename,
        owns extracted_text,
        owns created_at;

    # Relations
    relation analysis_rel,
        owns analysis_link_id @key,
        relates subject,
        relates result;

    relation distinction,
        owns distinction_id @key,
        owns distinction_label,
        relates identity,
        relates other;

    relation system_structure,
        owns system_id @key,
        owns system_label,
        relates whole,
        relates part;

    relation relationship_link,
        owns relationship_id @key,
        owns relationship_type,
        owns relationship_label,
        relates action,
        relates reaction;

    relation perspective_view,
        owns perspective_id @key,
        owns perspective_label,
        relates point,
        relates view;
    """

    try:
        driver = typedb.driver
        if not driver:
            return {"success": False, "error": "TypeDB driver not available"}

        db_name = "dsrp_483"

        # Check if database exists
        databases = driver.databases.all()
        db_names = [db.name for db in databases]

        if db_name in db_names:
            # Delete existing database to recreate with fresh schema
            driver.databases.get(db_name).delete()
            logger.info(f"Deleted existing database: {db_name}")

        # Create database
        driver.databases.create(db_name)
        logger.info(f"Created database: {db_name}")

        # Define schema
        from typedb.driver import TransactionType

        tx = driver.transaction(db_name, TransactionType.SCHEMA)
        try:
            tx.query(schema).resolve()
            tx.commit()
            logger.info("Schema defined successfully")
        except Exception as e:
            tx.close()
            # Schema might already exist
            if "already defined" in str(e).lower() or "exists" in str(e).lower():
                logger.info("Schema already exists")
            else:
                raise e

        return {
            "success": True,
            "message": "Database initialized successfully",
            "database": db_name,
        }
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return {
            "success": False,
            "error": str(e),
        }
