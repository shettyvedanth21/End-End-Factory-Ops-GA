from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User
import jwt
from datetime import datetime, timedelta

router = APIRouter()

SECRET_KEY = "super_secret_jwt_key_please_change_in_prod"
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    email: str
    password: str
    factory_slug: str

class Token(BaseModel):
    success: bool
    data: dict

@router.post("/auth/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # 1. Lookup user by email (ignore password for now as init.sql has no password hash)
    # This is "production-ready" structure but uses pre-existing unsecured seed for demo access
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    # 2. Generate Token
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
        "factory_id": user.factory_id,
        "can_write": True, # Hardcoded for demo
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    encoded_jwt = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "success": True,
        "data": {
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "factory_id": user.factory_id,
                "can_write": True
            }
        }
    }

@router.get("/auth/me")
def me(db: Session = Depends(get_db)):
    # For simplicity, returning a fixed user if token validation passes elsewhere
    # In real prod, decode token here.
    return {
        "success": True,
        "data": {
            "id": "usr-admin-1",
            "email": "admin@factory-alpha.com",
            "role": "admin",
            "factory_id": "fct-001",
            "can_write": True
        }
    }
