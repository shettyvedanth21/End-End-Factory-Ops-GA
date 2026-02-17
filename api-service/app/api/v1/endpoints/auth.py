from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import security
from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, Factory
from app.schemas.schemas import Token, LoginRequest, UserResponse, UserProfile, UserRole

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    login_req: LoginRequest = Body(...),
) -> Any:
    # Validate factory
    factory = db.query(Factory).filter(Factory.slug == login_req.factory_slug).first()
    if not factory:
        raise HTTPException(status_code=400, detail="Factory not found")

    user = db.query(User).filter(
        User.factory_id == factory.id,
        User.email == login_req.email
    ).first()

    if not user or not security.verify_password(login_req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=user.id,
            factory_id=user.factory_id,
            role=user.role.value, # UserRole is Enum
            can_write=user.can_write,
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
        "expires_in": security.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/logout")
def logout(current_user: User = Depends(deps.get_current_active_user)) -> Any:
    # Add logic to invalidate token (e.g., store jti in Redis)
    return {"success": True, "data": {"message": "Logged out successfully."}}

@router.get("/me", response_model=UserProfile)
def read_users_me(current_user: User = Depends(deps.get_current_active_user)) -> Any:
    return current_user
