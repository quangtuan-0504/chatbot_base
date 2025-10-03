from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from dataclasses import asdict
from ..tools.load_resources import resource
from ..data_models.group_dataclass import *
from ..data_models import BaseResponse, ResponseMessage
from ..utils.auth_utils import get_current_active_user, require_admin, require_creator_or_admin
from ..loggers.logapp import logger

router = APIRouter()

@router.post("/create-group", response_model=dict)
async def create_group(
    request: CreateGroupRequest,
    current_user: dict = Depends(require_creator_or_admin)
):
    """Create a new group (creator or admin only)"""
    try:
        if not request.group_name:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('group_name')
                )),
                status_code=400
            )

        group_data = resource["group_tool"].create_group(
            group_name=request.group_name,
            manager_id=current_user["id"],
            description=request.description,
            is_public=request.is_public,
            is_hidden=request.is_hidden
        )

        return asdict(GroupResponse(
            code=200,
            data=GroupItem.from_dict(group_data),
            message="Group created successfully"
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=400,
                message=str(ve)
            )),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Create group error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/modify-group", response_model=dict)
async def modify_group(
    request: ModifyGroupRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Modify group information (admin_gr only)"""
    try:
        if not request.group_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('group_id')
                )),
                status_code=400
            )

        updated_group = resource["group_tool"].modify_group(
            group_id=request.group_id,
            user_id=current_user["id"],
            group_name=request.group_name,
            description=request.description,
            is_public=request.is_public,
            is_hidden=request.is_hidden
        )

        return asdict(GroupResponse(
            code=200,
            data=GroupItem.from_dict(updated_group),
            message="Group modified successfully"
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=400,
                message=str(ve)
            )),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Modify group error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/get-list-group-you-created", response_model=dict)
async def get_list_group_you_created(
    current_user: dict = Depends(get_current_active_user)
):
    """Get list of groups created by current user"""
    try:
        groups = resource["group_tool"].get_groups_created_by_user(current_user["id"])
        group_items = [GroupItem.from_dict(group) for group in groups]

        return asdict(GroupListResponse(
            code=200,
            data=group_items,
            total=len(group_items),
            page=1,
            limit=len(group_items),
            message="Groups retrieved successfully"
        ))

    except Exception as e:
        logger.error(f"Get groups created error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/get-list-group-shared-you", response_model=dict)
async def get_list_group_shared_you(
    current_user: dict = Depends(get_current_active_user)
):
    """Get list of groups shared with current user"""
    try:
        groups = resource["group_tool"].get_groups_shared_with_user(current_user["id"])
        group_items = [GroupItem.from_dict(group) for group in groups]

        return asdict(GroupListResponse(
            code=200,
            data=group_items,
            total=len(group_items),
            page=1,
            limit=len(group_items),
            message="Shared groups retrieved successfully"
        ))

    except Exception as e:
        logger.error(f"Get shared groups error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/get-list-group-community", response_model=dict)
async def get_list_group_community(
    current_user: dict = Depends(get_current_active_user)
):
    """Get list of public groups (is_hidden=False)"""
    try:
        groups = resource["group_tool"].get_community_groups()
        group_items = [GroupItem.from_dict(group) for group in groups]

        return asdict(GroupListResponse(
            code=200,
            data=group_items,
            total=len(group_items),
            page=1,
            limit=len(group_items),
            message="Community groups retrieved successfully"
        ))

    except Exception as e:
        logger.error(f"Get community groups error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/admin/view-all-groups", response_model=dict)
async def view_all_groups(
    request: ViewAllGroupsRequest,
    current_user: dict = Depends(require_admin)
):
    """View all groups (admin only)"""
    try:
        groups_data = resource["group_tool"].get_all_groups(
            group_name_filter=request.group_name_filter,
            num_member_filter=request.num_member_filter,
            page=request.page,
            limit=request.limit
        )

        group_items = [GroupItem.from_dict(group) for group in groups_data["groups"]]

        return asdict(GroupListResponse(
            code=200,
            data=group_items,
            total=groups_data["total"],
            page=request.page,
            limit=request.limit,
            message="Groups retrieved successfully"
        ))

    except Exception as e:
        logger.error(f"View all groups error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/add-member", response_model=dict)
async def add_member(
    request: AddMemberRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Add member to group"""
    try:
        if not request.group_id or not request.email:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('group_id or email')
                )),
                status_code=400
            )

        result = resource["group_tool"].add_member(
            group_id=request.group_id,
            email=request.email,
            assigned_by=current_user["id"]
        )

        return asdict(BaseResponse(
            code=200,
            message=result["message"]
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=400,
                message=str(ve)
            )),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Add member error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/remove-member", response_model=dict)
async def remove_member(
    request: RemoveMemberRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Remove member from group (admin_gr only)"""
    try:
        if not request.group_id or not request.email:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('group_id or email')
                )),
                status_code=400
            )

        result = resource["group_tool"].remove_member(
            group_id=request.group_id,
            email=request.email,
            removed_by=current_user["id"]
        )

        return asdict(BaseResponse(
            code=200,
            message=result["message"]
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=400,
                message=str(ve)
            )),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Remove member error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/view-users-in-group", response_model=dict)
async def view_users_in_group(
    request: ViewUsersInGroupRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """View users in group (members only)"""
    try:
        if not request.group_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('group_id')
                )),
                status_code=400
            )

        users = resource["group_tool"].get_users_in_group(
            group_id=request.group_id,
            user_id=current_user["id"]
        )

        return asdict(UserListInGroupResponse(
            code=200,
            data=users,
            message="Users retrieved successfully"
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=400,
                message=str(ve)
            )),
            status_code=400
        )
    except Exception as e:
        logger.error(f"View users in group error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/remove-group", response_model=dict)
async def remove_group(
    request: RemoveGroupRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Remove group (admin_gr only)"""
    try:
        if not request.group_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('group_id')
                )),
                status_code=400
            )

        result = resource["group_tool"].remove_group(
            group_id=request.group_id,
            user_id=current_user["id"]
        )

        return asdict(BaseResponse(
            code=200,
            message=result["message"]
        ))

    except ValueError as ve:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=400,
                message=str(ve)
            )),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Remove group error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )
