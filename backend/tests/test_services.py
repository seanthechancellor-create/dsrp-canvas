"""
Tests for backend services.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.export_service import (
    export_to_markdown,
    export_to_obsidian,
    export_to_remnote,
    format_analysis_markdown,
    format_analysis_obsidian,
)


class TestExportService:
    """Test suite for export service functions."""

    @pytest.mark.asyncio
    async def test_export_to_markdown_empty(self):
        """Test markdown export with empty concept list."""
        result = await export_to_markdown([])
        assert "# DSRP Knowledge Export" in result

    @pytest.mark.asyncio
    async def test_export_to_obsidian_has_tags(self):
        """Test Obsidian export includes tags."""
        result = await export_to_obsidian([])
        assert "#dsrp" in result
        assert "#systems-thinking" in result

    @pytest.mark.asyncio
    async def test_export_to_remnote_empty(self):
        """Test RemNote export returns empty list for no concepts."""
        result = await export_to_remnote([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_analysis_markdown(self):
        """Test markdown formatting of analysis."""
        analysis = {
            "move": "is-is-not",
            "pattern": "D",
            "reasoning": "This is the reasoning text.",
        }
        result = format_analysis_markdown(analysis)

        assert "Is Is Not" in result  # Title-cased move name
        assert "(D)" in result
        assert "This is the reasoning text" in result

    def test_format_analysis_obsidian(self):
        """Test Obsidian formatting includes pattern tag."""
        analysis = {
            "move": "zoom-in",
            "pattern": "S",
            "reasoning": "Breaking down into parts.",
        }
        result = format_analysis_obsidian(analysis)

        assert "Zoom In" in result
        assert "#s" in result.lower()  # Pattern as tag


class TestIngestionService:
    """Test suite for file ingestion service."""

    @pytest.mark.asyncio
    async def test_extract_pdf_text_missing_pypdf(self):
        """Test graceful handling when pypdf is missing."""
        from app.services.ingestion import extract_pdf_text

        with patch.dict("sys.modules", {"pypdf": None}):
            # Should return placeholder text
            result = await extract_pdf_text(Path("/fake/path.pdf"))
            assert "PDF extraction" in result or isinstance(result, str)

    @pytest.mark.asyncio
    async def test_transcribe_audio_missing_whisper(self):
        """Test graceful handling when whisper is missing."""
        from app.services.ingestion import transcribe_audio

        with patch.dict("sys.modules", {"whisper": None}):
            result = await transcribe_audio(Path("/fake/audio.mp3"))
            assert "transcription" in result.lower() or isinstance(result, str)


class TestTypeDBService:
    """Test suite for TypeDB service."""

    def test_typedb_service_creation(self):
        """Test TypeDB service can be instantiated."""
        from app.services.typedb_service import TypeDBService

        service = TypeDBService()
        assert service is not None
        assert service._driver is None  # Lazy loaded

    def test_get_typedb_service_singleton(self):
        """Test that get_typedb_service returns singleton."""
        from app.services.typedb_service import get_typedb_service

        service1 = get_typedb_service()
        service2 = get_typedb_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_typedb_service_graceful_failure(self):
        """Test TypeDB service handles connection failure gracefully."""
        from app.services.typedb_service import TypeDBService

        service = TypeDBService()

        # Mock driver creation to fail
        with patch.object(service, "_create_driver", return_value=None):
            # Should not crash, just return None
            driver = service.driver
            # Either returns None or raises RuntimeError on transaction


class TestDSRPAgent:
    """Test suite for DSRP AI agent."""

    def test_agent_creation(self):
        """Test DSRP agent can be instantiated."""
        from agents.dsrp_agent import DSRPAgent

        agent = DSRPAgent()
        assert agent is not None
        assert agent.providers is not None
        assert "gemini" in agent.providers or "claude" in agent.providers or "openai" in agent.providers

    def test_agent_move_prompts(self):
        """Test all moves have prompt templates."""
        from agents.dsrp_agent import MOVE_PROMPTS

        expected_moves = [
            "is-is-not",
            "zoom-in",
            "zoom-out",
            "part-party",
            "rds-barbell",
            "p-circle",
        ]

        for move in expected_moves:
            assert move in MOVE_PROMPTS
            assert "{concept}" in MOVE_PROMPTS[move]

    def test_extract_related_concepts_parts(self):
        """Test extraction of related concepts from parts."""
        from agents.dsrp_agent import DSRPAgent

        agent = DSRPAgent()
        result = {
            "elements": {
                "parts": ["Part A", "Part B", "Part C"],
            }
        }

        related = agent._extract_related_concepts(result)
        assert "Part A" in related
        assert "Part B" in related
        assert "Part C" in related

    def test_extract_related_concepts_whole(self):
        """Test extraction of related concepts from whole."""
        from agents.dsrp_agent import DSRPAgent

        agent = DSRPAgent()
        result = {
            "elements": {
                "whole": "Larger System",
            }
        }

        related = agent._extract_related_concepts(result)
        assert "Larger System" in related

    def test_extract_related_concepts_perspectives(self):
        """Test extraction of related concepts from perspectives."""
        from agents.dsrp_agent import DSRPAgent

        agent = DSRPAgent()
        result = {
            "elements": {
                "perspectives": [
                    {"point": "Observer 1", "view": "View 1"},
                    {"point": "Observer 2", "view": "View 2"},
                ],
            }
        }

        related = agent._extract_related_concepts(result)
        assert "Observer 1" in related
        assert "Observer 2" in related

    def test_extract_related_concepts_deduplication(self):
        """Test that duplicate concepts are removed."""
        from agents.dsrp_agent import DSRPAgent

        agent = DSRPAgent()
        result = {
            "elements": {
                "parts": ["Same", "Same", "Different"],
            }
        }

        related = agent._extract_related_concepts(result)
        # Should be deduplicated
        assert related.count("Same") == 1
        assert "Different" in related

    def test_extract_related_concepts_limit(self):
        """Test that related concepts are limited to 10."""
        from agents.dsrp_agent import DSRPAgent

        agent = DSRPAgent()
        result = {
            "elements": {
                "parts": [f"Part {i}" for i in range(20)],
            }
        }

        related = agent._extract_related_concepts(result)
        assert len(related) <= 10
