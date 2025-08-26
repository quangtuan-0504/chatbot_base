from fastapi import Form, APIRouter
from ..tools.load_resources import resource
from ..configs import settings
from bson import ObjectId
import shutil
import os



router = APIRouter(
    prefix="/api"
)

@router.put("/delete-file/{userId}")
async def deleteDoc(userId: str, collection_id: str = Form(...),file_id : str = Form(...),file_path : str = Form(...), file_name : str = Form(...)):

    db = resource["mongoDB"]
    file_table = db["documents"]
    # 1. Xóa cả trong thư mục lưu trữ file
    if os.path.exists(file_path):
        os.remove(file_path)

    # 2. Xóa trong mongoDB
    file_table.delete_one({"_id": ObjectId(file_id)})

    # 3. Xóa trong VectorStore
    # stt = delete_file_in_collection_qdrant(file_name=file_name)
    # print(stt)
    ############
    indexing = resource["indexing"]
    stt = indexing.delete_file(collection_name="hello" + collection_id, file_name=file_name)
    print(stt)

    # 4. Xóa các ảnh liên quan đến file
    if os.path.exists(f"{settings.PATH_SAVE_IMG_OF_FILE}/hello{collection_id}/{file_name}"):
        os.remove(f"{settings.PATH_SAVE_IMG_OF_FILE}/hello{collection_id}/{file_name}")
    return {"collection_id": collection_id, "file_id": file_id}