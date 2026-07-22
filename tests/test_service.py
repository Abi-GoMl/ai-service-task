from unittest.mock import AsyncMock

import pytest

from app.services.ticket_service import TicketService
from app.core.exceptions import TicketNotFoundError

#Happy path test for get_ticket
@pytest.mark.asyncio
async def test_get_ticket_success(monkeypatch):

    service = TicketService()

    ticket = type(
        "Ticket",
        (),
        {
            "status": "open"
        }
    )()

    mock = AsyncMock(return_value=ticket)

    monkeypatch.setattr(
        "app.services.ticket_service.ticket_repository.get_ticket",
        mock,
    )

    result = await service.get_ticket(
        None,
        "123"
    )

    assert result == ticket

#Ticket not found test for get_ticket
@pytest.mark.asyncio
async def test_ticket_not_found(monkeypatch):

    service = TicketService()

    mock = AsyncMock(return_value=None)

    monkeypatch.setattr(
        "app.services.ticket_service.ticket_repository.get_ticket",
        mock,
    )

    with pytest.raises(TicketNotFoundError):

        await service.get_ticket(
            None,
            "123"
        )

#Delete missing ticket
@pytest.mark.asyncio
async def test_closed_ticket_cannot_reopen(monkeypatch):

    service = TicketService()

    ticket = type(
        "Ticket",
        (),
        {
            "status": "closed"
        }
    )()

    payload = type(
        "Payload",
        (),
        {
            "status": "open"
        }
    )()

    monkeypatch.setattr(
        "app.services.ticket_service.ticket_repository.get_ticket",
        AsyncMock(return_value=ticket),
    )

    with pytest.raises(ValueError):

        await service.update_ticket(
            None,
            "1",
            payload,
        )

#Delete success
@pytest.mark.asyncio
async def test_delete_ticket_success(monkeypatch):

    service = TicketService()

    ticket = object()

    monkeypatch.setattr(
        "app.services.ticket_service.ticket_repository.get_ticket",
        AsyncMock(return_value=ticket),
    )

    monkeypatch.setattr(
        "app.services.ticket_service.ticket_repository.delete_ticket",
        AsyncMock(return_value=True),
    )

    result = await service.delete_ticket(
        None,
        "100",
    )

    assert result is True