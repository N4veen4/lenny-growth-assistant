import uuid
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class ConversationBase(BaseModel):
    title: Optional[str] = None
    user_metadata: Optional[dict] = Field(default_factory=dict)

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    user_metadata: Optional[dict] = None

class ConversationResponse(ConversationBase):
    id: uuid.UUID
    user_metadata: Optional[dict] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
