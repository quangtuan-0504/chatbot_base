from pydantic import BaseModel
from typing import Union

class GetChatRequest(BaseModel):
    userId: str

class AddChatRequest(BaseModel):
    userId: str
    text: str
class GetListChatRequest(BaseModel):
    User_id: str
class UpdateChatRequest(BaseModel):
    userId : str
    question: Union[str ,None]
    answer:  str = "ngủ rồi"
    source: list = []

class request_Chat(BaseModel):
    userId : str
    collection_name_inVS : str|None = None
    question: str
    chatId : str | None = None
    fileNames : list | None = None
    sysMode: Union[str, None] = None
    LLM: Union[str, None] = None
    searchMode: Union[str, None] = None