"""
DSRP Framework Models and Constants

Defines the 4-8-3 framework:
- 4 Patterns: D, S, R, P
- 8 Elements: identity/other, part/whole, action/reaction, point/view
- 3 Dynamics: equality, co-implication, simultaneity
"""

from pydantic import BaseModel
from enum import Enum


class DSRPPattern(str, Enum):
    """The 4 DSRP patterns."""
    D = "D"  # Distinctions
    S = "S"  # Systems
    R = "R"  # Relationships
    P = "P"  # Perspectives


class DSRPMove(str, Enum):
    """The 6 DSRP moves."""
    IS_IS_NOT = "is-is-not"
    ZOOM_IN = "zoom-in"
    ZOOM_OUT = "zoom-out"
    PART_PARTY = "part-party"
    RDS_BARBELL = "rds-barbell"
    P_CIRCLE = "p-circle"


class DSRPDynamic(str, Enum):
    """The 3 DSRP dynamics."""
    EQUALITY = "="
    CO_IMPLICATION = "co-implication"
    SIMULTANEITY = "simultaneity"


# Pattern metadata with colors matching frontend
DSRP_PATTERNS = {
    "D": {
        "id": "D",
        "name": "Distinctions",
        "elements": ["identity", "other"],
        "description": "Defining what something IS and IS NOT",
        "color": "#1976D2",
        "icon": "split",
    },
    "S": {
        "id": "S",
        "name": "Systems",
        "elements": ["part", "whole"],
        "description": "Understanding components and containers",
        "color": "#388E3C",
        "icon": "nested",
    },
    "R": {
        "id": "R",
        "name": "Relationships",
        "elements": ["action", "reaction"],
        "description": "Connections between things",
        "color": "#F57C00",
        "icon": "link",
    },
    "P": {
        "id": "P",
        "name": "Perspectives",
        "elements": ["point", "view"],
        "description": "Different viewpoints on the same thing",
        "color": "#7B1FA2",
        "icon": "eye",
    },
}

# Move metadata
DSRP_MOVES = {
    "is-is-not": {
        "id": "is-is-not",
        "name": "Is/Is Not",
        "pattern": "D",
        "description": "Define what it IS and IS NOT",
        "question": "What makes this distinct from everything else?",
    },
    "zoom-in": {
        "id": "zoom-in",
        "name": "Zoom In",
        "pattern": "S",
        "description": "Examine the parts",
        "question": "What components make up this concept?",
    },
    "zoom-out": {
        "id": "zoom-out",
        "name": "Zoom Out",
        "pattern": "S",
        "description": "Examine the whole",
        "question": "What larger system contains this?",
    },
    "part-party": {
        "id": "part-party",
        "name": "Part Party",
        "pattern": "S",
        "description": "Parts + relationships",
        "question": "How do the parts relate to each other?",
    },
    "rds-barbell": {
        "id": "rds-barbell",
        "name": "RDS Barbell",
        "pattern": "R",
        "description": "Relate, Distinguish, Systematize",
        "question": "What relationships emerge and what systems do they form?",
    },
    "p-circle": {
        "id": "p-circle",
        "name": "P-Circle",
        "pattern": "P",
        "description": "Map perspectives",
        "question": "Who sees this differently and what do they see?",
    },
}

# Dynamic metadata
DSRP_DYNAMICS = {
    "=": {
        "symbol": "=",
        "name": "Equality",
        "description": "Each pattern equals its two co-implying elements",
    },
    "co-implication": {
        "symbol": "⇔",
        "name": "Co-implication",
        "description": "If one element exists, the other must exist",
    },
    "simultaneity": {
        "symbol": "✷",
        "name": "Simultaneity",
        "description": "Any element exists simultaneously as any of the other 7 elements",
    },
}


class PatternInfo(BaseModel):
    """Pattern metadata response model."""
    id: str
    name: str
    elements: list[str]
    description: str
    color: str
    icon: str


class MoveInfo(BaseModel):
    """Move metadata response model."""
    id: str
    name: str
    pattern: str
    description: str
    question: str


class DynamicInfo(BaseModel):
    """Dynamic metadata response model."""
    symbol: str
    name: str
    description: str


class DSRPFrameworkResponse(BaseModel):
    """Complete DSRP framework metadata."""
    patterns: dict[str, PatternInfo]
    moves: dict[str, MoveInfo]
    dynamics: dict[str, DynamicInfo]


def get_pattern_for_move(move: str) -> str:
    """Get the pattern type for a given move."""
    return DSRP_MOVES.get(move, {}).get("pattern", "D")


def get_pattern_color(pattern: str) -> str:
    """Get the color for a pattern."""
    return DSRP_PATTERNS.get(pattern, {}).get("color", "#1976D2")


def get_pattern_elements(pattern: str) -> list[str]:
    """Get the element pair for a pattern."""
    return DSRP_PATTERNS.get(pattern, {}).get("elements", ["identity", "other"])
