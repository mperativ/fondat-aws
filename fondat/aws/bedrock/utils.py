from datetime import datetime
from typing import Optional


def parse_bedrock_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse a datetime string from Bedrock API format to a Python datetime object.
    Bedrock API returns dates in ISO 8601 format with 'Z' suffix, which needs to be
    converted to '+00:00' for proper parsing.
    
    Args:
        date_str: The datetime string from Bedrock API, or None
        
    Returns:
        A datetime object if date_str is not None, None otherwise
    """
    if date_str is None:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00")) 