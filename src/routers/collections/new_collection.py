from fastapi import APIRouter, Depends, HTTPException , Form
from ...tools.load_resources import resource
from src.data_models.collection_dataclass import CreateCollectionRequest
from datetime import datetime , timezone
from ...loggers.logapp import logger

router = APIRouter(
    prefix="/api/collections"
)
@router.post("/new-collection/{userId}")
async def create_collection(userId: str , request: CreateCollectionRequest):
    logger.info(f"Create collection request: {request}")

    try:
        collection_name = request.collection_name
        description = request.description
        status = request.status
        tags = request.tags

        create_res = resource["collection_tool"].create_collection(
            indexing_milvus=resource["indexing"],
            collection_name=collection_name,
            user_id=userId,
            status=status,
            description=description,
            tags=tags
        )
        return create_res
    except Exception as e:
        logger.error(f"Failed to create collection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create collection")

@router.post("/new-collection/{userId}")
async def create_collection(userId: str , request: CreateCollectionRequest):
    logger.info(f"Create collection request: {request}")
    collection_name = request.collection_name
    db = resource["mongoDB"]
    collection_table = db['collection']
    check_collection_exits = collection_table.find_one({"collection_name": collection_name})
    # Nếu collection chưa tồn tại, thêm mới
    if not check_collection_exits:
        
        # thêm trong mongoDB 
        collection_new = collection_table.insert_one({
                    "collection_name": collection_name,
                    "user_id_create": userId,
                    "createAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "updateAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # thêm phân quyền collection vừa tạo cho người tạo 
        collection_id=str(collection_new.inserted_id)
        user_collection = db["user_collections"]
        new_user_collection = user_collection.insert_one({"user_id": userId,
                                                          "collection_id":collection_id })
        # thêm trong qdrant
        indexing = resource["indexing"]
        stt=indexing.create_collection(collection_name="hello"+collection_id)
        print(stt)


        return "create collection successfully"
    else:
        print("Collection already exists")
        raise HTTPException(status_code=500, detail="Collection already exists")