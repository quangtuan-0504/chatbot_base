from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from dataclasses import asdict
from ..tools.load_resources import resource
from ..data_models.auth_dataclass import *
from ..data_models import BaseResponse, ResponseMessage
from ..utils.auth_utils import *
from ..loggers.logapp import logger

router = APIRouter()

@router.post("/register", response_model=dict)
async def register(request: UserRegistrationRequest):
    """Register a new user"""
    try:
        # Validate required fields
        if not request.email or not request.password:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('email or password')
                )),
                status_code=400
            )

        # Create user
        user_data = resource["user_tool"].create_user(
            email=request.email,
            username=request.username,
            password=request.password,
            name=request.name
        )

        return asdict(UserResponse(
            code=200,
            data=UserItem.from_dict(user_data),
            message=ResponseMessage.CREATE_SUCCESS
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
        logger.error(f"Registration error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/login", response_model=dict)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Authenticate user and return JWT tokens"""
    try:
        # Authenticate user
        user = resource["user_tool"].authenticate_user(
            email_or_username=form_data.username,
            password=form_data.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token = create_access_token(data={"sub": user["id"]})
        refresh_token = create_refresh_token(data={"sub": user["id"]})

        # Update last login
        resource["user_tool"].update_last_login(user["id"])

        return asdict(
            TokenData(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                user=UserItem.from_dict(user)
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/refresh-token", response_model=dict)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        payload = verify_token(request.refresh_token)
        email = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user = resource["user_tool"].get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        access_token = create_access_token(data={"sub": email})
        new_refresh_token = create_refresh_token(data={"sub": email})

        return asdict(TokenData(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user=UserItem.from_dict(user)
        ))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/logout", response_model=dict)
async def logout(current_user: dict = Depends(get_current_active_user)):
    """Logout user (in a real implementation, you'd invalidate the token)"""
    try:
        # In a real implementation, you'd add the token to a blacklist
        return asdict(BaseResponse(
            code=200,
            message="Logout successful"
        ))
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.put("/reset-password", response_model=dict)
async def reset_password(
    request: ResetPasswordRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Reset user password"""
    try:
        # Verify current password
        if not resource["user_tool"].verify_password(current_user["email"], request.current_password):
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message="Current password is incorrect"
                )),
                status_code=400
            )

        # Update password
        resource["user_tool"].update_password(current_user["id"], request.new_password)

        return asdict(BaseResponse(
            code=200,
            message="Password updated successfully"
        ))

    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )
