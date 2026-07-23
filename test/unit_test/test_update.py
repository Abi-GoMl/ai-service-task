import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.core.exceptions import TicketNotFoundError
from app.models.ticket import Ticket
from app.repositories.ticket_repository import ticket_repository
from app.schemas.ticket import TicketUpdate
from app.services.ticket_service import ticket_service


# =====================================================================
# Unit Tests for UPDATE Operation (ZONEF Principles)
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
@pytest.mark.parametrize(
    "field_name, new_value",
    [
        ("title", "Updated Single Title"),
        ("priority", "high"),
        ("status", "in_progress"),
        ("assignee", "Alice Worker"),
    ]
)
async def test_unit_update_one_field(mock_db: AsyncMock, field_name: str, new_value: str):
    """
    O - One: Test updating exactly one field at a time using parameterized inputs.
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
    payload = TicketUpdate(**{field_name: new_value})

    result = await ticket_service.update_ticket(mock_db, sample_id, payload)

    assert getattr(result, field_name) == new_value


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
# E - Exception: Business rules & validation error scenarios
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_update_exception_ticket_not_found(mock_db: AsyncMock):
    """
    E - Exception: Test TicketNotFoundError when attempting to update a non-existent ticket.
    """
    non_existent_id = uuid.uuid4()
    mock_db.get.return_value = None
    payload = TicketUpdate(title="Should Fail")

    with pytest.raises(TicketNotFoundError) as exc_info:
        await ticket_service.update_ticket(mock_db, non_existent_id, payload)

    assert exc_info.value.ticket_id == str(non_existent_id)


@pytest.mark.asyncio
@pytest.mark.parametrize("target_status", ["open", "in_progress", "resolved"])
async def test_unit_update_exception_cannot_reopen_closed_ticket(mock_db: AsyncMock, target_status: str):
    """
    E - Exception: Business rule verification: Closed tickets cannot be reopened to non-closed statuses.
    """
    sample_id = uuid.uuid4()
    closed_ticket = Ticket(
        id=sample_id,
        title="Closed Ticket",
        priority="medium",
        status="closed",
    )
    mock_db.get.return_value = closed_ticket
    payload = TicketUpdate(status=target_status)  # type: ignore

    with pytest.raises(ValueError) as exc_info:
        await ticket_service.update_ticket(mock_db, sample_id, payload)

    assert "Closed tickets cannot be reopened." in str(exc_info.value)


@pytest.mark.parametrize("invalid_title", ["", "   ", "\t  \n"])
def test_unit_update_exception_blank_title_validation(invalid_title: str):
    """
    E - Exception: Schema validation error when updating title to blank/whitespace.
    """
    with pytest.raises(ValueError) as exc_info:
        TicketUpdate(title=invalid_title)
    assert "Title cannot be blank" in str(exc_info.value)


@pytest.mark.asyncio
async def test_unit_update_exception_db_rollback_on_failure(mock_db: AsyncMock):
    """
    E - Exception: Test repository rollback when database flush fails during update.
    """
    sample_id = uuid.uuid4()
    mock_ticket = Ticket(id=sample_id, title="Old Title", status="open", priority="low")
    mock_db.get.return_value = mock_ticket
    mock_db.flush.side_effect = RuntimeError("DB write error")

    payload = TicketUpdate(title="New Title")

    with pytest.raises(RuntimeError):
        await ticket_repository.update_ticket(mock_db, sample_id, payload)

    mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------
# F - Format & Boundary: Test valid state transitions & formatting
# ---------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "initial_status, new_status, should_succeed",
    [
        ("open", "in_progress", True),
        ("in_progress", "resolved", True),
        ("resolved", "closed", True),
        ("closed", "closed", True),  # Updating closed ticket with closed status is allowed
        ("closed", "open", False),   # Reopening closed ticket is disallowed
    ]
)
async def test_unit_update_format_status_transitions(
    mock_db: AsyncMock,
    initial_status: str,
    new_status: str,
    should_succeed: bool,
):
    """
    F - Format/Boundary: Test state transitions matrix for ticket status.
    """
    sample_id = uuid.uuid4()
    ticket = Ticket(id=sample_id, title="Transition Test", status=initial_status, priority="low")
    mock_db.get.return_value = ticket
    payload = TicketUpdate(status=new_status)  # type: ignore

    if should_succeed:
        result = await ticket_service.update_ticket(mock_db, sample_id, payload)
        assert result.status == new_status
    else:
        with pytest.raises(ValueError):
            await ticket_service.update_ticket(mock_db, sample_id, payload)
