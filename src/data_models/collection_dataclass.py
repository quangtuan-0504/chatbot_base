from pydantic import BaseModel, Field
from typing import Union
from fastapi import File, Form, UploadFile
from dataclasses import dataclass
from typing import List, Optional, Union
from datetime import datetime
from .base_dataclass import BaseResponse
from src.utils.timezone_utils import format_datetime_gmt7, get_gmt7_datetime_for_db


class CreateCollectionRequest(BaseModel):
    collection_name: str = None
    description: str|None = None
    status: str|None = "active"
    tags: list[str]|None = None
    is_public: bool|None = False
    is_hidden: bool|None = False
class RemoveCollectionRequest(BaseModel):
    collection_id: str = None
    collection_name: str|None = None
class ModifyCollectionRequest(BaseModel):
    collection_id: str
    collection_name: Optional[str]|None = None
    is_public: bool|None = False
    is_hidden: bool|None = False

@dataclass
class CollectionItem:
    collection_id: str
    collection_name: str
    user_id: str  # Creator of the collection (remains unchanged)
    role: str  # Role of the user in relation to the collection (owner, editor, viewer)
    status: str
    created_at: str
    updated_at: str
    # group_id: Optional[str] = None  # Group that owns this collection
    document_count: int = 0
    total_size_bytes: int = 0
    description: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    @classmethod
    def from_dict(cls, collection_dict: dict):
        # Helper function to format timestamp
        def format_timestamp(timestamp_value):
            if isinstance(timestamp_value, str):
                # If it's already a string, try to parse and reformat, or return as-is
                try:
                    # Try to parse ISO format and convert to desired format
                    dt = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    # If parsing fails, return the string as-is
                    return timestamp_value
            elif isinstance(timestamp_value, datetime):
                # If it's a datetime object, format it
                return timestamp_value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # If it's None or other type, use current time
                return format_datetime_gmt7(get_gmt7_datetime_for_db())

        return cls(
            collection_id=str(collection_dict.get('_id', collection_dict.get('id', ''))),
            collection_name=collection_dict.get('collection_name', ''),
            user_id=str(collection_dict.get('user_id', collection_dict.get('user_id_create', ''))),
            role=collection_dict.get('role', 'owner'),
            status=collection_dict.get('status', 'active'),
            created_at=format_timestamp(collection_dict.get('created_at')),
            updated_at=format_timestamp(collection_dict.get('updated_at')),
            # group_id=str(collection_dict.get('group_id')),
            document_count=collection_dict.get('document_count', 0),
            total_size_bytes=collection_dict.get('total_size_bytes', 0),
            description=collection_dict.get('description'),
            tags=collection_dict.get('tags', [])
        )

@dataclass
class CollectionListResponse(BaseResponse):
    data: List[CollectionItem]
    total: int = 0

@dataclass
class CollectionResponse(BaseResponse):
    data: Optional[CollectionItem] = None

class ShareCollectionRequest(BaseModel):
    collection_id: str
    user_email: str
    role: str = "viewer"  # "editor" or "viewer"

class ShareCollectionToGroupRequest(BaseModel):
    collection_id: str
    group_id: str
    role: str = "viewer"  # "editor" or "viewer"

class GetCollectionsCommunityRequest(BaseModel):
    search_name: Optional[str] = None

class GetCollectionsAccessRequest(BaseModel):
    collection_name: str
    roles: List|None = ["editor", "viewer"]

class ViewAllCollectionsRequest(BaseModel):
    collection_name: Optional[str] = None
    status: Optional[str] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
