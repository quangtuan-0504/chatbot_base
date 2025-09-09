from pydantic import BaseModel, Field
from datetime import datetime
from dataclasses import dataclass, fields
from typing import List, Optional, Any, Union, Dict
from datetime import datetime
from enum import Enum
from .base_dataclass import BaseResponse, ResponseMessage
from src.utils.timezone_utils import format_datetime_gmt7, get_gmt7_datetime_for_db



class ChatHistoryItem(BaseModel):
    role: str
    text: str
    img: Optional[str] =None

class Chat(BaseModel):
    userId: str
    history: list[ChatHistoryItem] = []

class UserChatItem(BaseModel):
    _id: str
    title: str
    createAt: Optional[str] = datetime.today().strftime("%d/%m/%Y")
class UserColelctionItem(BaseModel):
    _id: str
    collection_name: str
    createAt: Optional[str] = datetime.today().strftime("%d/%m/%Y")

class UserChatsCollections(BaseModel):
    userId: str
    chats: list[UserChatItem] = []
    collections : list[UserColelctionItem] = []

class User(BaseModel):# trong tutorial là nó dùng API của bên thứ 3 để lưu thông tin người dùng nên không cần bảng User,
    # mình không muốn dùng bên thứ 3 thì mình phải có bảng user để lưu thông tin người dùng.
    userName: str # tên tài khoản
    password: str # mật khẩu
    email: str # email khôi phục
    department: str

# Pydantic model for request validation
class FilesQueryRequest(BaseModel):
    collection_id: str
    file_types: Optional[List[str]] = None
    status: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
class DeleteFileRequest(BaseModel):
    collection_id: str
    file_id: str
 
 

@dataclass
class FileItem:
    file_id: str  # MongoDB _id
    file_name: str
    file_type: str
    status: str
    user_id: str
    collection_id: str
    created_at: str
    updated_at: str
    process_result: str
    @classmethod
    def from_dict(cls, file_dict: dict):
        return cls(
            file_id=str(file_dict.get('file_id', '')),
            file_name=file_dict.get('file_name', ''),
            file_type=file_dict.get('file_type', ''),
            status=file_dict.get('status', 'pending'),
            process_result= file_dict.get('result', ''),
            user_id=file_dict.get('user_id', ''),
            collection_id=file_dict.get('collection_id', ''),
            created_at=format_datetime_gmt7(file_dict.get('created_at', get_gmt7_datetime_for_db()), '%d/%m/%Y %H:%M:%S'),
            updated_at=format_datetime_gmt7(file_dict.get('updated_at', get_gmt7_datetime_for_db()), '%d/%m/%Y %H:%M:%S')
        )

    def asdict(self):
        """Convert dataclass to dictionary with camelCase keys"""
        result = {}
        for field in fields(self):
            value = getattr(self, field.name)
            parts = field.name.split('_')
            camel_key = parts[0] + ''.join(part.capitalize() for part in parts[1:])
            result[camel_key] = value
        return result

@dataclass
class FileListResponse(BaseResponse):
    data: List[FileItem]
    total: int = 0

@dataclass
class FileResponse(BaseResponse):
    data: Optional[FileItem] = None

@dataclass
class FileUploadRequest:
    filename: str
    file_type: str
    user_id: str
    collection_id: str
    file_id: Optional[str] = None

@dataclass
class FileStatusUpdateRequest:
    file_id: str
    status: str

@dataclass
class FileProcessingResponse(BaseResponse):
    data: Dict[str, Any] = None

@dataclass
class FileSearchRequest:
    user_id: Optional[str] = None
    collection_id: Optional[str] = None
    file_type: Optional[str] = None
    status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None