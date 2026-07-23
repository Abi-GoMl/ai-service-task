import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import TicketNotFoundError
from app.models.ticket import Ticket
from app.repositories.ticket_repository import ticket_repository
from app.services.ticket_service import ticket_service


# =====================================================================
# Unit Tests for DELETE Operation (ZONEF Principles)
# =====================================================================

# ---------------------------------------------------------------------
# Z - Zero: Repository level deletion when 0 items are affected
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_delete_zero_records_in_repository(mock_db: AsyncMock):
    """
    Z - Zero: Test ticket_repository.delete_ticket returning False when 0 rows match.
    """
    non_existent_id = uuid.uuid4()
    mock_db.get.return_value = None

    result = await ticket_repository.delete_ticket(mock_db, non_existent_id)

    assert result is False
    mock_db.delete.assert_not_called()


# ---------------------------------------------------------------------
# O - One: Successfully delete one existing ticket
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_delete_one_existing_ticket(mock_db: AsyncMock):
    """
    O - One: Test deleting 1 single valid ticket via ticket_service.
    """
    sample_id = uuid.uuid4()
    existing_ticket = Ticket(
        id=sample_id,
        title="Ticket to be deleted",
        priority="medium",
        status="open",
    )
    mock_db.get.return_value = existing_ticket

    result = await ticket_service.delete_ticket(mock_db, sample_id)

    assert result is True
    mock_db.delete.assert_awaited_once_with(existing_ticket)
    mock_db.flush.assert_awaited()


# ---------------------------------------------------------------------
# N - Numerous: Delete multiple tickets sequentially
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_delete_numerous_tickets(mock_db: AsyncMock):
    """
    N - Numerous: Test deleting multiple tickets one after another in a loop.
    """
    ticket_ids = [uuid.uuid4() for _ in range(3)]
    for tid in ticket_ids:
        ticket = Ticket(id=tid, title=f"Ticket {tid}", priority="low", status="open")
        mock_db.get.return_value = ticket

        result = await ticket_service.delete_ticket(mock_db, tid)
        assert result is True

    assert mock_db.delete.await_count == 3


# ---------------------------------------------------------------------
# E - Exception: Non-existent ticket ID raises TicketNotFoundError
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unit_delete_exception_not_found(mock_db: AsyncMock):
    """
    E - Exception: Test TicketNotFoundError is raised by service when ticket ID does not exist.
    """
    non_existent_id = uuid.uuid4()
    mock_db.get.return_value = None

    with pytest.raises(TicketNotFoundError) as exc_info:
        await ticket_service.delete_ticket(mock_db, non_existent_id)

    assert exc_info.value.ticket_id == str(non_existent_id)


@pytest.mark.asyncio
async def test_unit_delete_exception_db_error_triggers_rollback(mock_db: AsyncMock):
    """
    E - Exception: Test database failure during deletion triggers rollback in repository.
    """
    sample_id = uuid.uuid4()
    existing_ticket = Ticket(id=sample_id, title="Ticket DB error", priority="low")
    mock_db.get.return_value = existing_ticket
    mock_db.flush.side_effect = RuntimeError("Delete constraint error")

    with pytest.raises(RuntimeError):
        await ticket_repository.delete_ticket(mock_db, sample_id)

    mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------
# F - Format & Boundary: Test parameter types and string representations
# ---------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("uuid_instance", [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()])
async def test_unit_delete_format_valid_uuid_types(mock_db: AsyncMock, uuid_instance: uuid.UUID):
    """
    F - Format/Boundary: Test delete_ticket handles various valid UUID format inputs cleanly.
    """
    ticket = Ticket(id=uuid_instance, title="Formatted UUID Ticket", priority="high")
    mock_db.get.return_value = ticket

    result = await ticket_service.delete_ticket(mock_db, uuid_instance)
    assert result is True
