import json

import pytest

from jsonrpc_mcp.utils import extract_json

DEMO_STR = json.dumps(
    {
        "foo": [{"baz": 1, "qux": "a"}, {"baz": 2, "qux": "b"}],
        "bar": {"items": [10, 20, 30], "config": {"enabled": True, "name": "example", "nested": {"key1": "value1", "key2": "value2"}}},
        "metadata": {"version": "1.0.0", "timestamp": "2023-01-01T00:00:00Z"},
    }
)


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("foo[*].baz", [1, 2]),
        ("bar.items", [[10, 20, 30]]),
        ("bar.items[*]", [10, 20, 30]),
        ("bar.config.enabled", [True]),
        ("metadata.version", ["1.0.0"]),
        ("metadata.timestamp", ["2023-01-01T00:00:00Z"]),
        ("bar.config.nested", [{"key1": "value1", "key2": "value2"}]),
        ("bar.config.nested.key1", ["value1"]),
        ("bar.config.nested.key2", ["value2"]),
        ("", [json.loads(DEMO_STR)]),  # Empty pattern returns full document
        ("$", [json.loads(DEMO_STR)]),  # Root pattern returns full document
    ],
)
def test_extract_json(pattern, expected):
    assert extract_json(DEMO_STR, pattern) == expected


def test_extract_json_invalid_json():
    """Test extract_json with invalid JSON"""
    with pytest.raises(json.JSONDecodeError, match="Invalid JSON"):
        extract_json("invalid json", "foo")


def test_extract_json_invalid_pattern():
    """Test extract_json with invalid JSONPath pattern"""
    with pytest.raises(Exception, match="Invalid JSONPath pattern"):
        extract_json('{"test": "value"}', "invalid[[[pattern")
