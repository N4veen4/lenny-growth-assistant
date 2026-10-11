import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field
from datetime import datetime
from typing import Optional, List
from app.schemas.artifact import ArtifactResponse
from app.schemas.chat import Citation

class MessageBase(BaseModel):
    role: str = Field(..., description="Role of the sender: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, max_length=10000, description="Content of the message")

    @field_validator('content')
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Content must not be empty or whitespace only')
        return v

class MessageCreate(MessageBase):
    @field_validator('role')
    @classmethod
    def role_must_be_user(cls, v: str) -> str:
        if v != 'user':
            raise ValueError('Only user messages can be created via this endpoint')
        return v

class MessageResponse(MessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime
    artifacts: List[ArtifactResponse] = []
    citations: List[Citation] = []

    @computed_field
    @property
    def artifact(self) -> Optional[ArtifactResponse]:
        return self.artifacts[0] if self.artifacts else None

    model_config = ConfigDict(from_attributes=True)
