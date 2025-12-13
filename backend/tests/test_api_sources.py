"""
Tests for the sources API endpoints.
"""

import io
import pytest
from fastapi.testclient import TestClient


class TestSourcesAPI:
    """Test suite for /api/sources endpoints."""

    def test_upload_pdf(self, client: TestClient):
        """Test uploading a PDF file."""
        # Create a minimal PDF-like content
        pdf_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}

        response = client.post("/api/sources/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "source_id" in data
        assert "file_path" in data
        assert data["status"] == "processing"

    def test_upload_audio(self, client: TestClient):
        """Test uploading an audio file."""
        audio_content = b"fake audio content"
        files = {"file": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")}

        response = client.post("/api/sources/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"

    def test_upload_video(self, client: TestClient):
        """Test uploading a video file."""
        video_content = b"fake video content"
        files = {"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}

        response = client.post("/api/sources/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"

    def test_get_source_status_not_found(self, client: TestClient):
        """Test getting status of non-existent source."""
        response = client.get("/api/sources/nonexistent-id/status")

        assert response.status_code == 404

    def test_list_sources(self, client: TestClient):
        """Test listing all sources."""
        response = client.get("/api/sources/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_upload_and_check_status(self, client: TestClient):
        """Test upload flow with status checking."""
        # Upload
        pdf_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        upload_response = client.post("/api/sources/upload", files=files)

        assert upload_response.status_code == 200
        source_id = upload_response.json()["source_id"]

        # Check status (should be processing or ready)
        status_response = client.get(f"/api/sources/{source_id}/status")
        assert status_response.status_code == 200
        status = status_response.json()["status"]
        assert status in ["processing", "ready", "error"]


class TestSourceTypeDetection:
    """Test file type detection for sources."""

    def test_pdf_detection(self, client: TestClient):
        """Test that PDF files are detected correctly."""
        files = {"file": ("document.pdf", io.BytesIO(b"content"), "application/pdf")}
        response = client.post("/api/sources/upload", files=files)

        assert response.status_code == 200
        # The source type is inferred from filename

    def test_audio_detection_mp3(self, client: TestClient):
        """Test MP3 audio detection."""
        files = {"file": ("audio.mp3", io.BytesIO(b"content"), "audio/mpeg")}
        response = client.post("/api/sources/upload", files=files)
        assert response.status_code == 200

    def test_audio_detection_wav(self, client: TestClient):
        """Test WAV audio detection."""
        files = {"file": ("audio.wav", io.BytesIO(b"content"), "audio/wav")}
        response = client.post("/api/sources/upload", files=files)
        assert response.status_code == 200

    def test_video_detection_mp4(self, client: TestClient):
        """Test MP4 video detection."""
        files = {"file": ("video.mp4", io.BytesIO(b"content"), "video/mp4")}
        response = client.post("/api/sources/upload", files=files)
        assert response.status_code == 200

    def test_video_detection_webm(self, client: TestClient):
        """Test WebM video detection."""
        files = {"file": ("video.webm", io.BytesIO(b"content"), "video/webm")}
        response = client.post("/api/sources/upload", files=files)
        assert response.status_code == 200
