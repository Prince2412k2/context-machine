from pydantic import BaseModel, Field
from datetime import datetime


# Shared base attributes for reusability
class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


# Schema for creation
class DocumentCreate(DocumentBase):
    pass


# Schema for partial updates
class DocumentUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)


# Schema for reading/response
class DocumentRead(DocumentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # replaces orm_mode in Pydantic v2
