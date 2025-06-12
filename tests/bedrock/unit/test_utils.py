import pytest
from datetime import datetime, timezone
from fondat.aws.bedrock.utils import (
    parse_bedrock_datetime,
    camel_to_snake,
    convert_dict_keys_to_snake_case
)
from fondat.aws.bedrock.pagination import paginate, decode_cursor
from fondat.aws.bedrock.cache import BedrockCache
from fondat.aws.bedrock.decorators import operation
from fondat.aws.bedrock.clients import agent_client, runtime_client
from fondat.pagination import Page

def test_parse_bedrock_datetime():
    # Test with None
    assert parse_bedrock_datetime(None) is None
    
    # Test with datetime object
    now = datetime.now(timezone.utc)
    assert parse_bedrock_datetime(now) == now
    
    # Test with ISO 8601 string with Z
    date_str = "2024-03-20T10:30:00Z"
    expected = datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc)
    assert parse_bedrock_datetime(date_str) == expected
    
    # Test with ISO 8601 string with timezone
    date_str = "2024-03-20T10:30:00+00:00"
    expected = datetime(2024, 3, 20, 10, 30, 0, tzinfo=timezone.utc)
    assert parse_bedrock_datetime(date_str) == expected

    with pytest.raises(ValueError):
        parse_bedrock_datetime("invalid-date")
    

def test_camel_to_snake():
    # Test simple camelCase
    assert camel_to_snake("camelCase") == "camel_case"
    
    # Test multiple words
    assert camel_to_snake("thisIsATest") == "this_is_a_test"
    
    # Test with numbers
    assert camel_to_snake("test123Case") == "test123_case"
    
    # Test with consecutive capitals
    assert camel_to_snake("HTMLParser") == "html_parser"
    
    # Test with single word
    assert camel_to_snake("test") == "test"
    
    # Test with empty string
    assert camel_to_snake("") == ""

def test_convert_dict_keys_to_snake_case():
    # Test simple dictionary
    input_dict = {"camelCase": 1, "PascalCase": 2, "already_snake_case": 3}
    expected = {"camel_case": 1, "pascal_case": 2, "already_snake_case": 3}
    assert convert_dict_keys_to_snake_case(input_dict) == expected
    
    # Test nested dictionary
    input_dict = {
        "outerCamel": {
            "innerCamel": 1,
            "innerPascal": 2
        },
        "outerPascal": {
            "innerCamel": 3,
            "innerPascal": 4
        }
    }
    expected = {
        "outer_camel": {
            "inner_camel": 1,
            "inner_pascal": 2
        },
        "outer_pascal": {
            "inner_camel": 3,
            "inner_pascal": 4
        }
    }
    assert convert_dict_keys_to_snake_case(input_dict) == expected

    # Test with lists
    input_dict = {
        "camelCase": [
            {"innerCamel": 1},
            {"innerPascal": 2}
        ]
    }
    expected = {
        "camel_case": [
            {"inner_camel": 1},
            {"inner_pascal": 2}
        ]
    }
    assert convert_dict_keys_to_snake_case(input_dict) == expected

    # Test with empty structures
    assert convert_dict_keys_to_snake_case({}) == {}
    assert convert_dict_keys_to_snake_case({"emptyList": []}) == {"empty_list": []}
    assert convert_dict_keys_to_snake_case({"emptyDict": {}}) == {"empty_dict": {}}
