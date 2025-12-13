"""
File ingestion service for PDFs, audio, and video.
Extracts text content and concepts for DSRP analysis.
"""

import logging
from pathlib import Path

from app.models.source import Source, SourceStatus
from app.services.typedb_service import get_typedb_service

logger = logging.getLogger(__name__)

# Store extracted concepts per source (in-memory cache)
extracted_concepts_db: dict[str, dict] = {}


async def process_file(source_id: str, sources_db: dict[str, Source]):
    """Process an uploaded file, extract text content, and identify concepts."""
    source = sources_db.get(source_id)
    if not source:
        return

    try:
        file_path = Path(source.file_path)

        if source.source_type == "pdf":
            text = await extract_pdf_text(file_path)
        elif source.source_type == "audio":
            text = await transcribe_audio(file_path)
        elif source.source_type == "video":
            text = await transcribe_video(file_path)
        else:
            raise ValueError(f"Unsupported file type: {source.source_type}")

        source.extracted_text = text
        source.status = SourceStatus.READY

        # Persist extracted text to TypeDB
        typedb = get_typedb_service()
        try:
            await typedb.update_source_text(source_id, text)
            logger.info(f"Saved extracted text to TypeDB for source {source_id}")
        except Exception as e:
            logger.warning(f"Failed to save to TypeDB (using in-memory): {e}")

        # Extract concepts from the text using AI
        if text and len(text) > 100:
            try:
                concepts_result = await extract_concepts(text, source.filename)
                extracted_concepts_db[source_id] = concepts_result
                logger.info(f"Extracted {len(concepts_result.get('concepts', []))} concepts from {source.filename}")
            except Exception as e:
                logger.warning(f"Failed to extract concepts: {e}")
                extracted_concepts_db[source_id] = {"concepts": [], "error": str(e)}

    except Exception as e:
        source.status = SourceStatus.ERROR
        source.error = str(e)


async def extract_concepts(text: str, source_name: str | None = None) -> dict:
    """Extract key concepts from text using DSRP agent."""
    from agents.dsrp_agent import DSRPAgent

    agent = DSRPAgent()
    result = await agent.extract_concepts_from_text(
        text=text,
        max_concepts=20,
        source_name=source_name,
    )
    return result


def get_extracted_concepts(source_id: str) -> dict | None:
    """Get extracted concepts for a source."""
    return extracted_concepts_db.get(source_id)


async def extract_pdf_text(file_path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        text_parts = []

        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"[Page {page_num}]\n{page_text}")

        return "\n\n".join(text_parts)
    except ImportError:
        return f"[PDF extraction requires pypdf: {file_path.name}]"


async def transcribe_audio(file_path: Path) -> str:
    """Transcribe audio using Whisper."""
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(str(file_path))
        return result["text"]
    except ImportError:
        return f"[Audio transcription requires whisper: {file_path.name}]"


async def transcribe_video(file_path: Path) -> str:
    """Extract audio from video and transcribe."""
    try:
        import subprocess
        import tempfile

        # Extract audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_path = tmp.name

        subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(file_path),
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                audio_path,
                "-y",
            ],
            check=True,
            capture_output=True,
        )

        # Transcribe the audio
        text = await transcribe_audio(Path(audio_path))

        # Cleanup
        Path(audio_path).unlink(missing_ok=True)

        return text
    except Exception as e:
        return f"[Video transcription failed: {e}]"
