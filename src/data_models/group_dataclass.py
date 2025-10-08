from dataclasses import dataclass
from typing import Optional, List
from .base_dataclass import BaseResponse

@dataclass
class GroupItem:
    id: str
    group_name: str
    description: str
    manager_id: str
    is_public: bool
    is_hidden: bool
    num_member: int
    created_at: str
    updated_at: str
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id", ""),
            group_name=data.get("group_name", ""),
            description=data.get("description", ""),
            manager_id=data.get("manager_id", ""),
            is_public=data.get("is_public", False),
            is_hidden=data.get("is_hidden", False),
            num_member=data.get("num_member", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

@dataclass
class UserGroupItem:
    id: str
    user_id: str
    group_id: str
    role: str
    assigned_by: str
    assigned_at: str
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id", ""),
            user_id=data.get("user_id", ""),
            group_id=data.get("group_id", ""),
            role=data.get("role", ""),
            assigned_by=data.get("assigned_by", ""),
            assigned_at=data.get("assigned_at", "")
        )

@dataclass
class CreateGroupRequest:
    group_name: str
    description: str = ""
    is_public: bool = False
    is_hidden: bool = False

@dataclass
class ModifyGroupRequest:
    group_id: str
    group_name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_hidden: Optional[bool] = None

@dataclass
class AddMemberRequest:
    group_id: str
    email: str

@dataclass
class RemoveMemberRequest:
    group_id: str
    email: str

@dataclass
class ViewUsersInGroupRequest:
    group_id: str

@dataclass
class ViewAllGroupsRequest:
    group_name_filter: Optional[str] = None
    num_member_filter: Optional[int] = None
    page: int = 1
    limit: int = 10

@dataclass
class RemoveGroupRequest:
    group_id: str

@dataclass
class GroupResponse(BaseResponse):
    data: Optional[GroupItem] = None

@dataclass
class GroupListResponse(BaseResponse):
    data: List[GroupItem]
    total: int = 0
    page: int =  1
    limit: int = 10

@dataclass
class UserListInGroupResponse(BaseResponse):
    data: List[dict]  # Contains user info with name and email only

class GetListGroupYouCreatedRequest:
    group_name: Optional[str] = None
class GetListGroupYouJoinedRequest:
    group_name: Optional[str] = None
class GetListGroupCommunityRequest:
    group_name: Optional[str] = None