from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import os


import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from src.tools.load_resources import resourcelifespan
# from tools.load_resources import resourcelifespan # nếu để vậy thì không hiểu sao bên routers/chats.py print resource ra bị rỗng.
from src.routers.chats import router as chat_router
from src.routers.documents import router as document_router
from src.routers.collections import router as collection_router
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

api_router = APIRouter(prefix="/api/v1")
app.include_router(api_router)
# Include routers
api_router.include_router(chat_router, prefix="/chats", tags=["chats"])
api_router.include_router(collection_router, prefix="/collections", tags=["collections"])
api_router.include_router(document_router, prefix="/documents", tags=["documents"])

app.include_router(add_user_to_collection.router)


  
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)

# python src/main.py
# uvicorn src.main:app --host 0.0.0.0 --port 8050