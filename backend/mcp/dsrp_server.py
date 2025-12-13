"""
DSRP Canvas MCP Server

Exposes DSRP analysis capabilities via the Model Context Protocol (MCP).
Uses FastMCP for a Pythonic, decorator-based implementation.

Usage:
    # Run with STDIO (for Claude Desktop)
    fastmcp run backend/mcp/dsrp_server.py

    # Run with SSE (for web)
    fastmcp run backend/mcp/dsrp_server.py --transport sse --port 8001
"""

import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP, Context
from typing import Optional
import json

# Initialize MCP server
mcp = FastMCP(
    "DSRP Canvas",
    description="Knowledge analysis using Dr. Derek Cabrera's DSRP 4-8-3 systems thinking framework",
)

# =============================================================================
# DSRP Analysis Tools
# =============================================================================


@mcp.tool()
async def analyze_concept(
    concept: str,
    move: str,
    context: Optional[str] = None,
) -> dict:
    """
    Analyze a concept using one of the 6 DSRP moves.

    Args:
        concept: The concept to analyze (e.g., "Democracy", "Machine Learning")
        move: One of the 6 DSRP moves:
            - is-is-not: Define what it IS and IS NOT (Distinctions)
            - zoom-in: Examine the parts that make it up (Systems)
            - zoom-out: Examine the larger system it belongs to (Systems)
            - part-party: Break into parts and show their relationships (Systems)
            - rds-barbell: Relate, Distinguish, Systematize (Relationships)
            - p-circle: Map multiple perspectives (Perspectives)
        context: Optional additional context about the concept

    Returns:
        Analysis result with pattern, elements, and reasoning
    """
    from agents.dsrp_agent import DSRPAgent

    valid_moves = ["is-is-not", "zoom-in", "zoom-out", "part-party", "rds-barbell", "p-circle"]
    if move not in valid_moves:
        return {"error": f"Invalid move. Must be one of: {valid_moves}"}

    agent = DSRPAgent()
    result = await agent.analyze(concept, move, context)
    return result


@mcp.tool()
async def explain_dsrp_framework() -> dict:
    """
    Explain the DSRP 4-8-3 systems thinking framework.

    Returns a comprehensive explanation of:
    - The 4 Patterns (D, S, R, P)
    - The 8 Elements (2 per pattern)
    - The 3 Dynamics
    - The 6 Moves for analysis
    """
    return {
        "framework": "DSRP 4-8-3",
        "author": "Dr. Derek Cabrera, Cornell University",
        "patterns": {
            "D": {
                "name": "Distinctions",
                "elements": ["identity", "other"],
                "description": "Define what something IS and IS NOT",
            },
            "S": {
                "name": "Systems",
                "elements": ["part", "whole"],
                "description": "Understand components and containers",
            },
            "R": {
                "name": "Relationships",
                "elements": ["action", "reaction"],
                "description": "Connections between things",
            },
            "P": {
                "name": "Perspectives",
                "elements": ["point", "view"],
                "description": "Different viewpoints on the same thing",
            },
        },
        "dynamics": {
            "equality": "Each pattern equals its two co-implying elements (D = i ⇔ o)",
            "coimplication": "If one element exists, the other exists",
            "simultaneity": "Any element exists simultaneously as any of the other 7",
        },
        "moves": {
            "is-is-not": "Define boundaries using Distinctions",
            "zoom-in": "Examine parts using Systems",
            "zoom-out": "Examine whole/context using Systems",
            "part-party": "Map parts and their relationships",
            "rds-barbell": "Relate → Distinguish → Systematize",
            "p-circle": "Map multiple perspectives",
        },
    }


# =============================================================================
# Knowledge Graph Tools
# =============================================================================


