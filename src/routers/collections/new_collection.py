from fastapi import APIRouter, Depends, HTTPException , Form
from ...tools.load_resources import resource
from src.data_models.collection_dataclass import CreateCollectionRequest
from datetime import datetime , timezone

router = APIRouter(
    prefix="/api"
)

@router.post("/new-collection/{userId}")
async def create_collection(userId: str , request: CreateCollectionRequest):

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
        new_user_collection = user_collection.insert_one({"userId": userId,
                                                          "collection_id":collection_id })
        # thêm trong qdrant
        indexing = resource["indexing"]
        stt=indexing.create_collection(collection_name="hello"+collection_id)
        print(stt)


        return "create collection successfully"
    else:
        print("Collection already exists")
        raise HTTPException(status_code=500, detail="Collection already exists")