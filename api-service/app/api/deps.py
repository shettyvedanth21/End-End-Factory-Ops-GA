from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")

class TokenData(BaseModel):
    sub: Optional[str] = None
    factory_id: Optional[str] = None
    role: Optional[str] = None
    can_write: bool = False

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[security.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(
            sub=user_id,
            factory_id=payload.get("factory_id"),
            role=payload.get("role"),
            can_write=payload.get("can_write", False)
        )
    except JWTError:
        raise credentials_exception
    
    # Check Redis deny-list here (omitted for brevity, but marking place)
    # if is_token_blacklisted(token): raise credentials_exception

    user = db.query(User).filter(User.id == token_data.sub).first()
    if user is None:
        raise credentials_exception
    
    # Validation
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ["platform_root", "super_admin"]:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_factory_id(
    current_user: User = Depends(get_current_active_user)
) -> str:
    if not current_user.factory_id and current_user.role != "platform_root":
         raise HTTPException(status_code=400, detail="User not associated with a factory")
    return current_user.factory_id
