import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Literal, Optional

class ArtifactBase(BaseModel):
    title: str = Field(..., min_length=1)
    artifact_type: Literal["markdown", "html", "text"]
    content: str = Field(..., min_length=1)

class ArtifactCreate(ArtifactBase):
    conversation_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None

class ArtifactUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class ArtifactResponse(ArtifactBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None
    version: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def type(self) -> str:
        return self.artifact_type

    model_config = ConfigDict(from_attributes=True)
