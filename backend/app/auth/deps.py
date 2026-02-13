from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import settings
from app.models.user import TokenData, User, UserRole
from app.auth.jwt import verify_password, get_password_hash

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# MOCK DATABASE FOR DEV if no DB connected yet
# We will start with a mock user for testing functionality immediately
MOCK_USERS_DB = {
    "admin@example.com": {
        "id": 1,
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin"), # password: admin
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    },
    "user@example.com": {
        "id": 2,
        "email": "user@example.com",
        "hashed_password": get_password_hash("user"), # password: user
        "full_name": "Test User",
        "role": "user",
        "is_active": True
    }
}

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # In a real app, fetch from DB
    user_dict = MOCK_USERS_DB.get(token_data.email)
    if user_dict is None:
        raise credentials_exception
        
    user = User(**user_dict)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")
    return current_user












    
