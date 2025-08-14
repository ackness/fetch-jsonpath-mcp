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
        assert config['headers'] == {"Authorization": "Bearer token"}
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
    
    async def mock_fetch(url, as_json=True):
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
    
    async def mock_fetch(url, as_json=True):
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