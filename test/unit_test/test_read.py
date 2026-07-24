import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import TicketNotFoundError
from app.models.ticket import Ticket
from app.schemas.ticket import TicketResponse
from app.services.ticket_service import ticket_service


# =====================================================================
# Unit Tests for READ Operation (ZONEF Principles) - 6 Test Cases
# =====================================================================

# ---------------------------------------------------------------------
# Z - Zero: Empty states and 0 matching records returned (2 Cases)
# ---------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_arg, priority_arg",
    [
        (None, None),          # 0 total records in repo
        ("resolved", "high"),  # 0 matching filter results
    ]
)
async def test_unit_read_zero_tickets(mock_db: AsyncMock, status_arg: str | None, priority_arg: str | None):
    """
    Z - Zero: Test get_tickets returning an empty list when zero records match query.
    """
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    tickets = await ticket_service.get_tickets(mock_db, status=status_arg, priority=priority_arg)

    assert tickets == []
    mock_db.execute.assert_awaited_once()


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
async def test_unit_read_numerous_filtered_tickets(mock_db: AsyncMock):
    """
    N - Numerous: Test get_tickets filtering multiple ticket records.
    """
    t1 = Ticket(id=uuid.uuid4(), title="Ticket 1", status="open", priority="high")
    t2 = Ticket(id=uuid.uuid4(), title="Ticket 2", status="open", priority="medium")
    t3 = Ticket(id=uuid.uuid4(), title="Ticket 3", status="resolved", priority="low")

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [t1, t2]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    results = await ticket_service.get_tickets(mock_db, status="open", priority=None)

    assert len(results) == 2
    assert all(t.status == "open" for t in results)


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
# F - Format & Boundary: Test TicketResponse computed is_resolved property
# ---------------------------------------------------------------------
def test_unit_read_format_computed_is_resolved():
    """
    F - Format/Boundary: Test TicketResponse computed property is_resolved across status values.
    """
    now = datetime.now(timezone.utc)
    statuses = [("open", False), ("in_progress", False), ("resolved", True), ("closed", False)]

    for status_val, expected in statuses:
        resp = TicketResponse(
            id=uuid.uuid4(),
            title="Status Check Ticket",
            priority="medium",
            status=status_val,  # type: ignore
            created_at=now,
        )
        assert resp.is_resolved is expected
