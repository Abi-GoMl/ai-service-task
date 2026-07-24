import pytest
from httpx import AsyncClient


# =====================================================================
# Integration Tests for CREATE Operation (POST /tickets) - 5 Test Cases
# =====================================================================

@pytest.mark.asyncio
async def test_integration_create_ticket_success(async_client: AsyncClient):
    """
    Integration: Test successful ticket creation via POST /tickets endpoint (Happy Path).
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
    Integration: Test ticket creation across all valid priority levels (3 Cases).
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
async def test_integration_create_ticket_validation_failures(async_client: AsyncClient):
    """
    Integration: Test invalid payloads return HTTP 422 Unprocessable Entity (Failure & Edge Cases).
    """
    invalid_payloads = [
        {"title": "ab", "priority": "low"},           # Title too short (<3 chars)
        {"title": "a" * 201, "priority": "medium"},  # Title too long (>200 chars)
        {"title": "", "priority": "high"},           # Blank title
        {"title": "    ", "priority": "high"},       # Whitespace title
        {"title": "Valid Title"},                    # Missing priority
        {"priority": "medium"},                       # Missing title
        {"title": "Valid Title", "priority": "urgent"} # Invalid priority enum
    ]

    for payload in invalid_payloads:
        response = await async_client.post("/tickets", json=payload)
        assert response.status_code == 422
