"""
Timezone utility module for handling datetime operations with GMT+7 (Asia/Bangkok) timezone.
This module provides consistent timezone-aware datetime operations across the application.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# GMT+7 timezone (Southeast Asia timezone)
GMT_PLUS_7 = timezone(timedelta(hours=7))


def now_gmt7() -> datetime:
    """
    Get current datetime in GMT+7 timezone.

    Returns:
        datetime: Current datetime with GMT+7 timezone
    """
    return datetime.now(GMT_PLUS_7)


def utcnow_to_gmt7() -> datetime:
    """
    Get current UTC datetime converted to GMT+7 timezone.

    Returns:
        datetime: Current datetime in GMT+7 timezone
    """
    return datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(GMT_PLUS_7)


def format_datetime_gmt7(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime in GMT+7 timezone.

    Args:
        dt: Datetime object to format. If None, uses current time.
        format_str: Format string for datetime formatting

    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        dt = now_gmt7()
    elif dt.tzinfo is None:
        # If datetime is naive, assume it's UTC and convert to GMT+7
        dt = dt.replace(tzinfo=timezone.utc).astimezone(GMT_PLUS_7)
    elif dt.tzinfo != GMT_PLUS_7:
        # Convert to GMT+7 if it's in a different timezone
        dt = dt.astimezone(GMT_PLUS_7)

    return dt.strftime(format_str)


def convert_to_gmt7(dt: datetime) -> datetime:
    """
    Convert any datetime to GMT+7 timezone.

    Args:
        dt: Datetime object to convert

    Returns:
        datetime: Datetime in GMT+7 timezone
    """
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(GMT_PLUS_7)


def get_gmt7_datetime_for_db() -> datetime:
    """
    Get GMT+7 datetime object suitable for database storage.
    Returns timezone-aware datetime in GMT+7.

    Returns:
        datetime: GMT+7 timezone-aware datetime
    """
    return now_gmt7()


def parse_datetime_string(datetime_str: str, format_str: str = "%d-%m-%Y %H:%M") -> datetime:
    """
    Parse datetime string and return as GMT+7 timezone-aware datetime.

    Args:
        datetime_str: String representation of datetime
        format_str: Format string for parsing

    Returns:
        datetime: Parsed datetime in GMT+7 timezone
    """
    dt = datetime.strptime(datetime_str, format_str)
    # Assume the parsed datetime is in GMT+7 timezone
    return dt.replace(tzinfo=GMT_PLUS_7)