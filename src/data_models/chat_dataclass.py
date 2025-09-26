from dataclasses import dataclass
from typing import List, Optional, Any, Union, Dict
from datetime import datetime
from enum import Enum
from .base_dataclass import BaseResponse, ResponseMessage
import time
from pydantic import BaseModel
__all__ = [
    'ChatListItem', 'ChatListResponse', 'ChatHistory', 
    'ChatHistoryResponse', 'ChatRequestPayload', 'ChatRequest', 
    'ChatResponsePayload', 'ChatResponse', 'RenameChatRequest'
]
# thêm class vào __all__ mới import * ở __init__.py được
class RenameChatRequest(BaseModel):
    chat_id: str
    new_title: str
@dataclass
class ChatListItem:
    id: str
    title: str
    update_at: str

    @classmethod
    def from_dict(cls, chat_dict: dict):
        return cls(
            id=str(chat_dict['_id']),
            title=chat_dict['title'],
            update_at=chat_dict.get('update_at', int(time.time()))
        )

@dataclass
class ChatListResponse(BaseResponse):
    data: List[ChatListItem]
    total: int = 0

@dataclass
class ChatHistory:
    chat_id: str
    history: List[List[str]]

@dataclass
class ChatHistoryResponse(BaseResponse):
    data: ChatHistory
    total: int = 0


@dataclass
class ChatRequestPayload:
    userId: str
    question: str
    chatId: Optional[str] = ""
    collectionId: Optional[str] = ""

@dataclass
class ChatRequest:
    payload: ChatRequestPayload
    header: Dict[str, Any] = None

@dataclass
class ChatResponsePayload:
    id: str
    answer: str
    source: Optional[List[Dict]] = None

@dataclass
class ChatResponse(BaseResponse):
    header: Dict[str, Any] = None
    payload: Optional[ChatResponsePayload] = None
    code: int = 200
    message: str = "Success"