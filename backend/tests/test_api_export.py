"""
Tests for the export API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestExportAPI:
    """Test suite for /api/export endpoints."""

    def test_export_markdown_empty(self, client: TestClient):
        """Test markdown export with no concepts."""
        response = client.post(
            "/api/export/markdown",
            json={"concept_ids": []},
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "DSRP Knowledge Export" in data["content"]

    def test_export_markdown_with_concepts(self, client: TestClient, sample_concept):
        """Test markdown export with concepts."""
        # Create a concept first
        create_response = client.post("/api/concepts/", json=sample_concept)
        concept_id = create_response.json()["id"]

        # Export
        response = client.post(
            "/api/export/markdown",
            json={"concept_ids": [concept_id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert sample_concept["name"] in data["content"]

    def test_export_obsidian_empty(self, client: TestClient):
        """Test Obsidian export with no concepts."""
        response = client.post(
            "/api/export/obsidian",
            json={"concept_ids": []},
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "#dsrp" in data["content"]  # Obsidian tags

    def test_export_obsidian_with_wikilinks(self, client: TestClient, sample_concept):
        """Test Obsidian export includes wikilinks."""
        # Create a concept first
        create_response = client.post("/api/concepts/", json=sample_concept)
        concept_id = create_response.json()["id"]

        # Export
        response = client.post(
            "/api/export/obsidian",
            json={"concept_ids": [concept_id]},
        )

        assert response.status_code == 200
        data = response.json()
        # Should have wikilink format
        assert "[[" in data["content"]
        assert "]]" in data["content"]

    def test_export_remnote_empty(self, client: TestClient):
        """Test RemNote export with no concepts."""
        response = client.post(
            "/api/export/remnote",
            json={"concept_ids": []},
        )

        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        assert isinstance(data["cards"], list)

    def test_export_remnote_card_structure(self, client: TestClient, sample_concept):
        """Test RemNote export card structure."""
        # Create a concept first
        create_response = client.post("/api/concepts/", json=sample_concept)
        concept_id = create_response.json()["id"]

        # Export (may not have cards if no analyses)
        response = client.post(
            "/api/export/remnote",
            json={"concept_ids": [concept_id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        # Cards list may be empty if no analyses exist
        if data["cards"]:
            card = data["cards"][0]
            assert "front" in card
            assert "back" in card
            assert "tags" in card

    def test_export_markdown_options(self, client: TestClient, sample_concept):
        """Test markdown export with options."""
        create_response = client.post("/api/concepts/", json=sample_concept)
        concept_id = create_response.json()["id"]

        # Without analyses
        response = client.post(
            "/api/export/markdown",
            json={
                "concept_ids": [concept_id],
                "include_analyses": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    def test_export_obsidian_options(self, client: TestClient, sample_concept):
        """Test Obsidian export with options."""
        create_response = client.post("/api/concepts/", json=sample_concept)
        concept_id = create_response.json()["id"]

        # Without relationships
        response = client.post(
            "/api/export/obsidian",
            json={
                "concept_ids": [concept_id],
                "include_relationships": False,
            },
        )

        assert response.status_code == 200


class TestExportFormats:
    """Test export format validation and content."""

    def test_markdown_has_headers(self, client: TestClient, sample_concept):
        """Test that markdown export has proper headers."""
        create_response = client.post("/api/concepts/", json=sample_concept)
        concept_id = create_response.json()["id"]

        response = client.post(
            "/api/export/markdown",
            json={"concept_ids": [concept_id]},
        )

        content = response.json()["content"]
        assert content.startswith("#")  # Has heading

    def test_obsidian_has_tags(self, client: TestClient):
        """Test that Obsidian export includes tags."""
        response = client.post(
            "/api/export/obsidian",
            json={"concept_ids": []},
        )

        content = response.json()["content"]
        assert "#dsrp" in content
        assert "#systems-thinking" in content
        assert "#knowledge-graph" in content

    def test_remnote_has_dsrp_tags(self, client: TestClient, sample_concept):
        """Test that RemNote cards have DSRP tags."""
        create_response = client.post("/api/concepts/", json=sample_concept)
        concept_id = create_response.json()["id"]

        response = client.post(
            "/api/export/remnote",
            json={"concept_ids": [concept_id]},
        )

        cards = response.json()["cards"]
        # If cards exist, they should have dsrp tag
        for card in cards:
            assert "dsrp" in card["tags"]
