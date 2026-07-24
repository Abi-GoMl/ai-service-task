import uuid
import pytest
from httpx import AsyncClient


# =====================================================================
# Integration Tests for READ Operations (GET /tickets & GET /tickets/{id}) - 4 Test Cases
# =====================================================================

@pytest.mark.asyncio
async def test_integration_get_ticket_by_id_success(async_client: AsyncClient):
    """
    Integration: Test retrieving an existing ticket by ID via GET /tickets/{ticket_id} (Happy Path).
    """
    # 1. Create a ticket
    create_res = await async_client.post("/tickets", json={
        "title": "Read Target Ticket",
        "priority": "medium"
    })
    ticket_id = create_res.json()["id"]

    # 2. Get the ticket by ID
    get_res = await async_client.get(f"/tickets/{ticket_id}")

    assert get_res.status_code == 200
    fetched_data = get_res.json()
    assert fetched_data["id"] == ticket_id
    assert fetched_data["title"] == "Read Target Ticket"


@pytest.mark.asyncio
async def test_integration_get_ticket_not_found(async_client: AsyncClient):
    """
    Integration: Test GET /tickets/{ticket_id} with non-existent UUID returns HTTP 404 (Failure Path).
    """
    non_existent_id = str(uuid.uuid4())
    response = await async_client.get(f"/tickets/{non_existent_id}")

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "ticket_not_found"
    assert data["id"] == non_existent_id


@pytest.mark.asyncio
async def test_integration_get_tickets_list_and_filters(async_client: AsyncClient):
    """
    Integration: Test GET /tickets listing all records and applying priority query filter (Happy Path).
    """
    await async_client.post("/tickets", json={"title": "Ticket Alpha", "priority": "low"})
    await async_client.post("/tickets", json={"title": "Ticket Beta", "priority": "high"})
    await async_client.post("/tickets", json={"title": "Ticket Gamma", "priority": "high"})

    # 1. Fetch all tickets
    res_all = await async_client.get("/tickets")
    assert res_all.status_code == 200
    assert len(res_all.json()) >= 3

    # 2. Filter by priority=high
    res_high = await async_client.get("/tickets?priority=high")
    assert res_high.status_code == 200
    high_tickets = res_high.json()
    assert all(t["priority"] == "high" for t in high_tickets)


@pytest.mark.asyncio
async def test_integration_get_tickets_parameterized_filters(async_client: AsyncClient):
    """
    Integration: Test GET /tickets query filter matrix across status and priority parameters (Edge Cases).
    """
    await async_client.post("/tickets", json={"title": "Filter Test Item", "priority": "low"})

    filter_queries = [
        ("status=open", 1),
        ("priority=low", 1),
        ("status=open&priority=low", 1),
        ("status=resolved", 0),
    ]

    for q_params, min_expected in filter_queries:
        response = await async_client.get(f"/tickets?{q_params}")
        assert response.status_code == 200
        assert len(response.json()) >= min_expected
