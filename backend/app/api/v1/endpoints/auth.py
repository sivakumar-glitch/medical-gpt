from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.jwt import create_access_token, verify_password
from app.auth.deps import MOCK_USERS_DB
from app.models.user import Token, User
from app.core.config import settings

router = APIRouter()

ALLOWED_LOGINS = {"user@example.com", "admin@example.com"}

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username.strip().lower()
    if username not in ALLOWED_LOGINS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only allowed users can log in",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_dict = MOCK_USERS_DB.get(username)
    if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    role = user_dict.get("role", "user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "role": role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user():
     raise HTTPException(status_code=501, detail="Registration not implemented in Mock DB mode. Use one of the seeded accounts: admin@example.com/admin or user@example.com/user")
