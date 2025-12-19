"""
Quiz service for generating DSRP-based quiz questions from knowledge graph.
Supports pattern-based questioning for exam prep with spaced repetition.
"""

import logging
import random
import uuid
from typing import Any

from app.services.typedb_service import get_typedb_service

logger = logging.getLogger(__name__)

# In-memory storage for quiz sessions
quiz_sessions: dict[str, dict] = {}

# Question templates by DSRP pattern and move
QUESTION_TEMPLATES = {
    "is-is-not": {
        "identity": {
            "template": "What IS {concept}?",
            "field": "identity",
            "pattern": "D",
            "hint": "Think about the defining characteristics",
        },
        "other": {
            "template": "What is {concept} NOT?",
            "field": "other",
            "pattern": "D",
            "hint": "Think about what falls outside the boundary",
        },
        "boundary": {
            "template": "What is the boundary/distinguishing line for {concept}?",
            "field": "boundary",
            "pattern": "D",
            "hint": "What separates identity from other?",
        },
    },
    "zoom-in": {
        "parts": {
            "template": "What are the parts/components of {concept}?",
            "field": "parts",
            "pattern": "S",
            "hint": "Think about the internal structure",
        },
    },
    "zoom-out": {
        "whole": {
            "template": "What larger system/context contains {concept}?",
            "field": "whole",
            "pattern": "S",
            "hint": "Think about what this is part of",
        },
    },
    "part-party": {
        "relations": {
            "template": "How do the parts of {concept} relate to each other?",
            "field": "reasoning",
            "pattern": "S",
            "hint": "Think about interactions between components",
        },
    },
    "rds-barbell": {
        "reactions": {
            "template": "What are the relationships/reactions of {concept}?",
            "field": "reactions",
            "pattern": "R",
            "hint": "Think about what this connects to",
        },
    },
    "woc": {
        "effects": {
            "template": "What effects does {concept} cause? (Web of Causality)",
            "field": "effects",
            "pattern": "R",
            "hint": "Think about downstream consequences",
        },
    },
    "waoc": {
        "causes": {
            "template": "What are the root causes of {concept}? (Web of Anticausality)",
            "field": "causes",
            "pattern": "R",
            "hint": "Think about upstream factors",
        },
    },
    "p-circle": {
        "perspectives": {
            "template": "What are different perspectives on {concept}?",
            "field": "perspectives",
            "pattern": "P",
            "hint": "Think about different viewpoints",
        },
    },
}

# Distractors - common wrong answers by pattern type
DISTRACTORS = {
    "D": [
        "All of the above",
        "None of the above",
        "It depends on context",
        "This is undefined",
        "No clear distinction exists",
    ],
    "S": [
        "No internal structure",
        "Single monolithic entity",
        "Unrelated elements",
        "Random components",
        "No containing system",
    ],
    "R": [
        "No relationships exist",
        "Isolated phenomenon",
        "Unrelated to other concepts",
        "No causal connections",
        "Independent entity",
    ],
    "P": [
        "Only one perspective exists",
        "Universal agreement",
        "No alternative views",
        "Objective truth only",
        "Single valid interpretation",
    ],
}


def _get_analyses_db():
    """Get the shared analyses db from the export service module."""
    try:
        from app.services.export_service import analyses_db
        return analyses_db
    except ImportError:
        return {}


def _get_concepts_db():
    """Get the shared concepts db from the concepts API module."""
    try:
        from app.api.concepts import concepts_db
        return concepts_db
    except ImportError:
        return {}


def _format_answer(value: Any) -> str:
    """Format a value as a readable answer string."""
    if isinstance(value, list):
        if len(value) == 0:
            return ""
        # Handle list of dicts (effects, causes, perspectives)
        if isinstance(value[0], dict):
            items = []
            for item in value[:4]:
                if "effect" in item:
                    items.append(item["effect"])
                elif "cause" in item:
                    items.append(item["cause"])
                elif "point" in item and "view" in item:
                    items.append(f"{item['point']}: {item['view']}")
                else:
                    items.append(str(list(item.values())[0]) if item else "")
            return ", ".join(items)
        return ", ".join(str(v) for v in value[:4])
    return str(value) if value else ""


def _generate_wrong_answers(correct: str, pattern: str, all_answers: list[str]) -> list[str]:
    """Generate plausible wrong answers."""
    wrong = []

    # Add some answers from other concepts if available
    other_answers = [a for a in all_answers if a != correct and len(a) > 5]
    if other_answers:
        wrong.extend(random.sample(other_answers, min(2, len(other_answers))))

    # Add pattern-specific distractors
    distractors = DISTRACTORS.get(pattern, DISTRACTORS["D"])
    remaining = 3 - len(wrong)
    wrong.extend(random.sample(distractors, min(remaining, len(distractors))))

    return wrong[:3]


