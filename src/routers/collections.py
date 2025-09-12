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
    
@router.post('/modify')
async def modify_collection(
    request: ModifyCollectionRequest,
):
    """Modify an existing collection. Can change name and/or group assignment."""
    logger.debug(f"Modify collection request: {request}")
    try:
        if not request:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('request data')
                )),
                status_code=400
            )

        if not request.collection_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('collection_id')
                )),
                status_code=400
            )

        response_data = None

        # Handle collection name change
        if request.collection_name:
            try:
                response_data = resource['collection_tool'].change_collection_name(
                    collection_id=request.collection_id,
                    collection_name=request.collection_name
                )
                logger.info(f"Collection name changed: {request.collection_id} -> {request.collection_name}")
            except ValueError as ve:
                return JSONResponse(
                    content=asdict(BaseResponse(
                        code=404,
                        message=str(ve)
                    )),
                    status_code=404
                )

        collection_item = CollectionItem.from_dict(response_data)

        return asdict(CollectionResponse(
            code=200,
            data=collection_item,
            message=ResponseMessage.UPDATE_SUCCESS
        ))
    except Exception as e:
        logger.error(f"Modify collection error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.put("/delete-collection/{userId}")
async def delete_collection(userId: str, request: RemoveCollectionRequest):
    logger.info(f"Delete collection request: {request}")
    try: 
        if not request.collection_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('collection_id')
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

@router.post("/get-list-collections/{userId}")
async def get_collections_of_user(userId: str, request: GetCollectionsRequest):
    logger.debug(f"Get all collections for user:{userId}")
    try:

        collections_data = resource['collection_tool'].get_collections_by_userid(
            user_id=userId,
            roles=request.roles
        )

        collection_items = [CollectionItem.from_dict(collection) for collection in collections_data]
        response = CollectionListResponse(
            data=collection_items,
            total=len(collection_items)
        )

        return asdict(response)

    except Exception as e:
        logger.error(f"Get all collections error for user: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )