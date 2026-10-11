import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.message import Message
from sqlalchemy.exc import OperationalError

@pytest.fixture(scope="module")
def pg_engine():
    db_url = os.getenv("TEST_DATABASE_URL")
    if not db_url:
        pytest.fail(
            "BLOCKED: TEST_DATABASE_URL is not set.\n"
            "MANUAL STEP REQUIRED: Please add TEST_DATABASE_URL to backend/.env\n"
            "Format: TEST_DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:<port>/<test_db>"
        )
    if "sqlite" in db_url:
        pytest.fail("BLOCKED: TEST_DATABASE_URL points to SQLite. A real PostgreSQL URL is required.")
    
    engine = create_engine(db_url)
    try:
        # Check connection
        with engine.connect() as conn:
            pass
    except Exception as e:
        pytest.skip(f"PostgreSQL is not available at TEST_DATABASE_URL ({e})")
        
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def pg_session(pg_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_pg_persistence(pg_session):
    # Test creation and persistence
    convo = Conversation(title="PG Test Convo")
    pg_session.add(convo)
    pg_session.commit()
    
    msg1 = Message(conversation_id=convo.id, role="user", content="Hello PG")
    msg2 = Message(conversation_id=convo.id, role="user", content="Second message")
    pg_session.add_all([msg1, msg2])
    pg_session.commit()
    
    # Read back to ensure they are saved
    saved_convo = pg_session.query(Conversation).filter_by(id=convo.id).first()
    assert saved_convo is not None
    assert saved_convo.title == "PG Test Convo"
    assert len(saved_convo.messages) == 2

def test_pg_cascade_deletion(pg_session):
    convo = Conversation(title="To Delete")
    pg_session.add(convo)
    pg_session.commit()
    
    msg = Message(conversation_id=convo.id, role="user", content="Will be deleted")
    pg_session.add(msg)
    pg_session.commit()
    
    # Perform deletion
    pg_session.delete(convo)
    pg_session.commit()
    
    # Verify messages are gone (Cascade delete)
    msgs = pg_session.query(Message).filter_by(conversation_id=convo.id).all()
    assert len(msgs) == 0

def test_independent_conversation_histories(pg_session):
    convo1 = Conversation(title="Convo 1")
    convo2 = Conversation(title="Convo 2")
    pg_session.add_all([convo1, convo2])
    pg_session.commit()

    msg1 = Message(conversation_id=convo1.id, role="user", content="Message 1")
    msg2 = Message(conversation_id=convo2.id, role="user", content="Message 2")
    pg_session.add_all([msg1, msg2])
    pg_session.commit()

    hist1 = pg_session.query(Message).filter_by(conversation_id=convo1.id).all()
    hist2 = pg_session.query(Message).filter_by(conversation_id=convo2.id).all()

    assert len(hist1) == 1
    assert hist1[0].content == "Message 1"
    
    assert len(hist2) == 1
    assert hist2[0].content == "Message 2"
