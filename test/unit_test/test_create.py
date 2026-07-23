import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.models.ticket import Ticket
from app.repositories.ticket_repository import ticket_repository, TicketRepository
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import ticket_service, TicketService


# =====================================================================
# Unit Tests for CREATE Operation (ZONEF Principles)
# =====================================================================

# ---------------------------------------------------------------------
# Z - Zero: Minimal / default attributes payload initialization
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_create_zero_optional_fields(mock_db: AsyncMock):
    """
    Z - Zero: Test creating a ticket with minimal valid data and checking defaults.
    """
    payload = TicketCreate(title="Bug in login", priority="low")
    
    def side_effect(ticket):
        ticket.id = uuid.uuid4()
        ticket.status = "open"
        ticket.created_at = None

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
@pytest.mark.parametrize("priority", ["low", "medium", "high"])
async def test_unit_create_one_valid_ticket(mock_db: AsyncMock, priority: str):
    """
    O - One: Test creating one valid ticket for each allowed priority.
    Uses parameterized inputs for all priorities.
    """
    payload = TicketCreate(title="Single Ticket Title", priority=priority)

    def side_effect(ticket):
        ticket.id = uuid.uuid4()

    mock_db.refresh.side_effect = side_effect

    result = await ticket_service.create_ticket(mock_db, payload)

    assert result.title == "Single Ticket Title"
    assert result.priority == priority
    mock_db.add.assert_called_once()


# ---------------------------------------------------------------------
# N - Numerous: Create multiple tickets in succession
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_create_numerous_tickets(mock_db: AsyncMock):
    """
    N - Numerous: Test creating multiple tickets sequentially using repository/service.
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
# E - Exception: Invalid inputs, blank title, missing fields, DB errors
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "blank_title",
    ["", "   ", "\t\n  "],
    ids=["empty_string", "spaces", "newlines_tabs"]
)
def test_unit_create_exception_blank_title(blank_title: str):
    """
    E - Exception: Test ValueError/ValidationError raised when title is blank or whitespace.
    """
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        TicketCreate(title=blank_title, priority="high")
    assert "Title cannot be blank" in str(exc_info.value) or "at least 3 characters" in str(exc_info.value)


def test_unit_create_exception_missing_priority():
    """
    E - Exception: Test ValidationError when required priority field is missing.
    """
    with pytest.raises(ValidationError):
        TicketCreate(title="Valid title missing priority")  # type: ignore


@pytest.mark.asyncio
async def test_unit_create_exception_database_error_triggers_rollback(mock_db: AsyncMock):
    """
    E - Exception: Test repository handles DB exceptions by executing rollback.
    """
    payload = TicketCreate(title="DB Failure Ticket", priority="high")
    mock_db.flush.side_effect = RuntimeError("Database connection dropped")

    with pytest.raises(RuntimeError) as exc_info:
        await ticket_repository.create_ticket(mock_db, payload)

    assert "Database connection dropped" in str(exc_info.value)
    mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------
# F - Format & Boundary: Test min/max title length & formatting
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "title, is_valid",
    [
        ("abc", True),                 # Min boundary = 3 chars
        ("a" * 200, True),             # Max boundary = 200 chars
        ("ab", False),                 # Too short (2 chars)
        ("a" * 201, False),            # Too long (201 chars)
        ("  Valid Title Stripped  ", True), # Whitespace stripping format check
    ]
)
def test_unit_create_format_title_boundaries(title: str, is_valid: bool):
    """
    F - Format/Boundary: Test boundary conditions for title length and whitespace formatting.
    """
    if is_valid:
        schema = TicketCreate(title=title, priority="medium")
        assert len(schema.title) >= 3
        assert schema.title == schema.title.strip()
    else:
        with pytest.raises(ValidationError):
            TicketCreate(title=title, priority="medium")


@pytest.mark.parametrize("invalid_priority", ["urgent", "LOW", "High", "invalid_enum"])
def test_unit_create_format_invalid_priority_enum(invalid_priority: str):
    """
    F - Format/Boundary: Test invalid priority enum values.
    """
    with pytest.raises(ValidationError):
        TicketCreate(title="Valid title", priority=invalid_priority)  # type: ignore
