import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.artifact import Artifact
from app.schemas.artifact import ArtifactResponse

router = APIRouter()

@router.get("/conversations/{conversation_id}/artifacts", response_model=List[ArtifactResponse])
def list_conversation_artifacts(conversation_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    from app.models.conversation import Conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    artifacts = db.query(Artifact).filter(Artifact.conversation_id == conversation_id).order_by(Artifact.created_at.desc()).offset(skip).limit(limit).all()
    return artifacts

@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: uuid.UUID, db: Session = Depends(get_db)):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return artifact