async def generate_quiz_questions(
    concept_ids: list[str] | None = None,
    patterns: list[str] | None = None,
    domain: str | None = None,
    topic: str | None = None,
    count: int = 10,
) -> list[dict[str, Any]]:
    """
    Generate quiz questions from DSRP analyses.

    Args:
        concept_ids: Optional list of concept IDs to quiz on
        patterns: Optional filter by DSRP patterns (D, S, R, P)
        domain: Optional filter by domain (e.g., "CIPP/E", "CIPP/US")
        topic: Optional filter by topic within domain
        count: Number of questions to generate

    Returns:
        List of question objects with question, options, correct answer
    """
    questions = []
    all_answers = []  # Collect all answers for generating distractors

    typedb = get_typedb_service()
    analyses_db = _get_analyses_db()
    concepts_db = _get_concepts_db()

    # Get all concepts if none specified
    if not concept_ids:
        # Filter by domain/topic if specified
        filtered_concepts = []
        for cid, concept in concepts_db.items():
            if domain and concept.get("domain") != domain:
                continue
            if topic and concept.get("topic") != topic:
                continue
            filtered_concepts.append(cid)

        concept_ids = filtered_concepts if filtered_concepts else list(concepts_db.keys())

        try:
            typedb_concepts = await typedb.get_all_concepts()
            for c in typedb_concepts:
                if c.get("id"):
                    # Apply domain/topic filter
                    if domain and c.get("domain") != domain:
                        continue
                    if topic and c.get("topic") != topic:
                        continue
                    concept_ids.append(c["id"])
        except Exception as e:
            logger.debug(f"TypeDB concepts fetch failed: {e}")

    # Collect analyses for all concepts
    concept_analyses = []
    for concept_id in concept_ids:
        concept = None
        analyses = []

        try:
            concept = await typedb.get_concept(concept_id)
            analyses = await typedb.get_analyses_for_concept(concept_id)
        except Exception as e:
            logger.debug(f"TypeDB lookup failed for {concept_id}: {e}")

        if not concept:
            concept = concepts_db.get(concept_id, {"name": concept_id})
        if not analyses:
            analyses = analyses_db.get(concept_id, [])

        for analysis in analyses:
            concept_analyses.append({
                "concept_id": concept_id,
                "concept_name": concept.get("name", concept_id),
                "analysis": analysis,
            })

            # Collect answers for distractor generation
            elements = analysis.get("elements", {})
            for key, value in elements.items():
                formatted = _format_answer(value)
                if formatted and len(formatted) > 5:
                    all_answers.append(formatted)

    # Generate questions from analyses
    for item in concept_analyses:
        analysis = item["analysis"]
        concept_name = item["concept_name"]
        move = analysis.get("move", "")
        elements = analysis.get("elements", {})

        if move not in QUESTION_TEMPLATES:
            continue

        templates = QUESTION_TEMPLATES[move]

        for q_type, template_info in templates.items():
            # Filter by pattern if specified
            if patterns and template_info["pattern"] not in patterns:
                continue

            field = template_info["field"]

            # Get the correct answer
            if field == "reasoning":
                correct_answer = _format_answer(analysis.get("reasoning", ""))
            else:
                correct_answer = _format_answer(elements.get(field, ""))

            if not correct_answer or len(correct_answer) < 3:
                continue

            # Generate wrong answers
            wrong_answers = _generate_wrong_answers(
                correct_answer,
                template_info["pattern"],
                all_answers
            )

            # Create options (shuffle correct answer in)
            options = wrong_answers + [correct_answer]
            random.shuffle(options)

            questions.append({
                "id": str(uuid.uuid4()),
                "question": template_info["template"].format(concept=concept_name),
                "concept": concept_name,
                "concept_id": item["concept_id"],
                "pattern": template_info["pattern"],
                "move": move,
                "options": options,
                "correct_answer": correct_answer,
                "correct_index": options.index(correct_answer),
                "hint": template_info["hint"],
                "tags": [f"DSRP", template_info["pattern"], move, concept_name],
            })

    # Shuffle and limit
    random.shuffle(questions)
    return questions[:count]


async def create_quiz_session(
    concept_ids: list[str] | None = None,
    patterns: list[str] | None = None,
    domain: str | None = None,
    topic: str | None = None,
    question_count: int = 10,
) -> dict[str, Any]:
    """
    Create a new quiz session.

    Returns:
        Session object with ID, questions, and initial state
    """
    questions = await generate_quiz_questions(concept_ids, patterns, domain, topic, question_count)

    if not questions:
        return {
            "error": "No questions could be generated. Analyze some concepts first.",
            "session_id": None,
        }

    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "questions": questions,
        "current_index": 0,
        "answers": [],
        "score": 0,
        "total": len(questions),
        "completed": False,
        "patterns_filter": patterns,
        "domain_filter": domain,
        "topic_filter": topic,
        "concept_ids_filter": concept_ids,
    }

    quiz_sessions[session_id] = session

    # Return session without revealing correct answers
    return {
        "session_id": session_id,
        "total_questions": len(questions),
        "patterns": patterns,
        "domain": domain,
        "topic": topic,
        "current_question": _sanitize_question(questions[0]) if questions else None,
    }


