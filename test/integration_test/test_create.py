import pytest
from httpx import AsyncClient


# =====================================================================
# Integration Tests for CREATE Operation (POST /tickets)
# =====================================================================

@pytest.mark.asyncio
async def test_integration_create_ticket_success(async_client: AsyncClient):
    """
    Integration: Test successful ticket creation via POST /tickets endpoint.
    """
    payload = {
        "title": "Integration Test Ticket",
        "priority": "high"
    }

    response = await async_client.post("/tickets", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Integration Test Ticket"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert data["is_resolved"] is False
    assert "created_at" in data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "priority",
    ["low", "medium", "high"]
)
async def test_integration_create_ticket_priorities(async_client: AsyncClient, priority: str):
    """
    Integration: Test ticket creation across all valid priority levels using parametrization.
    """
    payload = {
        "title": f"Ticket for priority {priority}",
        "priority": priority
    }

    response = await async_client.post("/tickets", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == priority


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_payload, expected_status",
    [
        ({"title": "ab", "priority": "low"}, 422),           # Title too short (<3 chars)
        ({"title": "a" * 201, "priority": "medium"}, 422),  # Title too long (>200 chars)
        ({"title": "", "priority": "high"}, 422),           # Blank title
        ({"title": "    ", "priority": "high"}, 422),       # Whitespace title
        ({"title": "Valid Title"}, 422),                    # Missing priority
        ({"priority": "medium"}, 422),                       # Missing title
        ({"title": "Valid Title", "priority": "urgent"}, 422) # Invalid priority enum
    ],
    ids=[
        "title_too_short",
        "title_too_long",
        "title_empty",
        "title_whitespace",
        "missing_priority",
        "missing_title",
        "invalid_priority"
    ]
)
async def test_integration_create_ticket_validation_failures(
    async_client: AsyncClient,
    invalid_payload: dict,
    expected_status: int
):
    """
    Integration: Test invalid create payloads return HTTP 422 Unprocessable Entity.
    """
    response = await async_client.post("/tickets", json=invalid_payload)
    assert response.status_code == expected_status
