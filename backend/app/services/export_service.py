"""
Export service for converting knowledge graph to various formats.
Supports Markdown, Obsidian, and RemNote exports.
"""

import logging
from typing import Any

from app.services.typedb_service import get_typedb_service

logger = logging.getLogger(__name__)

# Fallback in-memory stores (used when TypeDB unavailable)
# Import from concepts API to share the same store
def _get_concepts_db():
    """Get the shared concepts db from the concepts API module."""
    try:
        from app.api.concepts import concepts_db
        return concepts_db
    except ImportError:
        return {}

analyses_db: dict[str, list[dict]] = {}


async def export_to_markdown(
    concept_ids: list[str],
    include_analyses: bool = True,
    include_relationships: bool = True,
) -> str:
    """Export concepts to plain Markdown format."""
    lines = ["# DSRP Knowledge Export\n"]
    typedb = get_typedb_service()

    for concept_id in concept_ids:
        # Try TypeDB first
        concept = None
        analyses = []

        try:
            concept = await typedb.get_concept(concept_id)
            if include_analyses:
                analyses = await typedb.get_analyses_for_concept(concept_id)
        except Exception as e:
            logger.debug(f"TypeDB lookup failed: {e}")

        # Fallback to in-memory
        if not concept:
            concept = _get_concepts_db().get(concept_id, {"name": "Unknown", "description": ""})
        if not analyses and include_analyses:
            analyses = analyses_db.get(concept_id, [])

        lines.append(f"## {concept.get('name', 'Unnamed')}\n")

        if concept.get("description"):
            lines.append(f"{concept['description']}\n")

        if include_analyses and analyses:
            lines.append("### DSRP Analysis\n")
            for analysis in analyses:
                lines.append(format_analysis_markdown(analysis))

        lines.append("---\n")

    return "\n".join(lines)


async def export_to_obsidian(
    concept_ids: list[str],
    include_analyses: bool = True,
    include_relationships: bool = True,
) -> str:
    """Export to Obsidian-compatible Markdown with wikilinks."""
    lines = ["# DSRP Knowledge Export\n"]
    lines.append("Tags: #dsrp #systems-thinking #knowledge-graph\n")
    typedb = get_typedb_service()

    for concept_id in concept_ids:
        # Try TypeDB first
        concept = None
        analyses = []
        relations = None

        try:
            concept = await typedb.get_concept(concept_id)
            if include_analyses:
                analyses = await typedb.get_analyses_for_concept(concept_id)
            if include_relationships:
                relations = await typedb.get_concept_relations(concept_id)
        except Exception as e:
            logger.debug(f"TypeDB lookup failed: {e}")

        # Fallback to in-memory
        if not concept:
            concept = _get_concepts_db().get(concept_id, {"name": "Unknown", "description": ""})
        if not analyses and include_analyses:
            analyses = analyses_db.get(concept_id, [])

        name = concept.get("name", "Unnamed")
        lines.append(f"## [[{name}]]\n")

        if concept.get("description"):
            lines.append(f"{concept['description']}\n")

        if include_analyses and analyses:
            lines.append("### DSRP Analysis\n")
            for analysis in analyses:
                lines.append(format_analysis_obsidian(analysis))

        if include_relationships:
            lines.append("### Connections\n")
            if relations:
                # Add actual relationships from TypeDB
                related_names = []
                for sys in relations.get("systems", []):
                    if sys.get("part_name"):
                        related_names.append(sys["part_name"])
                for rel in relations.get("relationships", []):
                    if rel.get("reaction_name"):
                        related_names.append(rel["reaction_name"])
                for dist in relations.get("distinctions", []):
                    if dist.get("other_name"):
                        related_names.append(dist["other_name"])
                for persp in relations.get("perspectives", []):
                    if persp.get("view_name"):
                        related_names.append(persp["view_name"])

                if related_names:
                    wikilinks = ", ".join([f"[[{n}]]" for n in related_names[:10]])
                    lines.append(f"- Related: {wikilinks}\n")
                else:
                    lines.append("- No connections yet\n")
            else:
                lines.append("- No connections yet\n")

        lines.append("---\n")

    return "\n".join(lines)


async def export_to_remnote(
    concept_ids: list[str],
    include_analyses: bool = True,
) -> list[dict[str, Any]]:
    """
    Export to RemNote flashcard format.
    Creates spaced repetition cards from DSRP analyses.
    """
    cards = []
    typedb = get_typedb_service()

    for concept_id in concept_ids:
        # Try TypeDB first
        concept = None
        analyses = []

        try:
            concept = await typedb.get_concept(concept_id)
            analyses = await typedb.get_analyses_for_concept(concept_id)
        except Exception as e:
            logger.debug(f"TypeDB lookup failed: {e}")

        # Fallback to in-memory
        if not concept:
            concept = _get_concepts_db().get(concept_id, {"name": "Unknown"})
        if not analyses:
            analyses = analyses_db.get(concept_id, [])

        name = concept.get("name", "Unnamed")

        for analysis in analyses:
            # Create cards based on the move type
            move = analysis.get("move", "")

            if move == "is-is-not":
                cards.append({
                    "front": f"What IS {name}?",
                    "back": analysis.get("elements", {}).get("identity", ""),
                    "tags": ["dsrp", "distinctions", name],
                })
                cards.append({
                    "front": f"What is {name} NOT?",
                    "back": analysis.get("elements", {}).get("other", ""),
                    "tags": ["dsrp", "distinctions", name],
                })

            elif move == "zoom-in":
                cards.append({
                    "front": f"What are the parts of {name}?",
                    "back": analysis.get("elements", {}).get("parts", ""),
                    "tags": ["dsrp", "systems", name],
                })

            elif move == "zoom-out":
                cards.append({
                    "front": f"What larger system does {name} belong to?",
                    "back": analysis.get("elements", {}).get("whole", ""),
                    "tags": ["dsrp", "systems", name],
                })

            elif move == "part-party":
                cards.append({
                    "front": f"How do the parts of {name} relate to each other?",
                    "back": analysis.get("reasoning", ""),
                    "tags": ["dsrp", "systems", name],
                })

            elif move == "rds-barbell":
                cards.append({
                    "front": f"What relationships does {name} have?",
                    "back": analysis.get("elements", {}).get("relationships", ""),
                    "tags": ["dsrp", "relationships", name],
                })

            elif move == "p-circle":
                cards.append({
                    "front": f"What are different perspectives on {name}?",
                    "back": analysis.get("elements", {}).get("perspectives", ""),
                    "tags": ["dsrp", "perspectives", name],
                })

    return cards


def format_analysis_markdown(analysis: dict) -> str:
    """Format a single analysis for plain Markdown."""
    move = analysis.get("move", "unknown")
    pattern = analysis.get("pattern", "")
    reasoning = analysis.get("reasoning", "")

    return f"""
#### {move.replace("-", " ").title()} ({pattern})

{reasoning}

"""


def format_analysis_obsidian(analysis: dict) -> str:
    """Format a single analysis for Obsidian with tags."""
    move = analysis.get("move", "unknown")
    pattern = analysis.get("pattern", "")
    reasoning = analysis.get("reasoning", "")

    return f"""
#### {move.replace("-", " ").title()} #{pattern.lower()}

{reasoning}

"""
