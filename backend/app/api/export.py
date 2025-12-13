from fastapi import APIRouter
from pydantic import BaseModel

from app.services.export_service import (
    export_to_markdown,
    export_to_remnote,
    export_to_obsidian,
)

router = APIRouter()


class ExportRequest(BaseModel):
    concept_ids: list[str]
    include_analyses: bool = True
    include_relationships: bool = True


@router.post("/markdown")
async def export_markdown(request: ExportRequest):
    """Export selected concepts to plain Markdown."""
    content = await export_to_markdown(
        concept_ids=request.concept_ids,
        include_analyses=request.include_analyses,
        include_relationships=request.include_relationships,
    )
    return {"content": content}


@router.post("/obsidian")
async def export_obsidian(request: ExportRequest):
    """
    Export to Obsidian-compatible Markdown with wikilinks.
    Uses [[concept]] syntax for internal links.
    """
    content = await export_to_obsidian(
        concept_ids=request.concept_ids,
        include_analyses=request.include_analyses,
        include_relationships=request.include_relationships,
    )
    return {"content": content}


@router.post("/remnote")
async def export_remnote(request: ExportRequest):
    """
    Export to RemNote format for spaced repetition.
    Creates flashcard-style Q&A pairs from DSRP analyses.
    """
    cards = await export_to_remnote(
        concept_ids=request.concept_ids,
        include_analyses=request.include_analyses,
    )
    return {"cards": cards, "count": len(cards)}
