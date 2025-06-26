import uuid
from typing import Any, Optional


def validate_uuid(uuid_string: str) -> bool:
    """Validate that a string is a proper UUID"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def validate_block_type(block_type: str) -> bool:
    """Validate block type is one of the allowed values"""
    allowed_types = ["bullet", "todo", "done", "heading", "quote", "code", "divider"]
    return block_type in allowed_types


def validate_content_type(content_type: str) -> bool:
    """Validate content type is one of the allowed values"""
    allowed_types = ["text", "markdown", "image", "video", "audio", "file", "embed", "code", "quote"]
    return content_type in allowed_types


def validate_page_type(page_type: str) -> bool:
    """Validate page type is one of the allowed values"""
    allowed_types = ["page", "daily", "template"]
    return page_type in allowed_types


def validate_positive_integer(value: Any) -> Optional[int]:
    """Validate and convert value to positive integer"""
    try:
        int_value = int(value)
        return int_value if int_value >= 0 else None
    except (ValueError, TypeError):
        return None


def validate_date_string(date_string: str) -> bool:
    """Validate date string is in YYYY-MM-DD format"""
    try:
        from datetime import datetime
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def sanitize_search_query(query: str) -> str:
    """Sanitize search query to prevent issues"""
    if not query:
        return ""
    # Remove excessive whitespace and limit length
    return query.strip()[:200]