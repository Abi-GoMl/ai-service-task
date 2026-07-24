import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.core.exceptions import TicketNotFoundError
from app.models.ticket import Ticket
from app.repositories.ticket_repository import ticket_repository
from app.schemas.ticket import TicketUpdate
from app.services.ticket_service import ticket_service


# =====================================================================
# Unit Tests for UPDATE Operation (ZONEF Principles) - 7 Test Cases
# =====================================================================

# ---------------------------------------------------------------------
# Z - Zero: Update with zero fields specified (empty payload)
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_update_zero_fields_changed(mock_db: AsyncMock):
    """
    Z - Zero: Test updating a ticket with an empty payload where 0 fields are modified.
    """
    sample_id = uuid.uuid4()
    mock_ticket = Ticket(
        id=sample_id,
        title="Original Title",
        priority="medium",
        status="open",
        assignee=None,
    )
    mock_db.get.return_value = mock_ticket
    empty_payload = TicketUpdate()

    updated = await ticket_service.update_ticket(mock_db, sample_id, empty_payload)

    assert updated.title == "Original Title"
    assert updated.priority == "medium"
    assert updated.status == "open"


# ---------------------------------------------------------------------
# O - One: Update one single attribute on a ticket
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_update_one_field(mock_db: AsyncMock):
    """
    O - One: Test updating exactly one field at a time.
    """
    sample_id = uuid.uuid4()
    mock_ticket = Ticket(
        id=sample_id,
        title="Initial Title",
        priority="low",
        status="open",
        assignee=None,
    )
    mock_db.get.return_value = mock_ticket
    payload = TicketUpdate(title="Updated Single Title")

    result = await ticket_service.update_ticket(mock_db, sample_id, payload)

    assert result.title == "Updated Single Title"


# ---------------------------------------------------------------------
# N - Numerous: Update multiple fields simultaneously
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_update_numerous_fields(mock_db: AsyncMock):
    """
    N - Numerous: Test updating multiple ticket attributes simultaneously.
    """
    sample_id = uuid.uuid4()
    mock_ticket = Ticket(
        id=sample_id,
        title="Old Title",
        priority="low",
        status="open",
        assignee="Old User",
    )
    mock_db.get.return_value = mock_ticket
    payload = TicketUpdate(
        title="New Critical Title",
        priority="high",
        status="resolved",
        assignee="New Assignee",
    )

    result = await ticket_service.update_ticket(mock_db, sample_id, payload)

    assert result.title == "New Critical Title"
    assert result.priority == "high"
    assert result.status == "resolved"
    assert result.assignee == "New Assignee"


# ---------------------------------------------------------------------
# E - Exception: Failure & business rule error scenarios (3 Cases)
# ---------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception_scenario",
    ["not_found", "reopen_closed_prohibited", "db_rollback"]
)
async def test_unit_update_exceptions(mock_db: AsyncMock, exception_scenario: str):
    """
    E - Exception: Test update failures: ticket not found, reopening closed ticket, DB rollback.
    """
    sample_id = uuid.uuid4()

    if exception_scenario == "not_found":
        mock_db.get.return_value = None
        payload = TicketUpdate(title="Should Fail")
        with pytest.raises(TicketNotFoundError) as exc_info:
            await ticket_service.update_ticket(mock_db, sample_id, payload)
        assert exc_info.value.ticket_id == str(sample_id)

    elif exception_scenario == "reopen_closed_prohibited":
        closed_ticket = Ticket(id=sample_id, title="Closed Ticket", priority="medium", status="closed")
        mock_db.get.return_value = closed_ticket
        payload = TicketUpdate(status="open")  # type: ignore
        with pytest.raises(ValueError) as exc_info:
            await ticket_service.update_ticket(mock_db, sample_id, payload)
        assert "Closed tickets cannot be reopened." in str(exc_info.value)

    elif exception_scenario == "db_rollback":
        mock_ticket = Ticket(id=sample_id, title="Old Title", status="open", priority="low")
        mock_db.get.return_value = mock_ticket
        mock_db.flush.side_effect = RuntimeError("DB write error")
        payload = TicketUpdate(title="New Title")
        with pytest.raises(RuntimeError):
            await ticket_repository.update_ticket(mock_db, sample_id, payload)
        mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------
# F - Format & Boundary: State transition validation & title blank checks
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_update_format_status_transitions(mock_db: AsyncMock):
    """
    F - Format/Boundary: Test valid state transitions and blank title validation error.
    """
    # Blank title validation check
    with pytest.raises(ValueError) as exc_info:
        TicketUpdate(title="   ")
    assert "Title cannot be blank" in str(exc_info.value)

    # State transitions check
    transitions = [
        ("open", "in_progress", True),
        ("in_progress", "resolved", True),
        ("resolved", "closed", True),
        ("closed", "closed", True),
        ("closed", "open", False),
    ]

    for init_status, target_status, expected_success in transitions:
        sample_id = uuid.uuid4()
        ticket = Ticket(id=sample_id, title="Transition Test", status=init_status, priority="low")
        mock_db.get.return_value = ticket
        payload = TicketUpdate(status=target_status)  # type: ignore

        if expected_success:
            res = await ticket_service.update_ticket(mock_db, sample_id, payload)
            assert res.status == target_status
        else:
            with pytest.raises(ValueError):
                await ticket_service.update_ticket(mock_db, sample_id, payload)
