from app.repositories.ticket_repository import ticket_repository
from app.core.exceptions import TicketNotFoundError
 
 
class TicketService:
 
    async def create_ticket(
        self,
        db,
        payload,
    ):
        return await ticket_repository.create_ticket(
            db,
            payload,
        )
 
    async def get_ticket(
        self,
        db,
        ticket_id,
    ):
 
        ticket = await ticket_repository.get_ticket(
            db,
            ticket_id,
        )
 
        if ticket is None:
            raise TicketNotFoundError(str(ticket_id))
 
        return ticket
 
    async def get_tickets(
        self,
        db,
        status,
        priority,
    ):
        return await ticket_repository.get_tickets(
            db,
            status,
            priority,
        )
 
    async def update_ticket(
        self,
        db,
        ticket_id,
        payload,
    ):
 
        ticket = await ticket_repository.get_ticket(
            db,
            ticket_id,
        )
 
        if ticket is None:
            raise TicketNotFoundError(str(ticket_id))
 
        # Business Rule
        if (
            ticket.status == "closed"
            and payload.status is not None
            and payload.status != "closed"
        ):
            raise ValueError("Closed tickets cannot be reopened.")
 
        return await ticket_repository.update_ticket(
            db,
            ticket_id,
            payload,
        )
 
    async def delete_ticket(
        self,
        db,
        ticket_id,
    ):
 
        ticket = await ticket_repository.get_ticket(
            db,
            ticket_id,
        )
 
        if ticket is None:
            raise TicketNotFoundError(str(ticket_id))
 
        await ticket_repository.delete_ticket(
            db,
            ticket_id,
        )
 
        return True

    async def is_database_ready(self) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
 
 
ticket_service = TicketService() 