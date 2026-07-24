import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.repositories.ticket_repository import ticket_repository
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import ticket_service


# =====================================================================
# Unit Tests for CREATE Operation (ZONEF Principles) - 6 Test Cases
# =====================================================================

# ---------------------------------------------------------------------
# Z - Zero: Minimal / default attributes payload initialization
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_create_zero_optional_fields(mock_db: AsyncMock):
    """
    Z - Zero: Test creating a ticket with minimal valid data and checking default fields.
    """
    payload = TicketCreate(title="Bug in login", priority="low")

    def side_effect(ticket):
        ticket.id = uuid.uuid4()
        ticket.status = "open"

    mock_db.refresh.side_effect = side_effect

    created_ticket = await ticket_service.create_ticket(mock_db, payload)

    assert created_ticket.title == "Bug in login"
    assert created_ticket.priority == "low"
    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()


# ---------------------------------------------------------------------
# O - One: Create one single valid ticket entity
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_create_one_valid_ticket(mock_db: AsyncMock):
    """
    O - One: Test creating one valid ticket entity via ticket service.
    """
    payload = TicketCreate(title="Single Ticket Title", priority="high")

    def side_effect(ticket):
        ticket.id = uuid.uuid4()

    mock_db.refresh.side_effect = side_effect

    result = await ticket_service.create_ticket(mock_db, payload)

    assert result.title == "Single Ticket Title"
    assert result.priority == "high"
    mock_db.add.assert_called_once()


# ---------------------------------------------------------------------
# N - Numerous: Create multiple tickets in succession
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_create_numerous_tickets(mock_db: AsyncMock):
    """
    N - Numerous: Test creating multiple tickets sequentially using service.
    """
    tickets_data = [
        ("First ticket issue", "high"),
        ("Second ticket issue", "medium"),
        ("Third ticket issue", "low"),
    ]

    created_tickets = []
    for title, priority in tickets_data:
        payload = TicketCreate(title=title, priority=priority)
        mock_db.refresh.side_effect = lambda ticket: setattr(ticket, "id", uuid.uuid4())
        ticket = await ticket_service.create_ticket(mock_db, payload)
        created_tickets.append(ticket)

    assert len(created_tickets) == 3
    assert mock_db.add.call_count == 3
    assert mock_db.flush.await_count == 3


# ---------------------------------------------------------------------
# E - Exception: Invalid input validation and DB failure rollbacks (2 Cases)
# ---------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case_type",
    ["blank_title", "db_rollback"]
)
async def test_unit_create_exception_validation_and_rollback(mock_db: AsyncMock, case_type: str):
    """
    E - Exception: Test schema validation exception for blank title and DB error triggering rollback.
    """
    if case_type == "blank_title":
        with pytest.raises((ValueError, ValidationError)) as exc_info:
            TicketCreate(title="   ", priority="high")
        assert "Title cannot be blank" in str(exc_info.value) or "at least 3 characters" in str(exc_info.value)

    elif case_type == "db_rollback":
        payload = TicketCreate(title="DB Failure Ticket", priority="high")
        mock_db.flush.side_effect = RuntimeError("Database connection dropped")

        with pytest.raises(RuntimeError) as exc_info:
            await ticket_repository.create_ticket(mock_db, payload)

        assert "Database connection dropped" in str(exc_info.value)
        mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------
# F - Format & Boundary: Min/max title length & enum validation matrix
# ---------------------------------------------------------------------
def test_unit_create_format_boundaries_and_enums():
    """
    F - Format/Boundary: Test title boundaries (min=3, max=200, strip) and invalid priority enums.
    """
    # Min length boundary (3 chars) & Max length boundary (200 chars)
    valid_min = TicketCreate(title="abc", priority="medium")
    valid_max = TicketCreate(title="a" * 200, priority="medium")
    stripped = TicketCreate(title="  Valid Title Stripped  ", priority="medium")

    assert valid_min.title == "abc"
    assert len(valid_max.title) == 200
    assert stripped.title == "Valid Title Stripped"

    # Too short boundary (<3 chars)
    with pytest.raises(ValidationError):
        TicketCreate(title="ab", priority="medium")

    # Too long boundary (>200 chars)
    with pytest.raises(ValidationError):
        TicketCreate(title="a" * 201, priority="medium")

    # Invalid priority enums
    for invalid_prio in ["urgent", "LOW", "High", "invalid_enum"]:
        with pytest.raises(ValidationError):
            TicketCreate(title="Valid title", priority=invalid_prio)  # type: ignore
