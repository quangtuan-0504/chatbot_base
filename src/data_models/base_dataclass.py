from dataclasses import dataclass
from typing import List, Optional, Any, Union, Dict
from datetime import datetime
from enum import Enum


class ResponseMessage:
    # Success messages
    SUCCESS = "Success"
    CREATE_SUCCESS = "Created successfully"
    UPDATE_SUCCESS = "Updated successfully"
    DELETE_SUCCESS = "Deleted successfully"

    # Error messages
    # Generic errors
    INTERNAL_ERROR = "An internal server error occurred"
    BAD_REQUEST = "Bad request"
    NOT_FOUND = "Resource not found"
    UNAUTHORIZED = "Unauthorized access"

    # Validation errors
    MISSING_REQUIRED_FIELD = "Missing required field: {}"
    MISSING_REQUIRED_PARAM = "Missing required parameter: {}"
    INVALID_INPUT = "Invalid input provided"

    # Authentication errors
    INVALID_CREDENTIALS = "Invalid credentials"
    TOKEN_EXPIRED = "Token has expired"
    TOKEN_INVALID = "Invalid token"

    # Chat specific messages
    CHAT_NOT_FOUND = "Chat history not found"
    CHAT_CREATED = "Chat created successfully"
    CHAT_UPDATED = "Chat updated successfully"
    CHAT_DELETED = "Chat deleted successfully"
    CHAT_HISTORY_NOT_FOUND = "Chat history not found for the specified user and chat"
    USER_CHATS_NOT_FOUND = "No chat histories found for the specified user"

    # Collection specific messages
    COLLECTION_ID_INVALID = "Invalid Collection ID format"
    COLLECTION_NOT_FOUND = "Collection not found"

    @staticmethod
    def missing_field(field_name: str) -> str:
        return ResponseMessage.MISSING_REQUIRED_FIELD.format(field_name)

    @staticmethod
    def missing_param(param_name: str) -> str:
        return ResponseMessage.MISSING_REQUIRED_PARAM.format(param_name)

    @staticmethod
    def not_found(resource: str) -> str:
        return f"{resource} not found"

    @staticmethod
    def error_occurred(error: Exception) -> str:
        return f"An unexpected error occurred: {str(error)}"

@dataclass
class BaseResponse:
    data: Optional[Any] = None
    code: int = 200
    message: str = ResponseMessage.SUCCESS
 