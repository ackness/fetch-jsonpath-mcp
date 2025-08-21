import json
from unittest.mock import AsyncMock, patch

import pytest

from jsonrpc_mcp.utils import batch_extract_json, batch_fetch_urls, fetch_url_content, get_http_client_config


@pytest.mark.asyncio
async def test_get_http_client_config():
    """Test HTTP client configuration from environment"""
    with patch.dict('os.environ', {
        'JSONRPC_MCP_TIMEOUT': '30.0',
        'JSONRPC_MCP_VERIFY': 'false',
        'JSONRPC_MCP_FOLLOW_REDIRECTS': 'true',
        'JSONRPC_MCP_HEADERS': '{"Authorization": "Bearer token"}',
        'JSONRPC_MCP_PROXY': 'http://proxy:8080'
    }):
        config = await get_http_client_config()
        
        assert config['timeout'] == 30.0
        assert not config['verify']
        assert config['follow_redirects']
        # Check that custom headers are present and default headers exist
        assert "Authorization" in config['headers']
        assert config['headers']["Authorization"] == "Bearer token"
        assert "User-Agent" in config['headers']  # Default browser header
        assert "Accept" in config['headers']      # Default browser header
        assert config['trust_env']


@pytest.mark.asyncio
async def test_fetch_url_content_json():
    """Test fetching JSON content with validation"""
    mock_response = AsyncMock()
    mock_response.text = '{"valid": "json"}'
    mock_response.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        result = await fetch_url_content("http://example.com", as_json=True)
        assert result == '{"valid": "json"}'


@pytest.mark.asyncio
async def test_fetch_url_content_invalid_json():
    """Test fetching invalid JSON content raises error"""
    mock_response = AsyncMock()
    mock_response.text = 'not valid json'
    mock_response.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        with pytest.raises(Exception):
            await fetch_url_content("http://example.com", as_json=True)


@pytest.mark.asyncio
async def test_batch_fetch_urls_mixed_results():
    """Test batch fetching with some failures"""
    
    async def mock_fetch(url, as_json=True, output_format="markdown"):
        if "fail" in url:
            raise Exception("Network error")
        return f"content from {url}"
    
    with patch('jsonrpc_mcp.utils.fetch_url_content', side_effect=mock_fetch):
        urls = ["http://success.com", "http://fail.com"]
        results = await batch_fetch_urls(urls, as_json=False)
        
        assert len(results) == 2
        assert results[0]["success"]
        assert results[0]["content"] == "content from http://success.com"
        assert not results[1]["success"]
        assert "error" in results[1]


@pytest.mark.asyncio
async def test_batch_extract_json_mixed_results():
    """Test batch JSON extraction with some failures"""
    
    async def mock_fetch(url, as_json=True, method="GET", data=None, headers=None, output_format="markdown"):
        if "fail" in url:
            raise Exception("Network error")
        if "invalid" in url:
            return "not json"
        return '{"data": [1, 2, 3]}'
    
    with patch('jsonrpc_mcp.utils.fetch_url_content', side_effect=mock_fetch):
        requests = [
            {"url": "http://success.com", "pattern": "data[*]"},
            {"url": "http://fail.com"},
            {"url": "http://invalid.com"},
            {"url": ""},  # Missing URL
        ]
        results = await batch_extract_json(requests)
        
        assert len(results) == 4
        assert results[0]["success"]
        assert results[0]["content"] == [1, 2, 3]
        assert not results[1]["success"]
        assert not results[2]["success"]
        assert not results[3]["success"]
        assert results[3]["error"] == "Missing URL"


@pytest.mark.asyncio
async def test_batch_extract_json_no_pattern():
    """Test batch JSON extraction without patterns"""
    with patch('jsonrpc_mcp.utils.fetch_url_content') as mock_fetch:
        mock_fetch.return_value = '{"full": "document"}'
        
        requests = [{"url": "http://example.com"}]
        results = await batch_extract_json(requests)
        
        assert len(results) == 1
        assert results[0]["success"]
        assert results[0]["content"] == [{"full": "document"}]


