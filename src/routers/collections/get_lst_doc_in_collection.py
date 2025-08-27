from fastapi import APIRouter, Depends, HTTPException
from ...tools.load_resources import resource
from src.schemas.model_request import request_getDocs



router = APIRouter(
    prefix="/api"
)
@router.post("/get-list-docs-collections/{userId}")
async def get_documents_of_collection(
    userId: str , 
    request : request_getDocs
):
    collection_id = request.collection_id

    db = resource["mongoDB"]

    doc_collection = db["documents"]
    lst_doc = []
    for doc in doc_collection.find({"collection_id": collection_id}):
        lst_doc.append({"doc_id": str(doc["_id"]),
                        "file_name": doc["file_name"],
                        "description": doc["description"],
                        "path": doc["path"],
                        "size" : doc["size"],
                        "type": doc["type"]})
    return lst_doc