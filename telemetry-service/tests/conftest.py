from app.core import influx
from app.services import redis_service
from app.core.database import Base, engine, SessionLocal
from app.models.models import Device, DeviceProperty
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
import os

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine, monkeypatch):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    # Mock SessionLocal used in processor.py to return our test session
    monkeypatch.setattr("app.services.processor.SessionLocal", lambda: session) # Return session instance or callable returning it? 
    # SessionLocal() returns session. So lambda: session works if SessionLocal() is called.
    
    yield session
    
    session.close()

@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """Disable actual network calls for external services during tests"""
    def mock_write(*args, **kwargs):
        pass
    
    def mock_publish(*args, **kwargs):
        pass
    
    # Mock Influx
    monkeypatch.setattr(influx.InfluxService, "write_point", mock_write)
    # Mock Redis
    monkeypatch.setattr(redis_service.RedisService, "publish", mock_publish)
    # We also need to prevent Redis connection attempt at import time if possible, or mock it.
    # But since imports happen before fixtures, we rely on the try-except in RedisService.__init__
    
    yield