@mcp.tool()
async def create_concept(
    name: str,
    description: Optional[str] = None,
) -> dict:
    """
    Create a new concept in the knowledge graph.

    Args:
        name: Name of the concept
        description: Optional description

    Returns:
        The created concept with its ID
    """
    from app.services.typedb_service import get_typedb_service
    import uuid

    service = get_typedb_service()
    concept_id = str(uuid.uuid4())

    try:
        result = await service.create_concept(concept_id, name, description)
        return {"success": True, "concept": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_concepts(query: str, limit: int = 10) -> list:
    """
    Search for concepts in the knowledge graph.

    Args:
        query: Search query (matches concept names)
        limit: Maximum number of results (default: 10)

    Returns:
        List of matching concepts
    """
    from app.services.typedb_service import get_typedb_service

    service = get_typedb_service()

    try:
        concepts = await service.list_concepts(limit=limit)
        # Filter by query (case-insensitive)
        query_lower = query.lower()
        matches = [c for c in concepts if query_lower in c.get("name", "").lower()]
        return matches
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_concept_analysis(concept_name: str) -> dict:
    """
    Get all DSRP analyses for a concept.

    Args:
        concept_name: Name of the concept to look up

    Returns:
        Concept details with all associated analyses
    """
    from app.services.typedb_service import get_typedb_service

    service = get_typedb_service()

    try:
        concept = await service.get_concept_by_name(concept_name)
        if not concept:
            return {"error": f"Concept '{concept_name}' not found"}

        analyses = await service.get_analyses_for_concept(concept["id"])
        relations = await service.get_concept_relations(concept["id"])

        return {
            "concept": concept,
            "analyses": analyses,
            "relations": relations,
        }
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Export Tools
# =============================================================================


@mcp.tool()
async def export_to_markdown(concept_ids: Optional[list] = None) -> str:
    """
    Export knowledge graph to Markdown format.

    Args:
        concept_ids: Optional list of specific concept IDs to export.
                    If not provided, exports all concepts.

    Returns:
        Markdown string with all concepts and analyses
    """
    from app.services.typedb_service import get_typedb_service

    service = get_typedb_service()

    try:
        if concept_ids:
            concepts = []
            for cid in concept_ids:
                c = await service.get_concept(cid)
                if c:
                    concepts.append(c)
        else:
            concepts = await service.list_concepts(limit=100)

        # Build markdown
        lines = ["# DSRP Knowledge Export\n"]

        for concept in concepts:
            lines.append(f"## {concept.get('name', 'Unknown')}\n")

            if concept.get("description"):
                lines.append(f"{concept['description']}\n")

            # Get analyses
            analyses = await service.get_analyses_for_concept(concept["id"])
            if analyses:
                lines.append("### Analyses\n")
                for a in analyses:
                    lines.append(f"**{a.get('move', 'Unknown')}** ({a.get('pattern', '')})")
                    lines.append(f"- {a.get('reasoning', '')}\n")

            lines.append("---\n")

        return "\n".join(lines)
    except Exception as e:
        return f"Export failed: {str(e)}"


@mcp.tool()
async def export_to_obsidian(concept_ids: Optional[list] = None) -> str:
    """
    Export knowledge graph to Obsidian-compatible Markdown with [[wikilinks]].

    Args:
        concept_ids: Optional list of specific concept IDs to export

    Returns:
        Markdown string with Obsidian wikilinks
    """
    from app.services.typedb_service import get_typedb_service

    service = get_typedb_service()

    try:
        if concept_ids:
            concepts = []
            for cid in concept_ids:
                c = await service.get_concept(cid)
                if c:
                    concepts.append(c)
        else:
            concepts = await service.list_concepts(limit=100)

        lines = ["# DSRP Knowledge Graph\n"]
        lines.append("Created with DSRP Canvas\n")

        for concept in concepts:
            name = concept.get("name", "Unknown")
            lines.append(f"## [[{name}]]\n")

            # Get relations and create wikilinks
            relations = await service.get_concept_relations(concept["id"])

            if relations.get("systems"):
                lines.append("### Parts")
                for s in relations["systems"]:
                    part_name = s.get("part_name", "")
                    lines.append(f"- [[{part_name}]]")
                lines.append("")

            if relations.get("relationships"):
                lines.append("### Related To")
                for r in relations["relationships"]:
                    reaction_name = r.get("reaction_name", "")
                    lines.append(f"- [[{reaction_name}]]")
                lines.append("")

            if relations.get("distinctions"):
                lines.append("### Distinguished From")
                for d in relations["distinctions"]:
                    other_name = d.get("other_name", "")
                    lines.append(f"- [[{other_name}]]")
                lines.append("")

            lines.append("---\n")

        return "\n".join(lines)
    except Exception as e:
        return f"Export failed: {str(e)}"


# =============================================================================
# Resources (Read-only data access)
# =============================================================================


@mcp.resource("dsrp://concepts")
async def list_all_concepts() -> str:
    """List all concepts in the knowledge graph."""
    from app.services.typedb_service import get_typedb_service

    service = get_typedb_service()

    try:
        concepts = await service.list_concepts(limit=100)
        return json.dumps(concepts, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("dsrp://concepts/{concept_id}")
async def get_concept_resource(concept_id: str) -> str:
    """Get a specific concept by ID."""
    from app.services.typedb_service import get_typedb_service

    service = get_typedb_service()

    try:
        concept = await service.get_concept(concept_id)
        if not concept:
            return json.dumps({"error": "Concept not found"})

        analyses = await service.get_analyses_for_concept(concept_id)
        relations = await service.get_concept_relations(concept_id)

        return json.dumps(
            {"concept": concept, "analyses": analyses, "relations": relations},
            indent=2,
            default=str,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("dsrp://sources")
async def list_all_sources() -> str:
    """List all ingested sources."""
    from app.services.typedb_service import get_typedb_service

    service = get_typedb_service()

    try:
        sources = await service.list_sources(limit=100)
        return json.dumps(sources, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# Prompts (Reusable prompt templates)
# =============================================================================


@mcp.prompt()
def dsrp_analysis_prompt(concept: str, pattern: str = "D") -> str:
    """
    Generate a DSRP analysis prompt for a concept.

    Args:
        concept: The concept to analyze
        pattern: DSRP pattern (D, S, R, or P)
    """
    prompts = {
        "D": f"""Apply Distinctions to analyze "{concept}":

1. What IS {concept}? (identity)
2. What is {concept} NOT? (other)
3. What is the boundary between identity and other?

Think carefully about the defining characteristics that make {concept} what it is,
and contrast with similar but distinct concepts.""",
        "S": f"""Apply Systems thinking to analyze "{concept}":

1. What PARTS make up {concept}? (zoom in)
2. What larger WHOLE is {concept} part of? (zoom out)
3. How do the parts relate to each other? (part party)

Consider both the internal structure and external context.""",
        "R": f"""Apply Relationships to analyze "{concept}":

1. What does {concept} RELATE to?
2. What are the ACTION/REACTION dynamics?
3. Use RDS: Relate → Distinguish → Systematize

Map the network of connections and influences.""",
        "P": f"""Apply Perspectives to analyze "{concept}":

1. Who are the different OBSERVERS (points)?
2. What does each observer SEE (views)?
3. How do perspectives differ and complement?

Consider stakeholders, disciplines, and worldviews.""",
    }
    return prompts.get(pattern, prompts["D"])


@mcp.prompt()
def six_moves_prompt(concept: str) -> str:
    """
    Generate a comprehensive 6-moves analysis prompt.

    Args:
        concept: The concept to analyze with all 6 moves
    """
    return f"""Perform a comprehensive DSRP analysis of "{concept}" using all 6 moves:

## 1. Is/Is Not (Distinctions)
What IS {concept}? What is it NOT?

## 2. Zoom In (Systems)
What PARTS make up {concept}?

## 3. Zoom Out (Systems)
What larger WHOLE contains {concept}?

## 4. Part Party (Systems)
How do the parts of {concept} relate to each other?

## 5. RDS Barbell (Relationships)
- RELATE: What connects to {concept}?
- DISTINGUISH: What makes each relationship unique?
- SYSTEMATIZE: What system emerges?

## 6. P-Circle (Perspectives)
Who sees {concept} differently and how?

Provide structured analysis for each move."""


# =============================================================================
# Server Entry Point
# =============================================================================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
