import uuid
import pytest
from httpx import AsyncClient


# =====================================================================
# Integration Tests for UPDATE Operation (PATCH /tickets/{ticket_id})
# =====================================================================

@pytest.mark.asyncio
async def test_integration_update_ticket_success(async_client: AsyncClient):
    """
    Integration: Test updating a ticket title, priority, status, and assignee via PATCH /tickets/{id}.
    """
    # 1. Create a ticket
    create_res = await async_client.post("/tickets", json={
        "title": "Initial Integration Title",
        "priority": "low"
    })
    ticket_id = create_res.json()["id"]

    # 2. Patch update
    update_payload = {
        "title": "Updated Integration Title",
        "priority": "high",
        "status": "in_progress",
        "assignee": "Tech Lead"
    }
    patch_res = await async_client.patch(f"/tickets/{ticket_id}", json=update_payload)

    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["title"] == "Updated Integration Title"
    assert updated_data["priority"] == "high"
    assert updated_data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_integration_update_ticket_not_found(async_client: AsyncClient):
    """
    Integration: Test PATCH /tickets/{ticket_id} with non-existent ID returns HTTP 404.
    """
    non_existent_id = str(uuid.uuid4())
    update_payload = {"title": "New Title"}

    response = await async_client.patch(f"/tickets/{non_existent_id}", json=update_payload)

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "ticket_not_found"


@pytest.mark.asyncio
async def test_integration_update_reopen_closed_ticket_fails(async_client: AsyncClient):
    """
    Integration: Test attempting to reopen a closed ticket returns HTTP 400 Bad Request.
    """
    # 1. Create ticket
    create_res = await async_client.post("/tickets", json={"title": "Ticket to Close", "priority": "medium"})
    ticket_id = create_res.json()["id"]

    # 2. Close ticket
    await async_client.patch(f"/tickets/{ticket_id}", json={"status": "closed"})

    # 3. Attempt to reopen ticket -> should fail with 400
    reopen_res = await async_client.patch(f"/tickets/{ticket_id}", json={"status": "open"})

    assert reopen_res.status_code == 400
    assert reopen_res.json()["detail"] == "Closed tickets cannot be reopened."


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_update_body, expected_status",
    [
        ({"title": ""}, 422),             # Blank title string
        ({"title": "   "}, 422),          # Whitespace title
        ({"priority": "invalid"}, 422),   # Invalid priority enum
        ({"status": "unknown_status"}, 422) # Invalid status enum
    ]
)
async def test_integration_update_validation_errors(
    async_client: AsyncClient,
    invalid_update_body: dict,
    expected_status: int,
):
    """
    Integration: Test invalid update payloads return HTTP 422.
    """
    # Create ticket
    create_res = await async_client.post("/tickets", json={"title": "Validation Target", "priority": "low"})
    ticket_id = create_res.json()["id"]

    response = await async_client.patch(f"/tickets/{ticket_id}", json=invalid_update_body)
    assert response.status_code == expected_status
