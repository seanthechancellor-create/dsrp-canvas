"""
Study System API Endpoints

Exposes the 5-step study workflow:
1. GATHER - Upload and process source materials
2. REFLECTION - Apply DSRP 4-8-3 analysis
3. METACOGNITION - Build and explore knowledge graph
4. FIX/PRESENT - Review and correct analyses
5. ACTIVE RECALL - Generate questions for spaced repetition
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from agents.study_orchestrator import (
    get_study_orchestrator,
    StudyStep,
    StudySession,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreateSessionRequest(BaseModel):
    source_id: str
    source_name: str
    source_type: str = "document"


class SessionResponse(BaseModel):
    session_id: str
    source_id: str
    source_name: str
    current_step: str
    concepts_extracted: int = 0
    questions_generated: int = 0


class GatherRequest(BaseModel):
    session_id: str
    text: str
    chunks: Optional[list[str]] = None


class ReflectionRequest(BaseModel):
    session_id: str
    text: str
    analysis_depth: str = "standard"  # quick, standard, deep


class MetacognitionRequest(BaseModel):
    session_id: str


class FixPresentRequest(BaseModel):
    session_id: str
    corrections: Optional[list[dict]] = None


class ActiveRecallRequest(BaseModel):
    session_id: str
    questions_per_concept: int = 5


class CompleteWorkflowRequest(BaseModel):
    source_id: str
    source_name: str
    text: str
    source_type: str = "document"
    analysis_depth: str = "standard"
    questions_per_concept: int = 5


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new study session."""
    orchestrator = get_study_orchestrator()

    try:
        session = await orchestrator.create_session(
            source_id=request.source_id,
            source_name=request.source_name,
            source_type=request.source_type,
        )

        return SessionResponse(
            session_id=session.session_id,
            source_id=session.source_id,
            source_name=session.source_name,
            current_step=session.current_step.value,
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a study session by ID."""
    orchestrator = get_study_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.session_id,
        source_id=session.source_id,
        source_name=session.source_name,
        current_step=session.current_step.value,
        concepts_extracted=session.concepts_extracted,
        questions_generated=session.questions_generated,
    )


# =============================================================================
# STEP 1: GATHER
# =============================================================================

@router.post("/steps/gather")
async def step_gather(request: GatherRequest):
    """
    Step 1: Gather and prepare source material.

    Processes the uploaded text and prepares it for analysis.
    """
    orchestrator = get_study_orchestrator()

    try:
        result = await orchestrator.step_gather(
            session_id=request.session_id,
            text=request.text,
            chunks=request.chunks,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Step GATHER failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STEP 2: REFLECTION
# =============================================================================

@router.post("/steps/reflection")
async def step_reflection(request: ReflectionRequest):
    """
    Step 2: Reflection - Apply DSRP 4-8-3 analysis.

    Runs multiple AI agents:
    - Summary Agent: Hierarchical summaries
    - Structure Agent: Document organization
    - DSRP Agents: 8 moves analysis on key concepts
    """
    orchestrator = get_study_orchestrator()

    try:
        result = await orchestrator.step_reflection(
            session_id=request.session_id,
            text=request.text,
            analysis_depth=request.analysis_depth,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Step REFLECTION failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STEP 3: METACOGNITION
# =============================================================================

@router.post("/steps/metacognition")
async def step_metacognition(request: MetacognitionRequest):
    """
    Step 3: Metacognition - Build and understand the knowledge graph.

    Creates a visual knowledge map and finds cross-references.
    """
    orchestrator = get_study_orchestrator()

    try:
        result = await orchestrator.step_metacognition(
            session_id=request.session_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Step METACOGNITION failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STEP 4: FIX/PRESENT
# =============================================================================

@router.post("/steps/fix-present")
async def step_fix_present(request: FixPresentRequest):
    """
    Step 4: Fix errors and prepare for presentation.

    Allows user corrections before finalizing the knowledge.
    """
    orchestrator = get_study_orchestrator()

    try:
        result = await orchestrator.step_fix_present(
            session_id=request.session_id,
            corrections=request.corrections,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Step FIX_PRESENT failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STEP 5: ACTIVE RECALL
# =============================================================================

@router.post("/steps/active-recall")
async def step_active_recall(request: ActiveRecallRequest):
    """
    Step 5: Active Recall - Generate questions for spaced repetition.

    Creates a question bank based on DSRP patterns:
    - D: Distinction questions (What is X vs Y?)
    - S: System questions (What are parts of X?)
    - R: Relationship questions (What causes X?)
    - P: Perspective questions (How do stakeholders view X?)
    """
    orchestrator = get_study_orchestrator()

    try:
        result = await orchestrator.step_active_recall(
            session_id=request.session_id,
            questions_per_concept=request.questions_per_concept,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Step ACTIVE_RECALL failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMPLETE WORKFLOW
# =============================================================================

@router.post("/workflow/complete")
async def run_complete_workflow(request: CompleteWorkflowRequest):
    """
    Run the complete 5-step study workflow.

    This is a convenience endpoint that runs all steps in sequence:
    1. GATHER
    2. REFLECTION
    3. METACOGNITION
    4. FIX/PRESENT
    5. ACTIVE RECALL

    For large documents, consider using the individual step endpoints
    with a background task.
    """
    orchestrator = get_study_orchestrator()

    try:
        result = await orchestrator.run_complete_workflow(
            source_id=request.source_id,
            source_name=request.source_name,
            text=request.text,
            source_type=request.source_type,
            analysis_depth=request.analysis_depth,
            questions_per_concept=request.questions_per_concept,
        )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Complete workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@router.get("/sessions/{session_id}/export/remnote")
async def export_remnote(session_id: str):
    """Export question bank in RemNote format."""
    orchestrator = get_study_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.question_bank:
        raise HTTPException(status_code=400, detail="No questions generated yet")

    # Convert to RemNote format (simplified)
    remnote_export = []
    for concept_questions in session.question_bank:
        concept = concept_questions.get("concept", "")
        for q in concept_questions.get("questions", []):
            remnote_export.append({
                "text": q.get("question", ""),
                "children": [{"text": q.get("answer", "")}],
                "tags": q.get("tags", []) + [concept, session.source_name]
            })

    return {
        "format": "remnote",
        "source": session.source_name,
        "question_count": len(remnote_export),
        "data": remnote_export
    }


@router.get("/sessions/{session_id}/export/anki")
async def export_anki(session_id: str):
    """Export question bank in Anki-compatible format."""
    orchestrator = get_study_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.question_bank:
        raise HTTPException(status_code=400, detail="No questions generated yet")

    # Convert to Anki format (tab-separated for import)
    anki_cards = []
    for concept_questions in session.question_bank:
        concept = concept_questions.get("concept", "")
        for q in concept_questions.get("questions", []):
            tags = " ".join(q.get("tags", []) + [concept.replace(" ", "_")])
            anki_cards.append({
                "front": q.get("question", ""),
                "back": q.get("answer", ""),
                "tags": tags,
                "type": q.get("type", "basic")
            })

    return {
        "format": "anki",
        "source": session.source_name,
        "card_count": len(anki_cards),
        "data": anki_cards
    }


@router.get("/sessions/{session_id}/export/markdown")
async def export_markdown(session_id: str):
    """Export study notes in Markdown format (Obsidian-compatible)."""
    orchestrator = get_study_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build Markdown document
    md_lines = [
        f"# {session.source_name}",
        "",
        "## Summary",
        session.summary.get("executive_summary", "No summary available."),
        "",
        "## Key Themes",
    ]

    for theme in session.summary.get("key_themes", []):
        md_lines.append(f"- {theme}")

    md_lines.extend([
        "",
        "## Concepts",
        ""
    ])

    for analysis in session.dsrp_analyses:
        concept = analysis.get("concept", "")
        definition = analysis.get("definition", "")
        md_lines.extend([
            f"### [[{concept}]]",
            "",
            definition if definition else "",
            ""
        ])

        for move_analysis in analysis.get("analyses", []):
            pattern = move_analysis.get("pattern", "")
            move = move_analysis.get("move", "")
            reasoning = move_analysis.get("reasoning", "")

            md_lines.extend([
                f"#### {pattern}: {move}",
                reasoning,
                ""
            ])

    # Add questions section
    if session.question_bank:
        md_lines.extend([
            "",
            "## Study Questions",
            ""
        ])

        for concept_questions in session.question_bank:
            concept = concept_questions.get("concept", "")
            md_lines.append(f"### {concept}")
            md_lines.append("")

            for q in concept_questions.get("questions", []):
                md_lines.extend([
                    f"**Q:** {q.get('question', '')}",
                    f"**A:** {q.get('answer', '')}",
                    ""
                ])

    return {
        "format": "markdown",
        "source": session.source_name,
        "content": "\n".join(md_lines)
    }


# =============================================================================
# INFO ENDPOINT
# =============================================================================

@router.get("/info")
async def get_study_info():
    """Get information about the study system."""
    orchestrator = get_study_orchestrator()

    return {
        "name": "DSRP 4-8-3 Study System",
        "version": "1.0.0",
        "steps": [
            {
                "number": 1,
                "name": "GATHER",
                "description": "Collect and ingest source materials",
                "endpoint": "/api/study/steps/gather"
            },
            {
                "number": 2,
                "name": "REFLECTION",
                "description": "Apply DSRP 4-8-3 analysis with AI agents",
                "endpoint": "/api/study/steps/reflection"
            },
            {
                "number": 3,
                "name": "METACOGNITION",
                "description": "Build and explore knowledge graph",
                "endpoint": "/api/study/steps/metacognition"
            },
            {
                "number": 4,
                "name": "FIX/PRESENT",
                "description": "Review, correct, and present knowledge",
                "endpoint": "/api/study/steps/fix-present"
            },
            {
                "number": 5,
                "name": "ACTIVE RECALL",
                "description": "Generate questions for spaced repetition",
                "endpoint": "/api/study/steps/active-recall"
            }
        ],
        "dsrp_moves": [
            {"move": "is-is-not", "pattern": "D", "description": "Define what it IS and IS NOT"},
            {"move": "zoom-in", "pattern": "S", "description": "Examine the parts"},
            {"move": "zoom-out", "pattern": "S", "description": "Examine the whole/context"},
            {"move": "part-party", "pattern": "S", "description": "Parts and their relationships"},
            {"move": "rds-barbell", "pattern": "R", "description": "Relate, Distinguish, Systematize"},
            {"move": "p-circle", "pattern": "P", "description": "Map multiple perspectives"},
            {"move": "woc", "pattern": "R", "description": "Web of Causality (forward effects)"},
            {"move": "waoc", "pattern": "R", "description": "Web of Anticausality (root causes)"}
        ],
        "export_formats": ["remnote", "anki", "markdown"],
        "ai_provider": orchestrator.dsrp_agent.active_provider.name if orchestrator.dsrp_agent.active_provider else None
    }
