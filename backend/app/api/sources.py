import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.ingestion import process_file, get_extracted_concepts
from app.services.typedb_service import get_typedb_service
from app.models.source import Source, SourceStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for tracking processing status (TypeDB stores persistent data)
# This tracks active uploads/processing; completed sources are in TypeDB
sources_db: dict[str, Source] = {}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class UploadResponse(BaseModel):
    source_id: str
    file_path: str
    status: str


class StatusResponse(BaseModel):
    source_id: str
    status: str
    extracted_text: str | None = None
    error: str | None = None


@router.post("/upload", response_model=UploadResponse)
async def upload_source(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload a PDF, audio, or video file for processing."""
    source_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{source_id}_{file.filename}"

    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    source_type = get_source_type(file.filename)

    # Create source record in TypeDB
    typedb = get_typedb_service()
    try:
        await typedb.create_source(
            source_id=source_id,
            source_type=source_type,
            file_path=str(file_path),
            original_filename=file.filename,
        )
    except Exception as e:
        logger.warning(f"TypeDB not available, using in-memory store: {e}")

    # Also track in memory for status updates during processing
    source = Source(
        id=source_id,
        filename=file.filename,
        file_path=str(file_path),
        source_type=source_type,
        status=SourceStatus.PROCESSING,
    )
    sources_db[source_id] = source

    # Process in background
    background_tasks.add_task(process_file, source_id, sources_db)

    return UploadResponse(
        source_id=source_id,
        file_path=str(file_path),
        status="processing",
    )


@router.get("/{source_id}/status", response_model=StatusResponse)
async def get_source_status(source_id: str):
    """Get the processing status of a source."""
    # First check in-memory for active processing
    if source_id in sources_db:
        source = sources_db[source_id]
        return StatusResponse(
            source_id=source_id,
            status=source.status.value,
            extracted_text=source.extracted_text,
            error=source.error,
        )

    # Check TypeDB for completed sources
    typedb = get_typedb_service()
    try:
        db_source = await typedb.get_source(source_id)
        if db_source:
            extracted_text = await typedb.get_source_text(source_id)
            return StatusResponse(
                source_id=source_id,
                status="ready" if extracted_text else "processing",
                extracted_text=extracted_text,
                error=None,
            )
    except Exception as e:
        logger.debug(f"TypeDB lookup failed: {e}")

    raise HTTPException(status_code=404, detail="Source not found")


@router.get("/")
async def list_sources():
    """List all sources."""
    # Merge in-memory (processing) and TypeDB (completed) sources
    all_sources = []

    # Add in-memory sources (currently processing)
    for source in sources_db.values():
        all_sources.append({
            "id": source.id,
            "filename": source.filename,
            "source_type": source.source_type,
            "status": source.status.value,
        })

    # Add TypeDB sources
    typedb = get_typedb_service()
    try:
        db_sources = await typedb.list_sources()
        seen_ids = {s["id"] for s in all_sources}
        for db_source in db_sources:
            if db_source.get("id") not in seen_ids:
                all_sources.append({
                    "id": db_source.get("id"),
                    "filename": db_source.get("original_filename"),
                    "source_type": db_source.get("source_type"),
                    "status": "ready",
                })
    except Exception as e:
        logger.debug(f"TypeDB list failed: {e}")

    return all_sources


@router.get("/{source_id}/concepts")
async def get_source_concepts(source_id: str):
    """Get extracted concepts from a processed source."""
    concepts = get_extracted_concepts(source_id)
    if concepts is None:
        # Check if source exists but concepts not ready
        if source_id in sources_db:
            source = sources_db[source_id]
            if source.status == SourceStatus.PROCESSING:
                return {"status": "processing", "concepts": []}
            elif source.status == SourceStatus.ERROR:
                raise HTTPException(status_code=500, detail=f"Source processing failed: {source.error}")
        raise HTTPException(status_code=404, detail="Concepts not found for this source")

    return {
        "status": "ready",
        "source_id": source_id,
        "source_summary": concepts.get("source_summary", ""),
        "main_theme": concepts.get("main_theme", ""),
        "concepts": concepts.get("concepts", []),
        "provider": concepts.get("provider", ""),
    }


def get_source_type(filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    if ext == "pdf":
        return "pdf"
    if ext in ["mp3", "wav", "ogg", "m4a"]:
        return "audio"
    if ext in ["mp4", "webm", "mov", "avi"]:
        return "video"
    return "unknown"
