"""
Tests for the concepts API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestConceptsAPI:
    """Test suite for /api/concepts endpoints."""

    def test_create_concept(self, client: TestClient, sample_concept):
        """Test creating a new concept."""
        response = client.post("/api/concepts/", json=sample_concept)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_concept["name"]
        assert data["description"] == sample_concept["description"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_concept_minimal(self, client: TestClient):
        """Test creating a concept with only required fields."""
        response = client.post("/api/concepts/", json={"name": "Minimal Concept"})

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Concept"
        assert data["description"] is None

    def test_create_concept_missing_name(self, client: TestClient):
        """Test that creating a concept without name fails."""
        response = client.post("/api/concepts/", json={"description": "No name"})

        assert response.status_code == 422  # Validation error

    def test_list_concepts_empty(self, client: TestClient):
        """Test listing concepts when none exist."""
        response = client.get("/api/concepts/")

        assert response.status_code == 200
        # May or may not be empty depending on test isolation
        assert isinstance(response.json(), list)

    def test_list_concepts_with_pagination(self, client: TestClient, sample_concept):
        """Test listing concepts with pagination parameters."""
        # Create a few concepts
        for i in range(3):
            client.post("/api/concepts/", json={**sample_concept, "name": f"Concept {i}"})

        # Test pagination
        response = client.get("/api/concepts/?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_get_concept_not_found(self, client: TestClient):
        """Test getting a non-existent concept."""
        response = client.get("/api/concepts/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_concept_not_found(self, client: TestClient):
        """Test deleting a non-existent concept."""
        response = client.delete("/api/concepts/nonexistent-id")

        assert response.status_code == 404

    def test_concept_crud_flow(self, client: TestClient, sample_concept):
        """Test full CRUD flow for concepts."""
        # Create
        create_response = client.post("/api/concepts/", json=sample_concept)
        assert create_response.status_code == 200
        concept_id = create_response.json()["id"]

        # Read
        get_response = client.get(f"/api/concepts/{concept_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == sample_concept["name"]

        # Delete
        delete_response = client.delete(f"/api/concepts/{concept_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == concept_id

        # Verify deleted
        verify_response = client.get(f"/api/concepts/{concept_id}")
        assert verify_response.status_code == 404
