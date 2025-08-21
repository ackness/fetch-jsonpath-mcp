from unittest.mock import AsyncMock, patch

import pytest

from jsonrpc_mcp.server import handle_call_tool, handle_get_json
from jsonrpc_mcp.utils import batch_extract_json, batch_fetch_urls, fetch_url_content


@pytest.mark.asyncio
async def test_handle_get_json_basic():
    """Test basic JSON extraction without pattern"""
    with patch('jsonrpc_mcp.server.fetch_url_content') as mock_fetch:
        mock_fetch.return_value = '{"test": "value"}'
        result = await handle_get_json("http://example.com")
        assert result == [{"test": "value"}]
        mock_fetch.assert_called_once_with("http://example.com", as_json=True, method="GET", data=None, headers=None)


@pytest.mark.asyncio
async def test_handle_get_json_with_pattern():
    """Test JSON extraction with JSONPath pattern"""
    with patch('jsonrpc_mcp.server.fetch_url_content') as mock_fetch:
        mock_fetch.return_value = '{"data": {"items": [1, 2, 3]}}'
        result = await handle_get_json("http://example.com", "data.items[*]")
        assert result == [1, 2, 3]
        mock_fetch.assert_called_once_with("http://example.com", as_json=True, method="GET", data=None, headers=None)


@pytest.mark.asyncio
async def test_fetch_url_content_text():
    """Test fetching raw text content"""
    mock_response = AsyncMock()
    mock_response.text = "Hello, World!"
    mock_response.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        result = await fetch_url_content("http://example.com", as_json=False)
        assert result == "Hello, World!"


@pytest.mark.asyncio
async def test_batch_fetch_urls():
    """Test batch fetching multiple URLs"""
    mock_response1 = AsyncMock()
    mock_response1.text = "Content 1"
    mock_response1.raise_for_status = AsyncMock()
    mock_response2 = AsyncMock()
    mock_response2.text = "Content 2"
    mock_response2.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_get = mock_client.return_value.__aenter__.return_value.get
        mock_get.side_effect = [mock_response1, mock_response2]
        
        result = await batch_fetch_urls(["http://example1.com", "http://example2.com"], as_json=False)
        
        assert len(result) == 2
        assert result[0]["url"] == "http://example1.com"
        assert result[0]["success"]
        assert result[0]["content"] == "Content 1"
        assert result[1]["url"] == "http://example2.com"
        assert result[1]["success"]
        assert result[1]["content"] == "Content 2"


@pytest.mark.asyncio
async def test_batch_extract_json():
    """Test batch JSON extraction"""
    requests = [
        {"url": "http://example1.com", "pattern": "data[*]"},
        {"url": "http://example2.com"}
    ]
    
    with patch('jsonrpc_mcp.utils.fetch_url_content') as mock_fetch:
        mock_fetch.side_effect = ['{"data": [1, 2]}', '{"value": "test"}']
        
        result = await batch_extract_json(requests)
        
        assert len(result) == 2
        assert result[0]["success"]
        assert result[0]["content"] == [1, 2]
        assert result[1]["success"]
        assert result[1]["content"] == [{"value": "test"}]


@pytest.mark.asyncio
async def test_handle_call_tool_missing_url():
    """Test tool call with missing URL"""
    result = await handle_call_tool("fetch-json", {})
    assert len(result) == 1
    assert "Missing required property: url" in result[0].text


@pytest.mark.asyncio
async def test_handle_call_tool_unknown_tool():
    """Test call to unknown tool"""
    result = await handle_call_tool("unknown-tool", {})
    assert len(result) == 1
    assert "Unknown tool: unknown-tool" in result[0].text


@pytest.mark.asyncio
async def test_handle_call_tool_fetch_text():
    """Test fetch-text tool"""
    with patch('jsonrpc_mcp.server.fetch_url_content') as mock_fetch:
        mock_fetch.return_value = "Plain text content"
        result = await handle_call_tool("fetch-text", {"url": "http://example.com"})
        assert len(result) == 1
        assert result[0].text == "Plain text content"
        mock_fetch.assert_called_once_with("http://example.com", as_json=False, method="GET", data=None, headers=None, output_format="markdown")


@pytest.mark.asyncio
async def test_handle_call_tool_batch_fetch_json():
    """Test batch-fetch-json tool"""
    with patch('jsonrpc_mcp.utils.batch_extract_json') as mock_batch:
        mock_batch.return_value = [{"url": "http://example.com", "success": True, "content": [1, 2, 3]}]
        result = await handle_call_tool("batch-fetch-json", {
            "requests": [{"url": "http://example.com", "pattern": "data[*]"}]
        })
        assert len(result) == 1
        assert "success" in result[0].text


@pytest.mark.asyncio
async def test_handle_call_tool_batch_fetch_text():
    """Test batch-fetch-text tool"""
    with patch('jsonrpc_mcp.utils.batch_fetch_urls') as mock_batch:
        mock_batch.return_value = [{"url": "http://example.com", "success": True, "content": "text"}]
        result = await handle_call_tool("batch-fetch-text", {
            "requests": ["http://example.com"]
        })
        assert len(result) == 1
        assert "success" in result[0].text


@pytest.mark.asyncio
async def test_handle_call_tool_batch_missing_params():
    """Test batch tools with missing parameters"""
    result = await handle_call_tool("batch-fetch-json", {})
    assert "Missing or empty 'requests' array" in result[0].text
    
    result = await handle_call_tool("batch-fetch-text", {})
    assert "Missing or empty 'requests' array" in result[0].text
