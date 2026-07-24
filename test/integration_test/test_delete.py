import uuid
import pytest
from httpx import AsyncClient


# =====================================================================
# Integration Tests for DELETE Operation (DELETE /tickets/{ticket_id}) - 3 Test Cases
# =====================================================================

@pytest.mark.asyncio
async def test_integration_delete_ticket_success(async_client: AsyncClient):
    """
    Integration: Test deleting an existing ticket via DELETE /tickets/{ticket_id} (Happy Path).
    Verifies that subsequent GET returns HTTP 404.
    """
    # 1. Create a ticket
    create_res = await async_client.post("/tickets", json={
        "title": "Ticket to Delete",
        "priority": "low"
    })
    ticket_id = create_res.json()["id"]

    # 2. Delete the ticket
    delete_res = await async_client.delete(f"/tickets/{ticket_id}")

    assert delete_res.status_code == 200
    assert delete_res.json() == {"message": "Ticket deleted successfully"}

    # 3. Verify ticket no longer exists
    get_res = await async_client.get(f"/tickets/{ticket_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_integration_delete_ticket_not_found(async_client: AsyncClient):
    """
    Integration: Test DELETE /tickets/{ticket_id} with non-existent ID returns HTTP 404 (Failure Path).
    """
    non_existent_id = str(uuid.uuid4())

    response = await async_client.delete(f"/tickets/{non_existent_id}")

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "ticket_not_found"
    assert data["id"] == non_existent_id


@pytest.mark.asyncio
async def test_integration_delete_ticket_invalid_uuid(async_client: AsyncClient):
    """
    Integration: Test DELETE /tickets/{ticket_id} with malformed UUID path parameter returns HTTP 422 (Edge Case).
    """
    invalid_id = "not-a-valid-uuid-format"

    response = await async_client.delete(f"/tickets/{invalid_id}")

    assert response.status_code == 422
