import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.models import User, Factory, UserRole
from app.core.security import get_password_hash, create_access_token

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def factory_one(db):
    factory = Factory(name="Factory One", slug="factory-one")
    db.add(factory)
    db.commit()
    db.refresh(factory)
    return factory

@pytest.fixture(scope="function")
def user_one(db, factory_one):
    user = User(
        email="user1@example.com",
        password_hash=get_password_hash("password"),
        role=UserRole.ADMIN,
        factory_id=factory_one.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def normal_user_token_headers(user_one):
    access_token = create_access_token(
        subject=user_one.id,
        factory_id=user_one.factory_id,
        role="admin",
        can_write=True
    )
    return {"Authorization": f"Bearer {access_token}"}
