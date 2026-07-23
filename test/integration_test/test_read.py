import uuid
import pytest
from httpx import AsyncClient


# =====================================================================
# Integration Tests for READ Operations (GET /tickets & GET /tickets/{id})
# =====================================================================

@pytest.mark.asyncio
async def test_integration_get_ticket_by_id_success(async_client: AsyncClient):
    """
    Integration: Test retrieving an existing ticket by ID via GET /tickets/{ticket_id}.
    """
    # 1. Create a ticket
    create_res = await async_client.post("/tickets", json={
        "title": "Read Target Ticket",
        "priority": "medium"
    })
    created_data = create_res.json()
    ticket_id = created_data["id"]

    # 2. Get the ticket by ID
    get_res = await async_client.get(f"/tickets/{ticket_id}")

    assert get_res.status_code == 200
    fetched_data = get_res.json()
    assert fetched_data["id"] == ticket_id
    assert fetched_data["title"] == "Read Target Ticket"
    assert fetched_data["priority"] == "medium"


@pytest.mark.asyncio
async def test_integration_get_ticket_not_found(async_client: AsyncClient):
    """
    Integration: Test GET /tickets/{ticket_id} with non-existent UUID returns HTTP 404.
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
    Integration: Test GET /tickets listing all records and applying query parameter filters.
    """
    # Create multiple tickets
    await async_client.post("/tickets", json={"title": "Ticket Alpha", "priority": "low"})
    await async_client.post("/tickets", json={"title": "Ticket Beta", "priority": "high"})
    await async_client.post("/tickets", json={"title": "Ticket Gamma", "priority": "high"})

    # 1. Fetch all tickets
    res_all = await async_client.get("/tickets")
    assert res_all.status_code == 200
    all_tickets = res_all.json()
    assert len(all_tickets) >= 3

    # 2. Filter by priority=high
    res_high = await async_client.get("/tickets?priority=high")
    assert res_high.status_code == 200
    high_tickets = res_high.json()
    assert all(t["priority"] == "high" for t in high_tickets)
    assert len(high_tickets) >= 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query_params, expected_min_count",
    [
        ("status=open", 1),
        ("priority=low", 1),
        ("status=open&priority=low", 1),
        ("status=resolved", 0),
    ]
)
async def test_integration_get_tickets_parameterized_filters(
    async_client: AsyncClient,
    query_params: str,
    expected_min_count: int,
):
    """
    Integration: Test GET /tickets query filter matrix using parametrization.
    """
    await async_client.post("/tickets", json={"title": "Filter Test Item", "priority": "low"})

    response = await async_client.get(f"/tickets?{query_params}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= expected_min_count
