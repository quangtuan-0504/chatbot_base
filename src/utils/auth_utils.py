from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Annotated
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from src.configs import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(request: Request, token: Annotated[str, Depends(oauth2_scheme)]) -> Dict[str, Any]:
    """Get current user from JWT token"""
    # print("Token:", token)  # Debugging line to print the token
    # print(request.headers)  # Debugging line to print request headers
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token)
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "access":
            raise credentials_exception
            
    except HTTPException:
        raise credentials_exception
    
    # Import here to avoid circular import
    from src.tools.load_resources import resource
    # from tools.load_resources import resource # ko hiểu sao import như này thì resource lại là dict rỗng
    user = resource["user_tool"].get_user_by_email(email)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user - checks if user is active"""
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return current_user

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Require admin role"""
    if current_user.get("system_role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def require_creator_or_admin(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Require creator or admin role"""
    if current_user.get("system_role") not in ["creator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creator or admin access required"
        )
    return current_user

async def require_group_admin(group_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Require group admin role"""
    from src.tools.load_resources import resource
    
    if not resource["group_tool"]._is_admin_gr(current_user["id"], group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Group admin access required"
        )
    return current_user

async def require_group_member(group_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Require group membership"""
    from src.tools.load_resources import resource
    
    if not resource["group_tool"]._is_member_of_group(current_user["id"], group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Group membership required"
        )
    return current_user
