import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import TicketNotFoundError
from app.models.ticket import Ticket
from app.repositories.ticket_repository import ticket_repository
from app.schemas.ticket import TicketResponse
from app.services.ticket_service import ticket_service


# =====================================================================
# Unit Tests for READ Operation (ZONEF Principles)
# =====================================================================

# ---------------------------------------------------------------------
# Z - Zero: Test empty states and 0 records returned
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_read_zero_tickets_returned(mock_db: AsyncMock):
    """
    Z - Zero: Test get_tickets returning an empty list when no records exist.
    """
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    tickets = await ticket_service.get_tickets(mock_db, status=None, priority=None)

    assert tickets == []
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_unit_read_zero_matching_filter_results(mock_db: AsyncMock):
    """
    Z - Zero: Test get_tickets with filter parameters returning 0 matching results.
    """
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    tickets = await ticket_service.get_tickets(mock_db, status="resolved", priority="high")

    assert tickets == []


# ---------------------------------------------------------------------
# O - One: Retrieve single valid ticket by ID
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_read_one_existing_ticket(mock_db: AsyncMock):
    """
    O - One: Test get_ticket returning a single matching Ticket object by UUID.
    """
    sample_id = uuid.uuid4()
    mock_ticket = Ticket(
        id=sample_id,
        title="Single existing issue",
        priority="medium",
        status="open",
        created_at=datetime.now(timezone.utc),
    )
    mock_db.get.return_value = mock_ticket

    ticket = await ticket_service.get_ticket(mock_db, sample_id)

    assert ticket.id == sample_id
    assert ticket.title == "Single existing issue"
    mock_db.get.assert_awaited_once_with(Ticket, sample_id)


# ---------------------------------------------------------------------
# N - Numerous: Retrieve multiple tickets and apply query filters
# ---------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_filter, priority_filter, expected_count",
    [
        (None, None, 3),
        ("open", None, 2),
        (None, "high", 1),
        ("closed", "low", 0),
    ]
)
async def test_unit_read_numerous_filtered_tickets(
    mock_db: AsyncMock,
    status_filter: str | None,
    priority_filter: str | None,
    expected_count: int,
):
    """
    N - Numerous: Test get_tickets returning multiple records under various filter conditions.
    """
    t1 = Ticket(id=uuid.uuid4(), title="Ticket 1", status="open", priority="high")
    t2 = Ticket(id=uuid.uuid4(), title="Ticket 2", status="open", priority="medium")
    t3 = Ticket(id=uuid.uuid4(), title="Ticket 3", status="resolved", priority="low")
    all_tickets = [t1, t2, t3]

    filtered = [
        t for t in all_tickets
        if (status_filter is None or t.status == status_filter) and
           (priority_filter is None or t.priority == priority_filter)
    ]

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = filtered
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    results = await ticket_service.get_tickets(mock_db, status=status_filter, priority=priority_filter)

    assert len(results) == expected_count


# ---------------------------------------------------------------------
# E - Exception: Non-existent ticket ID raises TicketNotFoundError
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_read_exception_ticket_not_found(mock_db: AsyncMock):
    """
    E - Exception: Test TicketNotFoundError is raised when ticket_id is not present.
    """
    non_existent_id = uuid.uuid4()
    mock_db.get.return_value = None

    with pytest.raises(TicketNotFoundError) as exc_info:
        await ticket_service.get_ticket(mock_db, non_existent_id)

    assert exc_info.value.ticket_id == str(non_existent_id)


# ---------------------------------------------------------------------
# F - Format & Boundary: Test TicketResponse schema & computed property
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "status, expected_is_resolved",
    [
        ("open", False),
        ("in_progress", False),
        ("resolved", True),
        ("closed", False),
    ]
)
def test_unit_read_format_computed_is_resolved(status: str, expected_is_resolved: bool):
    """
    F - Format/Boundary: Test TicketResponse computed property is_resolved for each status enum.
    """
    now = datetime.now(timezone.utc)
    response_schema = TicketResponse(
        id=uuid.uuid4(),
        title="Status Check Ticket",
        priority="medium",
        status=status,  # type: ignore
        created_at=now,
    )

    assert response_schema.is_resolved == expected_is_resolved
