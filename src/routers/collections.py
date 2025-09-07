from fastapi import APIRouter, Depends, HTTPException , Form
from fastapi.responses import JSONResponse
from dataclasses import asdict
from ..tools.load_resources import resource
from src.data_models.collection_dataclass import CreateCollectionRequest
from ..loggers.logapp import logger
from ..data_models import *


router = APIRouter()
@router.post("/new-collection/{userId}")
async def create_collection(userId: str , request: CreateCollectionRequest):
    logger.info(f"Create collection request: {request}")

    try:
        # Validate required fields for create
        if not request.collection_name:
            return JSONResponse(
                content=asdict(
                    BaseResponse(
                        code=400,
                        message=ResponseMessage.missing_field('collection_name')
                    )
                ),
                status_code=400
            )
        collection_name = request.collection_name
        description = request.description
        status = request.status
        tags = request.tags

        response_data = resource["collection_tool"].create_collection(
            indexing_milvus=resource["indexing"],
            collection_name=collection_name,
            user_id=userId,
            status=status,
            description=description,
            tags=tags
        )
        collection_item = CollectionItem.from_dict(response_data)
        return asdict(CollectionResponse(
            code=200,
            data=collection_item,
            message=ResponseMessage.CREATE_SUCCESS
        ))
    except Exception as e:
        logger.error(f"Failed to create collection: {str(e)}")
        # raise HTTPException(status_code=500, detail="Failed to create collection")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )


@router.put("/delete-collection/{userId}")
async def deleteCollection(userId: str, request: RemoveCollectionRequest):
    logger.info(f"Delete collection request: {request}")
    try: 
        if not request.collection_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('collectionId')
                )),
                status_code=400
            )
        try:
            response_data = resource['collection_tool'].remove_collection(
                indexing_milvus=resource['indexing'],
                collection_id=request.collection_id,
                user_id=userId
                # role = ""
            )
            return asdict(CollectionResponse(
                code=200,
                data=CollectionItem.from_dict(response_data) if response_data else None,
                message=ResponseMessage.DELETE_SUCCESS
            ))

        except ValueError as ve:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=404,
                    message=str(ve)
                )),
                status_code=404
            )

        except RuntimeError as re:
            logger.error(f"Remove collection: {str(re)}")
            raise RuntimeError(f"Failed to remove collection: {str(re)}")

    except Exception as e:
        logger.error(f"Remove collection error: {str(e)}\n")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
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