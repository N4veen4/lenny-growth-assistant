from typing import Generator
from app.db.session import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail="Database connection error")
    finally:
        db.close()
