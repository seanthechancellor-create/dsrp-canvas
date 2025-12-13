import logging
import uuid

from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

from agents.dsrp_agent import DSRPAgent
from app.services.typedb_service import get_typedb_service

logger = logging.getLogger(__name__)
router = APIRouter()

dsrp_agent = DSRPAgent()


class AnalysisRequest(BaseModel):
    concept: str
    move: str
    context: str | None = None


class AnalysisResponse(BaseModel):
    pattern: str
    elements: dict
    move: str
    reasoning: str | None = None
    related_concepts: list[str] = []
    confidence: float = 0.85
    provider: str | None = None
    concept: str | None = None


@router.post("/dsrp", response_model=AnalysisResponse)
async def analyze_with_dsrp(request: AnalysisRequest):
    """
    Analyze a concept using DSRP 4-8-3 framework.

    Available moves:
    - is-is-not: Define what it is AND is not (Distinctions)
    - zoom-in: Examine the parts (Systems)
    - zoom-out: Examine the broader system (Systems)
    - part-party: Break into parts and relate them (Systems)
    - rds-barbell: Relate → Distinguish → Systematize (Relationships)
    - p-circle: Map multiple perspectives (Perspectives)
    """
    valid_moves = ["is-is-not", "zoom-in", "zoom-out", "part-party", "rds-barbell", "p-circle"]
    if request.move not in valid_moves:
        raise HTTPException(
            status_code=400, detail=f"Invalid move. Must be one of: {valid_moves}"
        )

    result = await dsrp_agent.analyze(
        concept=request.concept,
        move=request.move,
        context=request.context,
    )

    # Persist analysis to TypeDB
    typedb = get_typedb_service()
    try:
        # Ensure concept exists, create if not
        existing = await typedb.get_concept_by_name(request.concept)
        if not existing:
            concept_id = str(uuid.uuid4())
            await typedb.create_concept(
                concept_id=concept_id,
                name=request.concept,
                description=f"Auto-created from DSRP analysis",
            )
            logger.info(f"Created concept for analysis: {request.concept}")
        else:
            concept_id = existing["id"]

        # Store the analysis
        analysis_id = str(uuid.uuid4())
        await typedb.create_analysis(
            analysis_id=analysis_id,
            concept_id=concept_id,
            pattern_type=result.get("pattern", ""),
            move_type=request.move,
            reasoning=result.get("reasoning", ""),
            confidence_score=result.get("confidence", 0.85),
        )
        logger.info(f"Stored analysis {analysis_id} for concept {concept_id}")

        # Create related concepts and relationships from analysis
        await _store_related_concepts(typedb, concept_id, result)

    except Exception as e:
        logger.warning(f"Failed to persist analysis to TypeDB: {e}")

    return AnalysisResponse(**result)


async def _store_related_concepts(typedb, concept_id: str, result: dict):
    """Extract and store related concepts from analysis results."""
    elements = result.get("elements", {})
    pattern = result.get("pattern", "")
    move = result.get("move", "")

    try:
        # Handle zoom-in: create part relationships
        if move == "zoom-in" and isinstance(elements.get("parts"), list):
            for part_name in elements["parts"][:10]:  # Limit to 10 parts
                if not part_name or not isinstance(part_name, str):
                    continue
                # Create part concept if needed
                part = await typedb.get_concept_by_name(part_name)
                if not part:
                    part_id = str(uuid.uuid4())
                    await typedb.create_concept(
                        concept_id=part_id,
                        name=part_name,
                        description=result.get("part_descriptions", {}).get(part_name),
                    )
                else:
                    part_id = part["id"]

                # Create system-structure relation
                await typedb.create_system_structure(
                    system_id=str(uuid.uuid4()),
                    whole_concept_id=concept_id,
                    part_concept_id=part_id,
                )

        # Handle zoom-out: create whole relationship
        elif move == "zoom-out" and elements.get("whole"):
            whole_name = elements["whole"]
            if isinstance(whole_name, str):
                whole = await typedb.get_concept_by_name(whole_name)
                if not whole:
                    whole_id = str(uuid.uuid4())
                    await typedb.create_concept(
                        concept_id=whole_id,
                        name=whole_name,
                    )
                else:
                    whole_id = whole["id"]

                await typedb.create_system_structure(
                    system_id=str(uuid.uuid4()),
                    whole_concept_id=whole_id,
                    part_concept_id=concept_id,
                )

        # Handle is-is-not: create distinction
        elif move == "is-is-not" and elements.get("other"):
            other_text = elements["other"]
            if isinstance(other_text, str) and len(other_text) < 100:
                other = await typedb.get_concept_by_name(other_text)
                if not other:
                    other_id = str(uuid.uuid4())
                    await typedb.create_concept(
                        concept_id=other_id,
                        name=other_text,
                    )
                else:
                    other_id = other["id"]

                await typedb.create_distinction(
                    distinction_id=str(uuid.uuid4()),
                    identity_concept_id=concept_id,
                    other_concept_id=other_id,
                    label=elements.get("boundary"),
                )

        # Handle rds-barbell: create relationships
        elif move == "rds-barbell" and isinstance(elements.get("reactions"), list):
            for reaction_name in elements["reactions"][:10]:
                if not reaction_name or not isinstance(reaction_name, str):
                    continue
                reaction = await typedb.get_concept_by_name(reaction_name)
                if not reaction:
                    reaction_id = str(uuid.uuid4())
                    await typedb.create_concept(
                        concept_id=reaction_id,
                        name=reaction_name,
                    )
                else:
                    reaction_id = reaction["id"]

                await typedb.create_relationship_link(
                    relationship_id=str(uuid.uuid4()),
                    action_concept_id=concept_id,
                    reaction_concept_id=reaction_id,
                )

        # Handle p-circle: create perspective relations
        elif move == "p-circle" and isinstance(elements.get("perspectives"), list):
            for perspective in elements["perspectives"][:10]:
                if not isinstance(perspective, dict):
                    continue
                point_name = perspective.get("point")
                if not point_name or not isinstance(point_name, str):
                    continue

                point = await typedb.get_concept_by_name(point_name)
                if not point:
                    point_id = str(uuid.uuid4())
                    await typedb.create_concept(
                        concept_id=point_id,
                        name=point_name,
                        description=perspective.get("view"),
                    )
                else:
                    point_id = point["id"]

                await typedb.create_perspective_view(
                    perspective_id=str(uuid.uuid4()),
                    point_concept_id=point_id,
                    view_concept_id=concept_id,
                    label=perspective.get("view", "")[:100] if perspective.get("view") else None,
                )

    except Exception as e:
        logger.warning(f"Failed to store related concepts: {e}")


@router.post("/batch")
async def batch_analyze(
    concepts: list[str] = Body(...),
    moves: list[str] | None = Query(default=None),
):
    """Analyze multiple concepts with all or specified moves."""
    moves = moves or ["is-is-not", "zoom-in", "zoom-out", "part-party", "rds-barbell", "p-circle"]
    results = []

    for concept in concepts:
        concept_results = {}
        for move in moves:
            result = await dsrp_agent.analyze(concept=concept, move=move)
            concept_results[move] = result
        results.append({"concept": concept, "analyses": concept_results})

    return results
