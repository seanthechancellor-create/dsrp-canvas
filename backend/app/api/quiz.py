"""
Quiz API endpoints for DSRP-based testing.
Supports creating quiz sessions, answering questions, and getting results.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.quiz_service import (
    create_quiz_session,
    answer_question,
    get_quiz_results,
    get_session_state,
    generate_quiz_questions,
)

router = APIRouter()


class CreateQuizRequest(BaseModel):
    concept_ids: list[str] | None = None
    patterns: list[str] | None = None  # Filter by D, S, R, P
    domain: str | None = None  # Filter by domain (e.g., "CIPP/E", "CIPP/US")
    topic: str | None = None   # Filter by topic within domain
    question_count: int = 10


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_index: int


@router.post("/start")
async def start_quiz(request: CreateQuizRequest):
    """
    Start a new quiz session.

    Args:
        concept_ids: Optional list of concept IDs to quiz on
        patterns: Optional filter by DSRP patterns (D, S, R, P)
        domain: Optional filter by domain (e.g., "CIPP/E", "CIPP/US", "CIPM")
        topic: Optional filter by topic within domain
        question_count: Number of questions (default 10)

    Returns:
        Session ID and first question
    """
    result = await create_quiz_session(
        concept_ids=request.concept_ids,
        patterns=request.patterns,
        domain=request.domain,
        topic=request.topic,
        question_count=request.question_count,
    )
    return result


@router.post("/answer")
async def submit_answer(request: AnswerRequest):
    """
    Submit an answer to the current question.

    Returns:
        Whether answer was correct, explanation, score, and next question
    """
    result = await answer_question(
        session_id=request.session_id,
        question_id=request.question_id,
        answer_index=request.answer_index,
    )
    return result


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get current state of a quiz session."""
    return await get_session_state(session_id)


@router.get("/results/{session_id}")
async def get_results(session_id: str):
    """
    Get final results for a completed quiz.

    Returns:
        Score, pattern-wise breakdown, weak concepts, and recommendations
    """
    return await get_quiz_results(session_id)


@router.post("/preview")
async def preview_questions(request: CreateQuizRequest):
    """
    Preview generated questions without starting a session.
    Useful for testing question generation.
    """
    questions = await generate_quiz_questions(
        concept_ids=request.concept_ids,
        patterns=request.patterns,
        count=request.question_count,
    )
    return {
        "count": len(questions),
        "questions": questions,
    }
