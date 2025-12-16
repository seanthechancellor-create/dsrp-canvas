"""
Tests for the DSRP patterns API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestDSRPFrameworkAPI:
    """Test suite for /api/dsrp/framework endpoint."""

    def test_get_framework(self, client: TestClient):
        """Test getting the complete DSRP framework."""
        response = client.get("/api/dsrp/framework")

        assert response.status_code == 200
        data = response.json()

        # Should have all three sections
        assert "patterns" in data
        assert "moves" in data
        assert "dynamics" in data

    def test_framework_has_four_patterns(self, client: TestClient):
        """Test that framework includes all 4 DSRP patterns."""
        response = client.get("/api/dsrp/framework")
        data = response.json()

        patterns = data["patterns"]
        assert len(patterns) == 4
        assert "D" in patterns
        assert "S" in patterns
        assert "R" in patterns
        assert "P" in patterns

    def test_framework_has_eight_moves(self, client: TestClient):
        """Test that framework includes all 8 moves (6 core + 2 causal)."""
        response = client.get("/api/dsrp/framework")
        data = response.json()

        moves = data["moves"]
        assert len(moves) == 8
        expected_moves = ["is-is-not", "zoom-in", "zoom-out", "part-party", "rds-barbell", "p-circle", "woc", "waoc"]
        for move in expected_moves:
            assert move in moves

    def test_framework_has_three_dynamics(self, client: TestClient):
        """Test that framework includes all 3 dynamics."""
        response = client.get("/api/dsrp/framework")
        data = response.json()

        dynamics = data["dynamics"]
        assert len(dynamics) == 3
        assert "=" in dynamics
        assert "co-implication" in dynamics
        assert "simultaneity" in dynamics


class TestPatternsAPI:
    """Test suite for /api/dsrp/patterns endpoints."""

    def test_list_patterns(self, client: TestClient):
        """Test listing all patterns."""
        response = client.get("/api/dsrp/patterns")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4

    def test_pattern_structure(self, client: TestClient):
        """Test that each pattern has required fields."""
        response = client.get("/api/dsrp/patterns")
        data = response.json()

        required_fields = ["id", "name", "elements", "description", "color", "icon"]
        for pattern in data:
            for field in required_fields:
                assert field in pattern, f"Pattern missing field: {field}"

    def test_pattern_elements_are_pairs(self, client: TestClient):
        """Test that each pattern has exactly 2 elements."""
        response = client.get("/api/dsrp/patterns")
        data = response.json()

        for pattern in data:
            assert len(pattern["elements"]) == 2

    def test_get_pattern_d(self, client: TestClient):
        """Test getting Distinctions pattern."""
        response = client.get("/api/dsrp/patterns/D")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "D"
        assert data["name"] == "Distinctions"
        assert data["elements"] == ["identity", "other"]
        assert data["color"] == "#1976D2"

    def test_get_pattern_s(self, client: TestClient):
        """Test getting Systems pattern."""
        response = client.get("/api/dsrp/patterns/S")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "S"
        assert data["name"] == "Systems"
        assert data["elements"] == ["part", "whole"]
        assert data["color"] == "#388E3C"

    def test_get_pattern_r(self, client: TestClient):
        """Test getting Relationships pattern."""
        response = client.get("/api/dsrp/patterns/R")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "R"
        assert data["name"] == "Relationships"
        assert data["elements"] == ["action", "reaction"]
        assert data["color"] == "#F57C00"

    def test_get_pattern_p(self, client: TestClient):
        """Test getting Perspectives pattern."""
        response = client.get("/api/dsrp/patterns/P")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "P"
        assert data["name"] == "Perspectives"
        assert data["elements"] == ["point", "view"]
        assert data["color"] == "#7B1FA2"

    def test_get_pattern_lowercase(self, client: TestClient):
        """Test that lowercase pattern IDs are accepted."""
        response = client.get("/api/dsrp/patterns/d")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "D"

    def test_get_pattern_invalid(self, client: TestClient):
        """Test that invalid pattern ID returns error."""
        response = client.get("/api/dsrp/patterns/X")

        assert response.status_code == 200  # Returns error in body
        data = response.json()
        assert "error" in data


class TestMovesAPI:
    """Test suite for /api/dsrp/moves endpoints."""

    def test_list_moves(self, client: TestClient):
        """Test listing all moves."""
        response = client.get("/api/dsrp/moves")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 8

    def test_move_structure(self, client: TestClient):
        """Test that each move has required fields."""
        response = client.get("/api/dsrp/moves")
        data = response.json()

        required_fields = ["id", "name", "pattern", "description", "question"]
        for move in data:
            for field in required_fields:
                assert field in move, f"Move missing field: {field}"

    def test_get_move_is_is_not(self, client: TestClient):
        """Test getting is-is-not move."""
        response = client.get("/api/dsrp/moves/is-is-not")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "is-is-not"
        assert data["name"] == "Is/Is Not"
        assert data["pattern"] == "D"

    def test_get_move_zoom_in(self, client: TestClient):
        """Test getting zoom-in move."""
        response = client.get("/api/dsrp/moves/zoom-in")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "zoom-in"
        assert data["pattern"] == "S"

    def test_get_move_p_circle(self, client: TestClient):
        """Test getting p-circle move."""
        response = client.get("/api/dsrp/moves/p-circle")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "p-circle"
        assert data["pattern"] == "P"

    def test_get_move_woc(self, client: TestClient):
        """Test getting Web of Causality move."""
        response = client.get("/api/dsrp/moves/woc")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "woc"
        assert data["name"] == "Web of Causality"
        assert data["pattern"] == "R"

    def test_get_move_waoc(self, client: TestClient):
        """Test getting Web of Anticausality move."""
        response = client.get("/api/dsrp/moves/waoc")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "waoc"
        assert data["name"] == "Web of Anticausality"
        assert data["pattern"] == "R"

    def test_get_move_invalid(self, client: TestClient):
        """Test that invalid move ID returns error."""
        response = client.get("/api/dsrp/moves/invalid-move")

        assert response.status_code == 200  # Returns error in body
        data = response.json()
        assert "error" in data
        assert "valid_moves" in data

    def test_moves_pattern_mapping(self, client: TestClient):
        """Test that moves map to correct patterns."""
        expected_mapping = {
            "is-is-not": "D",
            "zoom-in": "S",
            "zoom-out": "S",
            "part-party": "S",
            "rds-barbell": "R",
            "p-circle": "P",
            "woc": "R",
            "waoc": "R",
        }

        for move_id, expected_pattern in expected_mapping.items():
            response = client.get(f"/api/dsrp/moves/{move_id}")
            data = response.json()
            assert data["pattern"] == expected_pattern, f"Move {move_id} should map to {expected_pattern}"


class TestDynamicsAPI:
    """Test suite for /api/dsrp/dynamics endpoint."""

    def test_list_dynamics(self, client: TestClient):
        """Test listing all dynamics."""
        response = client.get("/api/dsrp/dynamics")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_dynamics_structure(self, client: TestClient):
        """Test that each dynamic has required fields."""
        response = client.get("/api/dsrp/dynamics")
        data = response.json()

        required_fields = ["symbol", "name", "description"]
        for dynamic in data:
            for field in required_fields:
                assert field in dynamic, f"Dynamic missing field: {field}"

    def test_dynamics_symbols(self, client: TestClient):
        """Test that dynamics have correct symbols."""
        response = client.get("/api/dsrp/dynamics")
        data = response.json()

        symbols = [d["symbol"] for d in data]
        assert "=" in symbols
        # Unicode symbols for co-implication and simultaneity
        assert any(s in symbols for s in ["⇔", "\u21d4"])
        assert any(s in symbols for s in ["✷", "\u2737"])


class TestElementsAPI:
    """Test suite for /api/dsrp/elements endpoint."""

    def test_get_elements_d(self, client: TestClient):
        """Test getting element pair for Distinctions."""
        response = client.get("/api/dsrp/elements/D")

        assert response.status_code == 200
        data = response.json()
        assert data["pattern"] == "D"
        assert data["elements"] == ["identity", "other"]
        assert data["left_element"] == "identity"
        assert data["right_element"] == "other"

    def test_get_elements_s(self, client: TestClient):
        """Test getting element pair for Systems."""
        response = client.get("/api/dsrp/elements/S")

        assert response.status_code == 200
        data = response.json()
        assert data["left_element"] == "part"
        assert data["right_element"] == "whole"

    def test_get_elements_r(self, client: TestClient):
        """Test getting element pair for Relationships."""
        response = client.get("/api/dsrp/elements/R")

        assert response.status_code == 200
        data = response.json()
        assert data["left_element"] == "action"
        assert data["right_element"] == "reaction"

    def test_get_elements_p(self, client: TestClient):
        """Test getting element pair for Perspectives."""
        response = client.get("/api/dsrp/elements/P")

        assert response.status_code == 200
        data = response.json()
        assert data["left_element"] == "point"
        assert data["right_element"] == "view"


class TestMovePatternAPI:
    """Test suite for /api/dsrp/move-pattern endpoint."""

    def test_get_move_pattern_zoom_in(self, client: TestClient):
        """Test getting pattern info for zoom-in move."""
        response = client.get("/api/dsrp/move-pattern/zoom-in")

        assert response.status_code == 200
        data = response.json()
        assert data["move"] == "zoom-in"
        assert data["pattern"] == "S"
        assert "pattern_info" in data
        assert data["pattern_info"]["name"] == "Systems"

    def test_get_move_pattern_rds_barbell(self, client: TestClient):
        """Test getting pattern info for rds-barbell move."""
        response = client.get("/api/dsrp/move-pattern/rds-barbell")

        assert response.status_code == 200
        data = response.json()
        assert data["move"] == "rds-barbell"
        assert data["pattern"] == "R"
        assert data["pattern_info"]["color"] == "#F57C00"


class TestAnalysisMetadata:
    """Test that analysis responses include pattern/move metadata."""

    def test_mock_analysis_includes_pattern_metadata(self, client: TestClient):
        """Test that mock analysis includes pattern metadata."""
        response = client.post(
            "/api/analysis/mock",
            json={"concept": "Test", "move": "zoom-in"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "pattern_metadata" in data
        assert data["pattern_metadata"]["id"] == "S"
        assert data["pattern_metadata"]["name"] == "Systems"
        assert data["pattern_metadata"]["color"] == "#388E3C"
        assert data["pattern_metadata"]["elements"] == ["part", "whole"]

    def test_mock_analysis_includes_move_metadata(self, client: TestClient):
        """Test that mock analysis includes move metadata."""
        response = client.post(
            "/api/analysis/mock",
            json={"concept": "Test", "move": "p-circle"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "move_metadata" in data
        assert data["move_metadata"]["id"] == "p-circle"
        assert data["move_metadata"]["name"] == "P-Circle"
        assert "description" in data["move_metadata"]
