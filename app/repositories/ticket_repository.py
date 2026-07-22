from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
 
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate
 
 
class TicketRepository:
 
    async def create_ticket(
        self,
        db: AsyncSession,
        payload: TicketCreate,
    ) -> Ticket:
        ticket = Ticket(
            title=payload.title,
            priority=payload.priority,
        )
        db.add(ticket)
        try:
            await db.flush()
            await db.refresh(ticket)
            return ticket
        except Exception as e:
            await db.rollback()
            raise e
 
    async def get_ticket(
        self,
        db: AsyncSession,
        ticket_id: UUID,  
    ) -> Optional[Ticket]:
        return await db.get(Ticket, ticket_id)
 
    async def get_tickets(
        self,
        db: AsyncSession,
        status: Optional[str] = None,  
        priority: Optional[str] = None,  
    ) -> List[Ticket]:
        query = select(Ticket)
 
        if status:
            query = query.where(Ticket.status == status)
        if priority:
            query = query.where(Ticket.priority == priority)
 
        result = await db.execute(query)
        return list(result.scalars().all())
 
    async def update_ticket(
        self,
        db: AsyncSession,
        ticket_id: UUID,
        payload: TicketUpdate,
    ) -> Optional[Ticket]:
        ticket = await db.get(Ticket, ticket_id)
       
       
        if not ticket:
            return None
 
       
        update_data = payload.model_dump(exclude_unset=True)
 
        for field, value in update_data.items():
            setattr(ticket, field, value)
           
        try:
            await db.flush()
            await db.refresh(ticket)
            return ticket
        except Exception as e:
            await db.rollback()
            raise e
 
    async def delete_ticket(
        self,
        db: AsyncSession,
        ticket_id: UUID,
    ) -> bool:
        ticket = await db.get(Ticket, ticket_id)
       
        if not ticket:
            return False
 
        try:
            await db.delete(ticket)
            await db.flush()
            return True  
        except Exception as e:
            await db.rollback()
            raise e
 
 
ticket_repository = TicketRepository()
 
 