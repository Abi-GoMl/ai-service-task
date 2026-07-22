from datetime import datetime
from typing import Literal
from uuid import UUID
 
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)
 
class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    priority: Literal["low", "medium", "high"] 
 
    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str):
 
        value = value.strip()
 
        if value == "":
            raise ValueError("Title cannot be blank")
 
        return value
 
class TicketUpdate(BaseModel):
    title: str | None = None
    priority: Literal["low", "medium", "high"] | None = None
    status: Literal["open", "in_progress", "resolved", "closed"] | None = None
    assignee: str | None = None
 
    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None):
 
        if value is None:
            return value
 
        value = value.strip()
 
        if value == "":
            raise ValueError("Title cannot be blank")
 
        return value
 
 
class TicketResponse(BaseModel):
    id: UUID
    title: str
    priority: Literal["low", "medium", "high"]
    status: Literal["open", "in_progress", "resolved", "closed"]
    created_at: datetime
 
    model_config = ConfigDict(from_attributes=True)
 
    @computed_field
    @property
    def is_resolved(self) -> bool:
        return self.status == "resolved"
 