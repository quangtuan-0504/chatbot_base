from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class UserRegistrationRequest:
    email: str
    password: str
    username: Optional[str] = None
    name: Optional[str] = None

@dataclass
class LoginRequest:
    email_or_username: str
    password: str

@dataclass
class RefreshTokenRequest:
    refresh_token: str

@dataclass
class ResetPasswordRequest:
    current_password: str
    new_password: str

@dataclass
class UpdateProfileRequest:
    email: Optional[str] = None
    name: Optional[str] = None

@dataclass
class ViewUsersRequest:
    name_filter: Optional[str] = None
    email_filter: Optional[str] = None
    page: int = 1
    limit: int = 10

@dataclass
class GrantRoleRequest:
    user_id: str
    system_role: str  # "admin" | "creator" | "user"

@dataclass
class EnableDisableUserRequest:
    user_id: str

@dataclass
class UserItem:
    id: str
    email: str
    username: str
    name: str
    system_role: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'UserItem':
        return cls(
            id=str(data.get('_id', data.get('id', ''))),
            email=data.get('email', ''),
            username=data.get('username', ''),
            name=data.get('name', ''),
            system_role=data.get('system_role', 'user'),
            is_active=data.get('is_active', True),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            last_login=data.get('last_login')
        )

@dataclass
class TokenData:
    access_token: str
    refresh_token: str
    token_type: str
    user: UserItem

@dataclass
class UserResponse:
    code: int
    data: UserItem
    message: str

@dataclass
class LoginResponse:
    code: int
    data: TokenData
    message: str

@dataclass
class TokenRefreshResponse:
    code: int
    data: TokenData
    message: str

@dataclass
class UserListResponse:
    code: int
    data: List[UserItem]
    total: int
    page: int
    limit: int
    message: str
