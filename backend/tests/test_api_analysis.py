"""
Tests for the DSRP analysis API endpoints.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestAnalysisAPI:
    """Test suite for /api/analysis endpoints."""

    def test_analyze_invalid_move(self, client: TestClient):
        """Test that invalid move types are rejected."""
        response = client.post(
            "/api/analysis/dsrp",
            json={"concept": "Test", "move": "invalid-move"},
        )

        assert response.status_code == 400
        assert "Invalid move" in response.json()["detail"]

    def test_analyze_valid_moves(self, client: TestClient):
        """Test that all valid moves are accepted."""
        valid_moves = [
            "is-is-not",
            "zoom-in",
            "zoom-out",
            "part-party",
            "rds-barbell",
            "p-circle",
        ]

        for move in valid_moves:
            # This will fail without a real API key, but validates routing
            with patch("agents.dsrp_agent.DSRPAgent.analyze") as mock_analyze:
                mock_analyze.return_value = {
                    "pattern": "D",
                    "elements": {"identity": "test", "other": "test"},
                    "move": move,
                    "reasoning": "Test reasoning",
                    "related_concepts": [],
                    "confidence": 0.85,
                }

                response = client.post(
                    "/api/analysis/dsrp",
                    json={"concept": "Test", "move": move},
                )

                # Should not be a validation error
                assert response.status_code != 400 or "Invalid move" not in response.json().get(
                    "detail", ""
                )

    def test_analyze_missing_concept(self, client: TestClient):
        """Test that missing concept is rejected."""
        response = client.post(
            "/api/analysis/dsrp",
            json={"move": "is-is-not"},
        )

        assert response.status_code == 422  # Validation error

    def test_analyze_missing_move(self, client: TestClient):
        """Test that missing move is rejected."""
        response = client.post(
            "/api/analysis/dsrp",
            json={"concept": "Test"},
        )

        assert response.status_code == 422  # Validation error

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_analyze_is_is_not(self, mock_analyze, client: TestClient, mock_dsrp_result):
        """Test is-is-not analysis with mocked agent."""
        mock_analyze.return_value = mock_dsrp_result

        response = client.post(
            "/api/analysis/dsrp",
            json={"concept": "Democracy", "move": "is-is-not"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pattern"] == "D"
        assert "identity" in data["elements"]
        assert "other" in data["elements"]
        assert data["move"] == "is-is-not"

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_analyze_zoom_in(self, mock_analyze, client: TestClient, mock_zoom_in_result):
        """Test zoom-in analysis with mocked agent."""
        mock_analyze.return_value = mock_zoom_in_result

        response = client.post(
            "/api/analysis/dsrp",
            json={"concept": "Democracy", "move": "zoom-in"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pattern"] == "S"
        assert "parts" in data["elements"]
        assert isinstance(data["elements"]["parts"], list)

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_analyze_p_circle(self, mock_analyze, client: TestClient, mock_p_circle_result):
        """Test p-circle analysis with mocked agent."""
        mock_analyze.return_value = mock_p_circle_result

        response = client.post(
            "/api/analysis/dsrp",
            json={"concept": "Democracy", "move": "p-circle"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pattern"] == "P"
        assert "perspectives" in data["elements"]

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_analyze_with_context(self, mock_analyze, client: TestClient, mock_dsrp_result):
        """Test analysis with additional context."""
        mock_analyze.return_value = mock_dsrp_result

        response = client.post(
            "/api/analysis/dsrp",
            json={
                "concept": "Democracy",
                "move": "is-is-not",
                "context": "In the context of ancient Greece",
            },
        )

        assert response.status_code == 200
        # Verify context was passed to agent
        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        assert call_args.kwargs.get("context") == "In the context of ancient Greece"

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_analyze_returns_related_concepts(
        self, mock_analyze, client: TestClient, mock_dsrp_result
    ):
        """Test that related concepts are included in response."""
        mock_analyze.return_value = mock_dsrp_result

        response = client.post(
            "/api/analysis/dsrp",
            json={"concept": "Democracy", "move": "is-is-not"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "related_concepts" in data
        assert isinstance(data["related_concepts"], list)

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_analyze_returns_confidence(self, mock_analyze, client: TestClient, mock_dsrp_result):
        """Test that confidence score is included in response."""
        mock_analyze.return_value = mock_dsrp_result

        response = client.post(
            "/api/analysis/dsrp",
            json={"concept": "Democracy", "move": "is-is-not"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1


class TestBatchAnalysis:
    """Test suite for batch analysis endpoint."""

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_batch_analyze_single_concept(
        self, mock_analyze, client: TestClient, mock_dsrp_result
    ):
        """Test batch analysis with a single concept."""
        mock_analyze.return_value = mock_dsrp_result

        response = client.post(
            "/api/analysis/batch",
            json=["Democracy"],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["concept"] == "Democracy"
        assert "analyses" in data[0]

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_batch_analyze_multiple_concepts(
        self, mock_analyze, client: TestClient, mock_dsrp_result
    ):
        """Test batch analysis with multiple concepts."""
        mock_analyze.return_value = mock_dsrp_result

        response = client.post(
            "/api/analysis/batch",
            json=["Democracy", "Freedom", "Justice"],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @patch("agents.dsrp_agent.DSRPAgent.analyze")
    def test_batch_analyze_specific_moves(
        self, mock_analyze, client: TestClient, mock_dsrp_result
    ):
        """Test batch analysis with specific moves."""
        mock_analyze.return_value = mock_dsrp_result

        response = client.post(
            "/api/analysis/batch?moves=is-is-not&moves=zoom-in",
            json=["Democracy"],
        )

        assert response.status_code == 200
        data = response.json()
        # Should only have specified moves
        assert len(data) == 1
        analyses = data[0]["analyses"]
        assert "is-is-not" in analyses
        assert "zoom-in" in analyses