def _sanitize_question(question: dict) -> dict:
    """Remove correct answer from question for client."""
    return {
        "id": question["id"],
        "question": question["question"],
        "concept": question["concept"],
        "pattern": question["pattern"],
        "move": question["move"],
        "options": question["options"],
        "hint": question["hint"],
        "tags": question["tags"],
    }


async def answer_question(
    session_id: str,
    question_id: str,
    answer_index: int,
) -> dict[str, Any]:
    """
    Submit an answer to a quiz question.

    Returns:
        Result with correct/incorrect, explanation, and next question
    """
    session = quiz_sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}

    # Find the question
    question = None
    for q in session["questions"]:
        if q["id"] == question_id:
            question = q
            break

    if not question:
        return {"error": "Question not found"}

    is_correct = answer_index == question["correct_index"]

    if is_correct:
        session["score"] += 1

    session["answers"].append({
        "question_id": question_id,
        "answer_index": answer_index,
        "correct": is_correct,
    })

    session["current_index"] += 1

    # Check if quiz is complete
    next_question = None
    if session["current_index"] < len(session["questions"]):
        next_question = _sanitize_question(session["questions"][session["current_index"]])
    else:
        session["completed"] = True

    return {
        "correct": is_correct,
        "correct_answer": question["correct_answer"],
        "correct_index": question["correct_index"],
        "explanation": f"[{question['pattern']}] {question['move'].replace('-', ' ').title()}: {question['correct_answer']}",
        "score": session["score"],
        "answered": len(session["answers"]),
        "total": session["total"],
        "completed": session["completed"],
        "next_question": next_question,
        "percentage": round((session["score"] / len(session["answers"])) * 100) if session["answers"] else 0,
    }


async def get_quiz_results(session_id: str) -> dict[str, Any]:
    """Get final results for a completed quiz session."""
    session = quiz_sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}

    # Calculate pattern-wise scores
    pattern_scores = {"D": {"correct": 0, "total": 0}, "S": {"correct": 0, "total": 0},
                      "R": {"correct": 0, "total": 0}, "P": {"correct": 0, "total": 0}}

    weak_concepts = []

    for i, answer in enumerate(session["answers"]):
        question = session["questions"][i]
        pattern = question["pattern"]
        pattern_scores[pattern]["total"] += 1

        if answer["correct"]:
            pattern_scores[pattern]["correct"] += 1
        else:
            weak_concepts.append({
                "concept": question["concept"],
                "concept_id": question["concept_id"],
                "pattern": pattern,
                "move": question["move"],
                "question": question["question"],
                "your_answer": question["options"][answer["answer_index"]],
                "correct_answer": question["correct_answer"],
            })

    # Calculate percentages
    for pattern in pattern_scores:
        total = pattern_scores[pattern]["total"]
        if total > 0:
            pattern_scores[pattern]["percentage"] = round(
                (pattern_scores[pattern]["correct"] / total) * 100
            )
        else:
            pattern_scores[pattern]["percentage"] = None

    return {
        "session_id": session_id,
        "score": session["score"],
        "total": session["total"],
        "percentage": round((session["score"] / session["total"]) * 100) if session["total"] else 0,
        "pattern_scores": pattern_scores,
        "weak_concepts": weak_concepts,
        "completed": session["completed"],
        "recommendation": _generate_recommendation(pattern_scores, weak_concepts),
    }


def _generate_recommendation(pattern_scores: dict, weak_concepts: list) -> str:
    """Generate study recommendation based on quiz results."""
    weakest_pattern = None
    lowest_pct = 100

    for pattern, scores in pattern_scores.items():
        if scores["total"] > 0 and scores["percentage"] < lowest_pct:
            lowest_pct = scores["percentage"]
            weakest_pattern = pattern

    pattern_names = {
        "D": "Distinctions (is/is-not)",
        "S": "Systems (parts/whole)",
        "R": "Relationships (cause/effect)",
        "P": "Perspectives (point/view)",
    }

    if weakest_pattern and lowest_pct < 70:
        return f"Focus on {pattern_names.get(weakest_pattern, weakest_pattern)} - scored {lowest_pct}%. Re-analyze weak concepts with {weakest_pattern} moves."
    elif weak_concepts:
        concepts = list(set(wc["concept"] for wc in weak_concepts[:3]))
        return f"Review these concepts: {', '.join(concepts)}. Export to RemNote for spaced repetition."
    else:
        return "Great job! Continue with spaced repetition in RemNote to maintain retention."


async def get_session_state(session_id: str) -> dict[str, Any]:
    """Get current state of a quiz session."""
    session = quiz_sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}

    current_question = None
    if session["current_index"] < len(session["questions"]):
        current_question = _sanitize_question(session["questions"][session["current_index"]])

    return {
        "session_id": session_id,
        "current_index": session["current_index"],
        "score": session["score"],
        "total": session["total"],
        "answered": len(session["answers"]),
        "completed": session["completed"],
        "current_question": current_question,
        "percentage": round((session["score"] / len(session["answers"])) * 100) if session["answers"] else 0,
    }
