from pydantic import BaseModel, Field
from typing import Union
from fastapi import FastAPI, HTTPException,Depends, Request,File, Form, UploadFile

class request_AddChat(BaseModel):
    userId: str
    text: str
class request_GetListChat(BaseModel):
    User_id: str
class request_UpdateChat(BaseModel):
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

class request_Login(BaseModel):
    userName: str 
    password: str 
    email: str
    department: str


class request_addDoc(BaseModel):
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    description: str = Form(...)

class request_addUsertoCollection(BaseModel):
    collection_id : str
    user_email : Union[str, None] = None
    department_name : Union[str, None] = None