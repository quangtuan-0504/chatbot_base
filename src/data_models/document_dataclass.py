from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


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
class request_getDocs(BaseModel):
    collection_id : str