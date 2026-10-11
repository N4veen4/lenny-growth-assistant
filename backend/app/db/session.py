import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

# Ensure all models are registered on Base.metadata before create_all
import app.models.conversation  # noqa: F401
import app.models.message       # noqa: F401
import app.models.artifact      # noqa: F401

logger = logging.getLogger(__name__)

def init_engine():
    db_url = settings.DATABASE_URL
    try:
        eng = create_engine(db_url, pool_pre_ping=True)
        with eng.connect() as conn:
            pass
        logger.info("Connected to primary database successfully.")
        # Ensure all tables are created if schema needs setup
        Base.metadata.create_all(bind=eng)
        try:
            with eng.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS message_id UUID REFERENCES messages(id)"))
                conn.commit()
        except Exception:
            pass
        try:
            with eng.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS citations_json TEXT"))
                conn.commit()
        except Exception:
            try:
                with eng.connect() as conn:
                    from sqlalchemy import text
                    conn.execute(text("ALTER TABLE messages ADD COLUMN citations_json TEXT"))
                    conn.commit()
            except Exception:
                pass
        return eng
    except Exception as e:
        if settings.ENVIRONMENT.lower() == "production":
            logger.critical(
                f"Production database connection to {db_url} failed: {e}. "
                "Silent fallback to SQLite is disallowed in production."
            )
            raise RuntimeError(f"Database connection failed in production: {e}") from e

        logger.warning(
            f"Primary database connection failed ({e}). Falling back to local SQLite for development."
        )
        sqlite_url = "sqlite:///./lenny_assistant.db"
        eng = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=eng)
        try:
            with eng.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE artifacts ADD COLUMN message_id UUID REFERENCES messages(id)"))
                conn.commit()
        except Exception:
            pass
        try:
            with eng.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE messages ADD COLUMN citations_json TEXT"))
                conn.commit()
        except Exception:
            pass
        logger.info(f"Initialized fallback SQLite database: {sqlite_url}")
        return eng

engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
