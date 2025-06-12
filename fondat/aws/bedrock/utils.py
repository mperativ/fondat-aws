from datetime import datetime
from typing import Optional, Any, Dict
import re


def parse_bedrock_datetime(date_str: Optional[str | datetime]) -> Optional[datetime]:
    """
    Parse a datetime string from Bedrock API format to a Python datetime object.
    Bedrock API returns dates in ISO 8601 format with 'Z' suffix, which needs to be
    converted to '+00:00' for proper parsing.
    
    Args:
        date_str: The datetime string from Bedrock API, or a datetime object, or None
        
    Returns:
        A datetime object if date_str is not None, None otherwise
    """
    if date_str is None:
        return None
    if isinstance(date_str, datetime):
        return date_str
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

def camel_to_snake(name: str) -> str:
    """Convert a camelCase string to snake_case."""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def convert_dict_keys_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all keys in a dictionary from camelCase to snake_case."""
    def convert_value(v: Any) -> Any:
        if isinstance(v, dict):
            return convert_dict_keys_to_snake_case(v)
        elif isinstance(v, list):
            return [convert_value(item) for item in v]
        return v

    return {
        camel_to_snake(str(k)) if isinstance(k, str) else k: convert_value(v)
        for k, v in data.items()
    } 