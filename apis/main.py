from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os


import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from src.tools.load_resources import resourcelifespan
# from tools.load_resources import resourcelifespan # nếu để vậy thì không hiểu sao bên routers/chats.py print resource ra bị rỗng.
from src.routers.chats import chats
from src.routers.documents import (
    add_doc,
    delete_doc,
    download_file
)
from src.routers.collections import ( 
    delete_collection,
    get_list_collections,
    get_lst_doc_in_collection,
    new_collection
)
from src.routers.shares import add_user_to_collection

from loggers.logapp import logger
from configs import settings

logger.info(" Starting FastAPI application...")

app = FastAPI(
    title=settings.app_name,
    lifespan=resourcelifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn gốc. Bạn có thể giới hạn lại theo nhu cầu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # Quan trọng: Cho phép header này hiển thị
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/sign-up") 
async def add_user():
    return "add user successfully!"

@app.post("/log-in")
async def check_user():
    return "Log-in sucessfully!"
@app.put("/reset_password")
async def resetpass():
    return "Reset pass successfully!"
@app.post("/log-out")
async def logout():
    return "Logout Successfully!"
@app.get("/api/getListDepartment/{userId}")
async def get_department(userId: str):
    lst_depart = ["depart 1","depart 2","depart 3","depart 4","depart 5"]
    return lst_depart


app.include_router(chats.router)
app.include_router(new_collection.router)
app.include_router(add_doc.router)
app.include_router(delete_collection.router)
app.include_router(delete_doc.router)
app.include_router(download_file.router)
app.include_router(get_list_collections.router)
app.include_router(get_lst_doc_in_collection.router)
app.include_router(add_user_to_collection.router)


  
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)

# python src/main.py
# uvicorn src.main:app --host 0.0.0.0 --port 8050