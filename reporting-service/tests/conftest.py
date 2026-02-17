from app.core import database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
import pandas as pd
import json

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

# Mock Services
class MockMinio:
    def upload_bytes(self, key, data, content_type):
        return True

class MockFetcher:
    def get_telemetry_aggregates(self, factory_id, device_ids, start, end):
        return pd.DataFrame({
            "property_name": ["value"],
            "value": [100]
        })
        
    def get_alerts(self, *args):
        return []

@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    import app.services.worker as worker_module
    
    # Mock MinIO
    monkeypatch.setattr(worker_module, "minio_service", MockMinio())
    
    # DataFetcher is instantiated inside process_report: fetcher = DataFetcher()
    # Mock the class constructor to return our instance
    monkeypatch.setattr(worker_module, "DataFetcher", MockFetcher)
    
    # Also need to mock renderers if they fail without real data or deps (WeasyPrint)
    # But WeasyPrint might work if installed. If not, mock generate_pdf.
    def mock_pdf(*args):
        return b"PDF_BYTES"
    
    monkeypatch.setattr("app.services.worker.generate_pdf", mock_pdf)
