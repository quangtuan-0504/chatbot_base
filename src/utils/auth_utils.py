from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Annotated
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

import os
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
        # print("Payload:", payload)  # Debugging line to print the payload
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except HTTPException:
        raise credentials_exception
    
    # Import here to avoid circular import
    from src.tools.load_resources import resource
    # from tools.load_resources import resource # ko hiểu sao import như này thì resource lại là dict rỗng
    user = resource["user_tool"].get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user
async def get_current_user_ws(token: str):
    """Xác thực user từ token cho WebSocket"""
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Import here to avoid circular import
        from src.tools.load_resources import resource
        user = resource["user_tool"].get_user_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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

async def require_collection_owner(collection_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Require collection owner role"""
    from src.tools.load_resources import resource
    
    # Check if user is owner in USER_COLLECTION table
    user_collection = resource["mongoDB"].USER_COLLECTION.find_one({
        "user_id": current_user["id"],
        "collection_id": collection_id,
        "role": "owner"
    })
    
    if not user_collection:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Collection owner access required"
        )
    return current_user

async def require_collection_editor_or_owner(collection_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Require collection editor or owner role"""
    from src.tools.load_resources import resource
    
    # Check if user has editor or owner role
    user_collection = resource["mongoDB"].USER_COLLECTION.find_one({
        "user_id": current_user["id"],
        "collection_id": collection_id,
        "role": {"$in": ["owner", "editor"]}
    })
    
    if not user_collection:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Collection editor or owner access required"
        )
    return current_user

async def require_collection_access(collection_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Require any level of collection access (owner, editor, or viewer)"""
    from src.tools.load_resources import resource
    
    # Check if user has any access to collection
    user_collection = resource["mongoDB"].USER_COLLECTION.find_one({
        "user_id": current_user["id"],
        "collection_id": collection_id
    })
    
    # Also check if collection is public
    collection = resource["collection_tool"].get_collection_by_id(collection_id)
    
    if not user_collection and not collection.get("is_public", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Collection access required"
        )
    return current_user
