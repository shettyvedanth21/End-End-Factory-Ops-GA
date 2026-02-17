from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core import security
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, UserUpdate, UserResponse

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    # Only show users for the current factory
    if current_user.role == "platform_root":
        users = db.query(User).offset(skip).limit(limit).all()
    else:
        users = db.query(User).filter(User.factory_id == current_user.factory_id).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    if current_user.role != "super_admin" and current_user.role != "platform_root":
         raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")
         
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    factory_id = current_user.factory_id
    if current_user.role == "platform_root":
        # Platform root creating global user logic or specific factory user logic would be complex here without factory_id in request.
        # Assuming platform root creates users for specific factories if provided, or global users.
        # But for this scope, let's assume super_admin creates users for their own factory.
        pass

    user = User(
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        role=user_in.role,
        can_write=user_in.can_write,
        factory_id=factory_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user = db.query(User).filter(User.id == user_id, User.factory_id == current_user.factory_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user_data = jsonable_encoder(user)
    update_data = user_in.model_dump(exclude_unset=True)
    for field in user_data:
        if field in update_data:
            setattr(user, field, update_data[field])
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
