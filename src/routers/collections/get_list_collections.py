from fastapi import APIRouter, Depends, HTTPException 
from bson import ObjectId
from ...tools.load_resources import resource


router = APIRouter(
    prefix="/api/collections"
)
@router.get("/get-list-collections/{userId}")
async def get_collections_of_user(userId: str):
    print(userId)
    db = resource["mongoDB"]
    milvus_collection_table = db["collection"]
    user_collection_table = db["user_collections"]
    lst_collection = user_collection_table.find({"userId" :userId})

    if lst_collection :
        lst=[]
        for collection in lst_collection:
            re = milvus_collection_table.find_one({"_id": ObjectId(collection["collection_id"])})

            lst.append({"collection_id": collection["collection_id"],
                        "collection_name": re["collection_name"]})
            
        return lst
    else:
        return []