from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from dataclasses import asdict
from ..tools.load_resources import resource
from ..data_models.auth_dataclass import *
from ..data_models import BaseResponse, ResponseMessage
from ..utils.auth_utils import get_current_active_user, require_admin
from ..loggers.logapp import logger

router = APIRouter()

@router.get("/profile", response_model=dict)
async def get_profile(current_user: dict = Depends(get_current_active_user)):
    """Get current user's profile"""
    try:
        return asdict(UserResponse(
            code=200,
            data=UserItem.from_dict(current_user),
            message="Profile retrieved successfully"
        ))
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.put("/profile", response_model=dict)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Update current user's profile"""
    try:
        updated_user = resource["user_tool"].update_user_profile(
            user_id=current_user["id"],
            email=request.email,
            name=request.name
        )

        return asdict(UserResponse(
            code=200,
            data=UserItem.from_dict(updated_user),
            message="Profile updated successfully"
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
        logger.error(f"Update profile error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/admin/view-all-users", response_model=dict)
async def view_all_users(
    request: ViewUsersRequest,
    current_user: dict = Depends(require_admin)
):
    """Get all users (admin only)"""
    try:
        users_data = resource["user_tool"].get_all_users(
            name_filter=request.name_filter,
            email_filter=request.email_filter,
            page=request.page,
            limit=request.limit
        )

        user_items = [UserItem.from_dict(user) for user in users_data["users"]]
        
        return asdict(UserListResponse(
            code=200,
            data=user_items,
            total=users_data["total"],
            page=request.page,
            limit=request.limit,
            message="Users retrieved successfully"
        ))

    except Exception as e:
        logger.error(f"View all users error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/admin/grant-role", response_model=dict)
async def grant_role(
    request: GrantRoleRequest,
    current_user: dict = Depends(require_admin)
):
    """Grant system role to user (admin only)"""
    try:
        if not request.user_id or not request.system_role:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('user_id or system_role')
                )),
                status_code=400
            )

        updated_user = resource["user_tool"].update_user_role(
            user_id=request.user_id,
            system_role=request.system_role,
            updated_by=current_user["id"]
        )

        return asdict(UserResponse(
            code=200,
            data=UserItem.from_dict(updated_user),
            message="Role granted successfully"
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
        logger.error(f"Grant role error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )
@router.put("/admin/enable-disable-user", response_model=dict)
async def enable_disable_user(
    request: EnableDisableUserRequest,
    current_user: dict = Depends(require_admin)
):
    """Disable user (admin only)"""
    try:
        if not request.user_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('user_id')
                )),
                status_code=400
            )

        updated_user = resource["user_tool"].enable_disable_user(
            user_id=request.user_id,
            updated_by=current_user["id"]
        )

        return asdict(UserResponse(
            code=200,
            data=UserItem.from_dict(updated_user),
            message="Disable user successfully"
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
        logger.error(f"Disable user error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )
 