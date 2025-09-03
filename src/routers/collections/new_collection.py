from fastapi import APIRouter, Depends, HTTPException , Form
from fastapi.responses import JSONResponse
from dataclasses import asdict
from ...tools.load_resources import resource
from src.data_models.collection_dataclass import CreateCollectionRequest
from datetime import datetime , timezone
from ...loggers.logapp import logger
from ...data_models import *

router = APIRouter(
    prefix="/api/collections"
)
@router.post("/new-collection/{userId}")
async def create_collection(userId: str , request: CreateCollectionRequest):
    logger.info(f"Create collection request: {request}")

    try:
        # Validate required fields for create
        if not request.collection_name:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('collection_name')
                )),
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