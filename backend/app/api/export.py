from fastapi import APIRouter
from pydantic import BaseModel

from app.services.export_service import (
    export_to_markdown,
    export_to_remnote,
    export_to_remnote_markdown,
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
    Creates flashcard-style Q&A pairs from DSRP 4-8-3 analyses.
    Uses :: notation for Concept Descriptor framework.
    """
    cards = await export_to_remnote(
        concept_ids=request.concept_ids,
        include_analyses=request.include_analyses,
    )
    return {"cards": cards, "count": len(cards)}


@router.post("/remnote-markdown")
async def export_remnote_md(request: ExportRequest):
    """
    Export to RemNote-compatible Markdown file with :: notation.
    Ready for direct import into RemNote for SRS study.
    Structured using DSRP 4-8-3 Concept Descriptor framework.

    Perfect for exam prep like IAPP CIPP certification.
    """
    content = await export_to_remnote_markdown(
        concept_ids=request.concept_ids,
        include_analyses=request.include_analyses,
    )
    return {"content": content}
