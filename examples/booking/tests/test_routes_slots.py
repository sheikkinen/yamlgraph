"""Tests for Slot API routes."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with in-memory database."""
    from examples.booking.api.app import create_app
    from examples.booking.api.db import BookingDB

    db = BookingDB(":memory:")
    db.init_schema()
    app = create_app(db=db)
    yield TestClient(app)
    db.close()


@pytest.fixture
def client_with_calendar(client):
    """Create client with a calendar already created."""
    resp = client.post("/calendars", json={"name": "Dr. Smith", "type": "provider"})
    calendar_id = resp.json()["id"]
    return client, calendar_id


class TestSlotRoutes:
    """Tests for /calendars/{calendar_id}/slots endpoints."""

    def test_create_slot(self, client_with_calendar):
        """POST /calendars/{id}/slots should create slot."""
        client, cal_id = client_with_calendar
        response = client.post(
            f"/calendars/{cal_id}/slots",
            json={"start": "2025-01-15T10:00:00", "duration_min": 60},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["calendar_id"] == cal_id
        assert data["available"] is True
        assert "id" in data

    def test_create_slot_calendar_not_found(self, client):
        """POST /calendars/{id}/slots should 404 for missing calendar."""
        response = client.post(
            "/calendars/nonexistent/slots",
            json={"start": "2025-01-15T10:00:00", "duration_min": 60},
        )
        assert response.status_code == 404

    def test_list_slots_empty(self, client_with_calendar):
        """GET /calendars/{id}/slots should return empty list."""
        client, cal_id = client_with_calendar
        response = client.get(f"/calendars/{cal_id}/slots")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_slots(self, client_with_calendar):
        """GET /calendars/{id}/slots should return all slots."""
        client, cal_id = client_with_calendar
        client.post(
            f"/calendars/{cal_id}/slots",
            json={"start": "2025-01-15T10:00:00", "duration_min": 30},
        )
        client.post(
            f"/calendars/{cal_id}/slots",
            json={"start": "2025-01-15T11:00:00", "duration_min": 30},
        )
        response = client.get(f"/calendars/{cal_id}/slots")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_slots_available_filter(self, client_with_calendar):
        """GET /calendars/{id}/slots?available=true should filter."""
        client, cal_id = client_with_calendar
        # Create one slot and mark it unavailable later
        resp1 = client.post(
            f"/calendars/{cal_id}/slots",
            json={"start": "2025-01-15T10:00:00", "duration_min": 30},
        )
        slot_id = resp1.json()["id"]
        client.post(
            f"/calendars/{cal_id}/slots",
            json={"start": "2025-01-15T11:00:00", "duration_min": 30},
        )
        # Book the first slot (makes it unavailable)
        client.post(
            "/appointments",
            json={"slot_id": slot_id, "patient_name": "John Doe"},
        )
        # Query for available only
        response = client.get(f"/calendars/{cal_id}/slots?available=true")
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) == 1
        assert slots[0]["available"] is True

    def test_get_slot(self, client_with_calendar):
        """GET /slots/{id} should return slot."""
        client, cal_id = client_with_calendar
        create_resp = client.post(
            f"/calendars/{cal_id}/slots",
            json={"start": "2025-01-15T10:00:00", "duration_min": 60},
        )
        slot_id = create_resp.json()["id"]

        response = client.get(f"/slots/{slot_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == slot_id

    def test_get_slot_not_found(self, client):
        """GET /slots/{id} should 404 for missing slot."""
        response = client.get("/slots/nonexistent")
        assert response.status_code == 404

    def test_delete_slot(self, client_with_calendar):
        """DELETE /slots/{id} should delete slot."""
        client, cal_id = client_with_calendar
        create_resp = client.post(
            f"/calendars/{cal_id}/slots",
            json={"start": "2025-01-15T10:00:00", "duration_min": 60},
        )
        slot_id = create_resp.json()["id"]

        response = client.delete(f"/slots/{slot_id}")
        assert response.status_code == 204

        # Verify gone
        get_resp = client.get(f"/slots/{slot_id}")
        assert get_resp.status_code == 404

    def test_delete_slot_not_found(self, client):
        """DELETE /slots/{id} should 404 for missing slot."""
        response = client.delete("/slots/nonexistent")
        assert response.status_code == 404