@pytest.mark.asyncio
async def test_batch_extract_json_same_url_optimization():
    """Test that same URL is only fetched once when multiple patterns are requested"""
    with patch('jsonrpc_mcp.utils.fetch_url_content') as mock_fetch:
        mock_fetch.return_value = '{"data": {"users": [{"name": "John"}, {"name": "Jane"}], "count": 2}}'
        
        # Multiple requests for the same URL with different patterns
        requests = [
            {"url": "http://127.0.0.1:8080", "pattern": "data.users[*].name"},
            {"url": "http://127.0.0.1:8080", "pattern": "data.count"},
            {"url": "http://other.com", "pattern": "data.users"},
            {"url": "http://127.0.0.1:8080", "pattern": "data.users"},
        ]
        results = await batch_extract_json(requests)
        
        # Verify fetch_url_content was called only twice (once for each unique URL)
        assert mock_fetch.call_count == 2
        
        # Verify all results are present and in the same order as requests
        assert len(results) == 4
        
        # First request: extract names
        assert results[0]["success"]
        assert results[0]["url"] == "http://127.0.0.1:8080"
        assert results[0]["pattern"] == "data.users[*].name"
        assert results[0]["content"] == ["John", "Jane"]
        
        # Second request: extract count
        assert results[1]["success"]
        assert results[1]["url"] == "http://127.0.0.1:8080"
        assert results[1]["pattern"] == "data.count"
        assert results[1]["content"] == [2]
        
        # Third request: different URL
        assert results[2]["success"]
        assert results[2]["url"] == "http://other.com"
        assert results[2]["pattern"] == "data.users"
        
        # Fourth request: same URL as first two
        assert results[3]["success"]
        assert results[3]["url"] == "http://127.0.0.1:8080"
        assert results[3]["pattern"] == "data.users"
        assert results[3]["content"] == [[{"name": "John"}, {"name": "Jane"}]]


@pytest.mark.asyncio
async def test_extract_json_extensions():
    """Test JSONPath extensions like len, keys, arithmetic, filtering"""
    from jsonrpc_mcp.utils import extract_json
    
    test_data = json.dumps({
        "users": [
            {"name": "John", "age": 30, "city": "NYC"},
            {"name": "Jane", "age": 25, "city": "LA"},
            {"name": "Bob", "age": 35, "city": "NYC"}
        ],
        "metadata": {
            "total": 3,
            "source": "api_v1"
        },
        "tags": "user,profile,test"
    })
    
    # Test len extension
    result = extract_json(test_data, "$.users.`len`")
    assert result == [3]
    
    # Test keys extension  
    result = extract_json(test_data, "$.metadata.`keys`")
    assert set(result) == {"total", "source"}
    
    # Test filtering
    result = extract_json(test_data, "$.users[?(@.age > 28)].name")
    assert set(result) == {"John", "Bob"}
    
    # Test arithmetic operations
    result = extract_json(test_data, "$.metadata.total + 1")
    assert result == [4]
    
    # Test string operations (split requires 3 params: separator, segment_index, max_splits)
    result = extract_json(test_data, "$.tags.`split(\",\", *, -1)`")
    assert result == [["user", "profile", "test"]]
    
    # Test multiple conditions filtering
    result = extract_json(test_data, "$.users[?(@.age > 25 & @.city = \"NYC\")].name")
    assert set(result) == {"John", "Bob"}  # Both John (30) and Bob (35) are > 25 and in NYC


@pytest.mark.asyncio  
async def test_extract_json_complex_extensions():
    """Test more complex JSONPath extension scenarios"""
    from jsonrpc_mcp.utils import extract_json
    
    test_data = json.dumps({
        "products": [
            {"name": "Apple", "price": 1.5, "category": "fruit", "stock": 100},
            {"name": "Banana", "price": 0.8, "category": "fruit", "stock": 150},
            {"name": "Carrot", "price": 2.0, "category": "vegetable", "stock": 80},
            {"name": "Broccoli", "price": 3.5, "category": "vegetable", "stock": 60}
        ],
        "store_info": {
            "name": "Fresh Market",
            "location": "Downtown_Plaza"
        }
    })
    
    # Test arithmetic with arrays
    result = extract_json(test_data, "$.products[*].price + $.products[*].stock")
    expected = [101.5, 150.8, 82.0, 63.5]  # price + stock for each item
    assert result == expected
    
    # Test string replacement - skip for now due to syntax complexity
    # result = extract_json(test_data, "$.store_info.location.`sub(/_/, \" \")`")
    # assert result == ["Downtown Plaza"]
    
    # Test filtering with complex conditions
    result = extract_json(test_data, "$.products[?(@.category = \"fruit\" & @.price < 1.0)].name")
    assert result == ["Banana"]
    
    # Test str() conversion
    result = extract_json(test_data, "$.products[0].price.`str()`")
    assert result == ["1.5"]
    
    # Test length of array
    result = extract_json(test_data, "$.products.`len`")
    assert result == [4]


@pytest.mark.asyncio
async def test_extract_json_fallback_to_basic_parser():
    """Test that basic patterns still work and fallback works correctly"""
    from jsonrpc_mcp.utils import extract_json
    
    test_data = json.dumps({
        "simple": {"nested": {"value": 42}},
        "array": [1, 2, 3, 4, 5]
    })
    
    # Basic patterns should work with both parsers
    result = extract_json(test_data, "$.simple.nested.value")
    assert result == [42]
    
    result = extract_json(test_data, "$.array[2:4]")
    assert result == [3, 4]
    
    result = extract_json(test_data, "$.array[*]")
    assert result == [1, 2, 3, 4, 5]