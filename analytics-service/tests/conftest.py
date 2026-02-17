from app.core import database
import app.services.worker as worker_module
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
    
    # Correctly monkeypatch SessionLocal used by worker
    monkeypatch.setattr(database, "SessionLocal", lambda: session)
    
    yield session
    session.close()

# Mock Services
class MockInflux:
    def query_dataset(self, factory_id, device_ids, properties, start, end):
        # Return a dummy dataframe suitable for training
        return pd.DataFrame({
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feature2": [10, 20, 30, 40, 50],
            "target": [1, 2, 3, 4, 5]
        })

class MockMinio:
    def upload_bytes(self, key, data):
        return True

@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    monkeypatch.setattr(worker_module, "influx_service", MockInflux())
    monkeypatch.setattr(worker_module, "minio_service", MockMinio())
