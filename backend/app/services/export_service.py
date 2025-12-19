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
    Export to RemNote flashcard format using Concept Descriptor framework.
    Creates spaced repetition cards from DSRP 4-8-3 analyses.
    Uses :: notation for automatic flashcard creation in RemNote.
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
            # Create cards based on the move type using DSRP 4-8-3
            move = analysis.get("move", "")
            elements = analysis.get("elements", {})
            pattern = analysis.get("pattern", "")
            reasoning = analysis.get("reasoning", "")

            # D - Distinctions (identity/other)
            if move == "is-is-not":
                identity = elements.get("identity", "")
                other = elements.get("other", "")
                cards.append({
                    "remnote_format": f"{name}\n  Pattern:: D (Distinction)\n  Identity:: {identity}\n  Other:: {other}\n  Boundary:: {elements.get('boundary', '')}\n  #DSRP #Distinction",
                    "front": f"[D] What IS {name}? (Identity)",
                    "back": identity,
                    "tags": ["DSRP", "D-Distinction", "identity", name],
                })
                cards.append({
                    "remnote_format": f"What is {name} NOT?\n  Answer:: {other}\n  #DSRP #Distinction",
                    "front": f"[D] What is {name} NOT? (Other)",
                    "back": other,
                    "tags": ["DSRP", "D-Distinction", "other", name],
                })

            # S - Systems (part/whole)
            elif move == "zoom-in":
                parts = elements.get("parts", [])
                parts_str = ", ".join(parts) if isinstance(parts, list) else str(parts)
                cards.append({
                    "remnote_format": f"{name} (Parts)\n  Pattern:: S (System)\n  Parts:: {parts_str}\n  #DSRP #System #ZoomIn",
                    "front": f"[S] What are the parts of {name}? (Zoom In)",
                    "back": parts_str,
                    "tags": ["DSRP", "S-System", "parts", "zoom-in", name],
                })

            elif move == "zoom-out":
                whole = elements.get("whole", "")
                cards.append({
                    "remnote_format": f"{name} (Context)\n  Pattern:: S (System)\n  Part of:: {whole}\n  #DSRP #System #ZoomOut",
                    "front": f"[S] What larger system/whole contains {name}? (Zoom Out)",
                    "back": whole,
                    "tags": ["DSRP", "S-System", "whole", "zoom-out", name],
                })

            elif move == "part-party":
                parts = elements.get("parts", [])
                parts_str = ", ".join(parts) if isinstance(parts, list) else str(parts)
                cards.append({
                    "remnote_format": f"{name} (Part-Party)\n  Pattern:: S (System)\n  Parts:: {parts_str}\n  Part Relations:: {reasoning}\n  #DSRP #System #PartParty",
                    "front": f"[S] How do the parts of {name} relate to each other? (Part-Party)",
                    "back": reasoning,
                    "tags": ["DSRP", "S-System", "part-party", name],
                })

            # R - Relationships (action/reaction)
            elif move == "rds-barbell":
                reactions = elements.get("reactions", [])
                reactions_str = ", ".join(reactions) if isinstance(reactions, list) else str(reactions)
                cards.append({
                    "remnote_format": f"{name} (Relationships)\n  Pattern:: R (Relationship)\n  Action:: {name}\n  Reactions:: {reactions_str}\n  #DSRP #Relationship #RDSBarbell",
                    "front": f"[R] What are the relationships/reactions of {name}? (RDS Barbell)",
                    "back": reactions_str,
                    "tags": ["DSRP", "R-Relationship", "rds-barbell", name],
                })

            # R - Web of Causality (forward effects)
            elif move == "woc":
                effects = elements.get("effects", [])
                effects_list = []
                for eff in effects if isinstance(effects, list) else []:
                    if isinstance(eff, dict):
                        effects_list.append(f"{eff.get('effect', '')} (Level {eff.get('level', 1)})")
                    else:
                        effects_list.append(str(eff))
                effects_str = ", ".join(effects_list) if effects_list else str(effects)
                cards.append({
                    "remnote_format": f"{name} (Web of Causality)\n  Pattern:: R (Relationship)\n  Cause:: {name}\n  Effects:: {effects_str}\n  #DSRP #Relationship #WoC #Causality",
                    "front": f"[R] What effects does {name} cause? (Web of Causality)",
                    "back": effects_str,
                    "tags": ["DSRP", "R-Relationship", "woc", "causality", name],
                })

            # R - Web of Anticausality (root causes)
            elif move == "waoc":
                causes = elements.get("causes", [])
                causes_list = []
                for c in causes if isinstance(causes, list) else []:
                    if isinstance(c, dict):
                        causes_list.append(f"{c.get('cause', '')} (Level {c.get('level', 1)})")
                    else:
                        causes_list.append(str(c))
                causes_str = ", ".join(causes_list) if causes_list else str(causes)
                cards.append({
                    "remnote_format": f"{name} (Root Causes)\n  Pattern:: R (Relationship)\n  Effect:: {name}\n  Root Causes:: {causes_str}\n  #DSRP #Relationship #WAoC #RootCause",
                    "front": f"[R] What are the root causes of {name}? (Web of Anticausality)",
                    "back": causes_str,
                    "tags": ["DSRP", "R-Relationship", "waoc", "root-cause", name],
                })

            # P - Perspectives (point/view)
            elif move == "p-circle":
                perspectives = elements.get("perspectives", [])
                persp_list = []
                for p in perspectives if isinstance(perspectives, list) else []:
                    if isinstance(p, dict):
                        persp_list.append(f"{p.get('point', '')}: {p.get('view', '')}")
                    else:
                        persp_list.append(str(p))
                persp_str = "; ".join(persp_list) if persp_list else str(perspectives)
                cards.append({
                    "remnote_format": f"{name} (Perspectives)\n  Pattern:: P (Perspective)\n  Perspectives:: {persp_str}\n  #DSRP #Perspective #PCircle",
                    "front": f"[P] What are different perspectives on {name}? (P-Circle)",
                    "back": persp_str,
                    "tags": ["DSRP", "P-Perspective", "p-circle", name],
                })

    return cards


async def export_to_remnote_markdown(
    concept_ids: list[str],
    include_analyses: bool = True,
) -> str:
    """
    Export to RemNote-compatible Markdown with :: notation for SRS.
    This can be directly imported into RemNote for spaced repetition study.
    Uses DSRP 4-8-3 Concept Descriptor framework.
    """
    cards = await export_to_remnote(concept_ids, include_analyses)

    lines = [
        "# DSRP 4-8-3 Knowledge Export",
        "## For RemNote Spaced Repetition Study",
        "",
        "**4 Patterns**: D (Distinctions), S (Systems), R (Relationships), P (Perspectives)",
        "**8 Elements**: identity/other, part/whole, action/reaction, point/view",
        "**3 Dynamics**: Equality (=), Co-implication (⇔), Simultaneity (✷)",
        "",
        "---",
        ""
    ]

    for card in cards:
        if card.get("remnote_format"):
            lines.append(card["remnote_format"])
            lines.append("")

    return "\n".join(lines)


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
