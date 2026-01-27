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
from src.routers.auth import router as auth_router
from src.routers.users import router as user_router
from src.routers.groups import router as group_router

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
    return {"message": f"welcome to {settings.app_name} API!"}


api_router = APIRouter(prefix="/api/v1")
# Include routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(group_router, prefix="/groups", tags=["groups"])
api_router.include_router(chat_router, prefix="/chats", tags=["chats"])
api_router.include_router(collection_router, prefix="/collections", tags=["collections"])
api_router.include_router(document_router, prefix="/documents", tags=["documents"])
app.include_router(api_router)


  
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)

# python src/main.py
# uvicorn src.main:app --host 0.0.0.0 --port 8050