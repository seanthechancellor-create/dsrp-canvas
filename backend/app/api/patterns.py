"""
DSRP Patterns API

Provides endpoints for accessing DSRP framework metadata:
- 4 Patterns (D, S, R, P)
- 6 Moves (is-is-not, zoom-in, zoom-out, part-party, rds-barbell, p-circle)
- 3 Dynamics (equality, co-implication, simultaneity)
"""

from fastapi import APIRouter

from app.models.dsrp import (
    DSRP_PATTERNS,
    DSRP_MOVES,
    DSRP_DYNAMICS,
    PatternInfo,
    MoveInfo,
    DynamicInfo,
    DSRPFrameworkResponse,
    get_pattern_for_move,
    get_pattern_color,
    get_pattern_elements,
)

router = APIRouter()


@router.get("/framework", response_model=DSRPFrameworkResponse)
async def get_dsrp_framework():
    """
    Get the complete DSRP 4-8-3 framework metadata.

    Returns:
        - 4 Patterns with colors, elements, and descriptions
        - 6 Moves with their associated patterns and questions
        - 3 Dynamics with symbols and descriptions
    """
    return DSRPFrameworkResponse(
        patterns={k: PatternInfo(**v) for k, v in DSRP_PATTERNS.items()},
        moves={k: MoveInfo(**v) for k, v in DSRP_MOVES.items()},
        dynamics={k: DynamicInfo(**v) for k, v in DSRP_DYNAMICS.items()},
    )


@router.get("/patterns")
async def get_patterns():
    """Get all DSRP pattern definitions."""
    return list(DSRP_PATTERNS.values())


@router.get("/patterns/{pattern_id}")
async def get_pattern(pattern_id: str):
    """Get a specific pattern's metadata."""
    pattern_id = pattern_id.upper()
    if pattern_id not in DSRP_PATTERNS:
        return {"error": f"Pattern '{pattern_id}' not found. Valid: D, S, R, P"}
    return DSRP_PATTERNS[pattern_id]


@router.get("/moves")
async def get_moves():
    """Get all DSRP moves with their metadata."""
    return list(DSRP_MOVES.values())


@router.get("/moves/{move_id}")
async def get_move(move_id: str):
    """Get a specific move's metadata."""
    if move_id not in DSRP_MOVES:
        return {"error": f"Move '{move_id}' not found", "valid_moves": list(DSRP_MOVES.keys())}
    return DSRP_MOVES[move_id]


@router.get("/dynamics")
async def get_dynamics():
    """Get all DSRP dynamics."""
    return list(DSRP_DYNAMICS.values())


@router.get("/move-pattern/{move_id}")
async def get_move_pattern(move_id: str):
    """Get the pattern associated with a specific move."""
    pattern = get_pattern_for_move(move_id)
    return {
        "move": move_id,
        "pattern": pattern,
        "pattern_info": DSRP_PATTERNS.get(pattern),
    }


@router.get("/elements/{pattern_id}")
async def get_pattern_element_pair(pattern_id: str):
    """Get the element pair for a pattern."""
    pattern_id = pattern_id.upper()
    elements = get_pattern_elements(pattern_id)
    return {
        "pattern": pattern_id,
        "elements": elements,
        "left_element": elements[0] if elements else None,
        "right_element": elements[1] if len(elements) > 1 else None,
    }
