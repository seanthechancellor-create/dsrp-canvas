"""
Pytest configuration and fixtures for DSRP Canvas backend tests.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["TYPEDB_HOST"] = "localhost"
os.environ["TYPEDB_PORT"] = "1729"

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_concept():
    """Sample concept data for testing."""
    return {
        "name": "Test Concept",
        "description": "A test concept for unit testing",
        "source_ids": [],
    }


@pytest.fixture
def sample_analysis_request():
    """Sample DSRP analysis request."""
    return {
        "concept": "Democracy",
        "move": "is-is-not",
        "context": None,
    }


@pytest.fixture
def sample_source_data():
    """Sample source metadata."""
    return {
        "source_id": "test-source-123",
        "source_type": "pdf",
        "file_path": "/tmp/test.pdf",
        "original_filename": "test.pdf",
    }


@pytest.fixture
def mock_dsrp_result():
    """Mock DSRP analysis result."""
    return {
        "pattern": "D",
        "elements": {
            "identity": "A system of government by the whole population",
            "other": "Autocracy, dictatorship, monarchy",
        },
        "boundary": "Citizen participation in governance",
        "reasoning": "Democracy is defined by collective decision-making...",
        "move": "is-is-not",
        "concept": "Democracy",
        "confidence": 0.85,
        "related_concepts": ["Government", "Voting", "Citizens"],
    }


@pytest.fixture
def mock_zoom_in_result():
    """Mock zoom-in analysis result."""
    return {
        "pattern": "S",
        "elements": {
            "whole": "Democracy",
            "parts": ["Voting System", "Legislative Branch", "Executive Branch", "Judicial Branch"],
        },
        "part_descriptions": {
            "Voting System": "The mechanism for citizen participation",
            "Legislative Branch": "Creates and passes laws",
        },
        "reasoning": "Democracy consists of several interconnected systems...",
        "move": "zoom-in",
        "concept": "Democracy",
        "confidence": 0.9,
        "related_concepts": ["Voting System", "Legislative Branch"],
    }


@pytest.fixture
def mock_p_circle_result():
    """Mock p-circle analysis result."""
    return {
        "pattern": "P",
        "elements": {
            "concept": "Democracy",
            "perspectives": [
                {"point": "Citizen", "view": "A system that gives me a voice"},
                {"point": "Politician", "view": "A framework for legitimate authority"},
                {"point": "Philosopher", "view": "An ideal of collective self-governance"},
            ],
        },
        "tensions": ["Individual rights vs collective good"],
        "synthesis": "Different stakeholders value different aspects...",
        "reasoning": "Multiple perspectives reveal different facets...",
        "move": "p-circle",
        "concept": "Democracy",
        "confidence": 0.85,
        "related_concepts": ["Citizen", "Politician", "Philosopher"],
    }
