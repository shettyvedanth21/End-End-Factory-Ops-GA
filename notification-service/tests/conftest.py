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
    
    # Mock SessionLocal used in worker.py
    monkeypatch.setattr("app.services.worker.database.SessionLocal", lambda: session) 
    
    yield session
    session.close()

# Mock SMTP/Twilio
@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    import app.services.worker as worker_module
    
    class MockSMTP:
        def send_email(self, *args, **kwargs):
            return True
            
    class MockWhatsApp:
        def send_whatsapp(self, *args, **kwargs):
            return True
            
    monkeypatch.setattr(worker_module, "email_service", MockSMTP())
    monkeypatch.setattr(worker_module, "whatsapp_service", MockWhatsApp())
