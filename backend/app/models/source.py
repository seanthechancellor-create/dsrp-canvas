from enum import Enum
from pydantic import BaseModel
from datetime import datetime


class SourceStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Source(BaseModel):
    id: str
    filename: str
    file_path: str
    source_type: str  # pdf, audio, video
    status: SourceStatus
    extracted_text: str | None = None
    error: str | None = None
    created_at: datetime = datetime.utcnow()
