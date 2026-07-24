from uuid import UUID
 
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
 
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.core.deps import get_db
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
)
from app.services.ticket_service import ticket_service
 
router = APIRouter(tags=["Tickets"],)
 
 
@router.post(
    "/tickets",
    response_model=TicketResponse,
)
async def create(
    ticket: TicketCreate,
    db: AsyncSession = Depends(get_db),
):
    return await ticket_service.create_ticket(
        db,
        ticket,
    )
 
 
@router.get(
    "/tickets",
    response_model=list[TicketResponse],
)
async def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await ticket_service.get_tickets(
        db,
        status,
        priority,
    )
 
 
@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
)
async def get_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await ticket_service.get_ticket(
        db,
        ticket_id,
    )
 
 
@router.patch(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
)
async def update(
    ticket_id: UUID,
    ticket: TicketUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ticket_service.update_ticket(
            db,
            ticket_id,
            ticket,
        )
 
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
 
 
@router.delete(
    "/tickets/{ticket_id}",
)
async def delete(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await ticket_service.delete_ticket(
        db,
        ticket_id,
    )
 
    return {
        "message": "Ticket deleted successfully"
    }

