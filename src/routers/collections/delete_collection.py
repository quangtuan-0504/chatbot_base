from fastapi import Form, APIRouter

from ...tools.load_resources import resource
from ...configs import settings
from ...data_models import RemoveCollectionRequest
from ...loggers.logapp import logger
from bson import ObjectId
import shutil
import os



router = APIRouter(
    prefix="/api/collections"
)
@router.put("/delete-collection/{userId}")
async def deleteCollection(userId: str, request: RemoveCollectionRequest):
    logger.info(f"Delete collection request: {request}")
    try: 
        collection_id = request.collection_id
        collection_name = request.collection_name
        db = resource["mongoDB"]
        collection_milvus_table = db["collection"]
        file_table = db["documents"]
        user_collection_table = db["user_collections"]

        # xóa tài liệu của collection bị xóa trong bảng document mongoDB 
        file_del = file_table.delete_many({"collection_id": collection_id})
        print("num file deleted:", file_del.deleted_count)

        # xóa truy cập của người dùng vào collection bị xóa trong bảng user_collection
        user_collection_del = user_collection_table.delete_many({"collection_id": collection_id})
        print("num access deleted:", user_collection_del.deleted_count)
    
        # xóa collection in VectorStore và bảng collection trong mongoDB 
        collection_milvus_table.delete_one({"_id": ObjectId(collection_id)})

        ############
        indexing = resource["indexing"]
        stt_del = indexing.delete_collection(collection_name="hello" + collection_id)# tên của collection trong Vector store là collection id tương ứng trong mongoDB thêm "hello ở đầu"
        print(stt_del)


        # xóa folder chứa file của collection

        if os.path.exists(f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}"):
            shutil.rmtree(f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}")

        # xóa folder chứa ảnh của từng file của collection
        if os.path.exists(f"{settings.PATH_SAVE_IMG_OF_FILE}/hello{collection_id}"):
            shutil.rmtree(f"{settings.PATH_SAVE_IMG_OF_FILE}/hello{collection_id}")
        return {"collection_id": collection_id}
    except Exception as e:
        logger.error(f"Failed to delete collection: {str(e)}")
        return {"error": str(e)}

@router.put("/delete-collection/{userId}")
async def deleteCollection(userId: str, request: RemoveCollectionRequest):
     
    db = resource["mongoDB"]
    collection_milvus_table = db["collection"]
    file_table = db["documents"]
    user_collection_table = db["user_collections"]

    # xóa tài liệu của collection bị xóa trong bảng document mongoDB 
    file_del = file_table.delete_many({"collection_id": collection_id})
    print("num file deleted:", file_del.deleted_count)

    # xóa truy cập của người dùng vào collection bị xóa trong bảng user_collection
    user_collection_del = user_collection_table.delete_many({"collection_id": collection_id})
    print("num access deleted:", user_collection_del.deleted_count)
   
    # xóa collection in VectorStore và bảng collection trong mongoDB 
    collection_milvus_table.delete_one({"_id": ObjectId(collection_id)})

    ############
    indexing = resource["indexing"]
    stt_del = indexing.delete_collection(collection_name="hello" + collection_id)# tên của collection trong Vector store là collection id tương ứng trong mongoDB thêm "hello ở đầu"
    print(stt_del)


    # xóa folder chứa file của collection

    if os.path.exists(f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}"):
        shutil.rmtree(f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}")

    # xóa folder chứa ảnh của từng file của collection
    if os.path.exists(f"{settings.PATH_SAVE_IMG_OF_FILE}/hello{collection_id}"):
        shutil.rmtree(f"{settings.PATH_SAVE_IMG_OF_FILE}/hello{collection_id}")
    return {"collection_id": collection_id}