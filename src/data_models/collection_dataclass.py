from pydantic import BaseModel, Field
from typing import Union
from fastapi import File, Form, UploadFile

class CreateCollectionRequest(BaseModel):
    collection_name: str|None = None
    description: str|None = None

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