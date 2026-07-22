import uuid
 
from sqlalchemy import (
    Column,
    String,
    Enum,
    DateTime,
)
 
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
 
class Ticket(Base):
 
    __tablename__ = "tickets"
 
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
 
    title = Column(
        String(200),
        nullable=False,
    )
 
    priority = Column(
        Enum(
            "low",
            "medium",
            "high",
            name="priority_enum",
        ),
        default="medium",
    )
 
    status = Column(
        Enum(
            "open",
            "in_progress",
            "resolved",
            "closed",
            name="status_enum",
        ),
        default="open",
    )
 
    assignee = Column(
    String,
    nullable=True,
    )
 
    assignee_email = Column(
    String(254),
    nullable=True,
    )
 
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
 