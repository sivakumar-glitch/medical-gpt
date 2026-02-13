from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.jwt import create_access_token, get_password_hash
from app.auth.deps import MOCK_USERS_DB
from app.models.user import Token, User
from app.core.config import settings

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Admin Login - Strict Check
    if form_data.username == "admin@example.com":
        user_dict = MOCK_USERS_DB.get(form_data.username)
        from app.auth.jwt import verify_password
        if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect admin credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = "admin"
    else:
        # User Login - Allow any email/password
        # In a real app this would be strict too, but for this demo/request we allow any
        role = "user"
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username, "role": role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user():
     raise HTTPException(status_code=501, detail="Registration not implemented in Mock DB mode. Use 'user@example.com' / 'user'")
