from fastapi import APIRouter, Depends, HTTPException , Form
from fastapi.responses import JSONResponse
from dataclasses import asdict
from ..tools.load_resources import resource
from src.data_models.collection_dataclass import (
    CreateCollectionRequest, RemoveCollectionRequest, ModifyCollectionRequest,
    ShareCollectionRequest, ShareCollectionToGroupRequest,
    GetCollectionsCommunityRequest, ViewAllCollectionsRequest, GetCollectionsAccessRequest
)
from src.utils.auth_utils import (
    get_current_active_user, require_creator_or_admin, require_admin,
    require_collection_owner, require_collection_access
)
from ..loggers.logapp import logger
from ..data_models import *


router = APIRouter()

@router.post("/new-collection")
async def create_new_collection(
    request: CreateCollectionRequest,
    current_user: dict = Depends(require_creator_or_admin)
):
    logger.info(f"Create collection request: {request}")

    try:
        if not request.collection_name:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('collection_name')
                )),
                status_code=400
            )

        response_data = resource["collection_tool"].create_collection(
            indexing_milvus=resource["indexing"],
            collection_name=request.collection_name,
            user_id=current_user["id"],
            status=request.status or "active",
            description=request.description,
            tags=request.tags,
            is_public=request.is_public or False,
            is_hidden=request.is_hidden or False
        )
        
        collection_item = CollectionItem.from_dict(response_data)
        return asdict(CollectionResponse(
            code=200,
            data=collection_item,
            message=ResponseMessage.CREATE_SUCCESS
        ))
    except Exception as e:
        logger.error(f"Failed to create collection: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post('/modify-collection')
async def modify_collection(
    request: ModifyCollectionRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Modify an existing collection. Owner can change name, description, visibility settings."""
    logger.debug(f"Modify collection request: {request}")
    
    try:
        if not request.collection_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('collection_id')
                )),
                status_code=400
            )

        # Check if user is owner
        await require_collection_owner(request.collection_id, current_user)

        # Prepare updates
        updates = {}
        if request.collection_name:
            updates["collection_name"] = request.collection_name
        if request.is_public is not None:
            updates["is_public"] = request.is_public
        if request.is_hidden is not None:
            updates["is_hidden"] = request.is_hidden

        response_data = resource['collection_tool'].update_collection_settings(
            collection_id=request.collection_id,
            **updates
        )

        collection_item = CollectionItem.from_dict(response_data)
        return asdict(CollectionResponse(
            code=200,
            data=collection_item,
            message=ResponseMessage.UPDATE_SUCCESS
        ))
    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(code=404, message=str(ve))),
            status_code=404
        )
    except Exception as e:
        logger.error(f"Modify collection error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/get-list-collection-you-created")
async def get_collections_you_created(
    current_user: dict = Depends(get_current_active_user)
):
    """Get collections created by current user"""
    try:
        collections_data = resource['collection_tool'].get_collections_created_by_user(
            user_id=current_user["id"]
        )

        collection_items = [CollectionItem.from_dict(collection) for collection in collections_data]
        return asdict(CollectionListResponse(
            data=collection_items,
            total=len(collection_items)
        ))

    except Exception as e:
        logger.error(f"Get created collections error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/get-list-collection-shared-you")
async def get_collections_shared_with_you(
    request: GetCollectionsAccessRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Get collections shared with current user (editor/viewer role)"""
    try:
        collections_data = resource['collection_tool'].get_collections_shared_with_user(
            user_id=current_user["id"],
            collection_name=request.collection_name,
            roles=request.roles
        )

        collection_items = [CollectionItem.from_dict(collection) for collection in collections_data]
        return asdict(CollectionListResponse(
            data=collection_items,
            total=len(collection_items)
        ))

    except Exception as e:
        logger.error(f"Get shared collections error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/get-list-collection-community")
async def get_community_collections(
    request: GetCollectionsCommunityRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Get public collections that are not hidden"""
    try:
        collections_data = resource['collection_tool'].get_community_collections(
            search_name=request.search_name
        )

        collection_items = [CollectionItem.from_dict(collection) for collection in collections_data]
        return asdict(CollectionListResponse(
            data=collection_items,
            total=len(collection_items)
        ))

    except Exception as e:
        logger.error(f"Get community collections error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/admin/view-all-collections")
async def view_all_collections(
    request: ViewAllCollectionsRequest,
    current_user: dict = Depends(require_admin)
):
    """Admin endpoint to view all collections"""
    try:
        filters = {}
        if request.status:
            filters["status"] = request.status
        if request.created_after:
            filters["created_at"] = {"$gte": request.created_after}
        if request.created_before:
            filters["created_at"] = {"$lte": request.created_before}

        collections_data = resource['collection_tool'].get_all_collections_admin(
            collection_name=request.collection_name,
            **filters
        )

        collection_items = [CollectionItem.from_dict(collection) for collection in collections_data]
        return asdict(CollectionListResponse(
            data=collection_items,
            total=len(collection_items)
        ))

    except Exception as e:
        logger.error(f"Admin view all collections error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/share")
async def share_collection_with_user(
    request: ShareCollectionRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Share collection with a specific user via email"""
    try:
        # Check if user is owner
        await require_collection_owner(request.collection_id, current_user)

        result = resource['collection_tool'].share_collection_with_user(
            collection_id=request.collection_id,
            user_email=request.user_email,
            role=request.role,
            assigned_by=current_user["id"]
        )

        return asdict(BaseResponse(
            code=200,
            message=f"Collection shared successfully. Action: {result['action']}"
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(code=404, message=str(ve))),
            status_code=404
        )
    except Exception as e:
        logger.error(f"Share collection error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/shares")
async def share_collection_with_group(
    request: ShareCollectionToGroupRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Share collection with all members of a group"""
    try:
        # Check if user is owner
        await require_collection_owner(request.collection_id, current_user)

        results = resource['collection_tool'].share_collection_with_group(
            collection_id=request.collection_id,
            group_id=request.group_id,
            role=request.role,
            assigned_by=current_user["id"]
        )

        created_count = sum(1 for r in results if r["action"] == "created")
        updated_count = sum(1 for r in results if r["action"] == "updated")
        existing_count = sum(1 for r in results if r["action"] == "already_exists")

        return asdict(BaseResponse(
            code=200,
            message=f"Collection shared with group. Created: {created_count}, Updated: {updated_count}, Already exists: {existing_count}"
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(code=404, message=str(ve))),
            status_code=404
        )
    except Exception as e:
        logger.error(f"Share collection with group error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/delete-collection")
async def delete_collection(
    request: RemoveCollectionRequest,
    current_user: dict = Depends(get_current_active_user)
):
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
        
        # Check if user is owner
        await require_collection_owner(request.collection_id, current_user)

        response_data = resource['collection_tool'].remove_collection(
            indexing_milvus=resource['indexing'],
            collection_id=request.collection_id,
            user_id=current_user["id"],
            role="owner"
        )
        
        return asdict(CollectionResponse(
            code=200,
            data=CollectionItem.from_dict(response_data) if response_data else None,
            message=ResponseMessage.DELETE_SUCCESS
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(code=404, message=str(ve))),
            status_code=404
        )
    except RuntimeError as re:
        logger.error(f"Remove collection: {str(re)}")
        return JSONResponse(
            content=asdict(BaseResponse(code=500, message=str(re))),
            status_code=500
        )
    except Exception as e:
        logger.error(f"Remove collection error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )