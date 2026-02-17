from app.core import database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    database.Base.metadata.create_all(bind=engine)
    yield engine
    database.Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine, monkeypatch):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    # Mock SessionLocal in processor.py
    monkeypatch.setattr("app.services.processor.SessionLocal", lambda: session)
    
    # Clear tables before each test
    session.execute("DELETE FROM alerts")
    session.execute("DELETE FROM rules")
    session.commit()
    
    yield session
    
    session.close()
