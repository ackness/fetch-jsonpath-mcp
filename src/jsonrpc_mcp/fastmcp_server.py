"""FastMCP server implementation for JSONRPC MCP Server."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from jsonrpc_mcp.utils import batch_extract_json, batch_fetch_urls, extract_json, fetch_url_content


def ensure_json_serializable(obj: Any) -> Any:
    """Ensure object is JSON serializable, converting if necessary."""
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        if isinstance(obj, list | tuple):
            return [ensure_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {str(k): ensure_json_serializable(v) for k, v in obj.items()}
        else:
            return str(obj)

# Create FastMCP server instance
mcp = FastMCP("fetch-jsonpath-mcp")


# Pydantic models for structured input/output
class BatchRequest(BaseModel):
    url: str
    pattern: str = ""
    method: str = "GET"
    data: dict | str | None = None
    headers: dict[str, str] | None = None


class BatchTextRequest(BaseModel):
    url: str
    method: str = "GET"
    data: dict | str | None = None
    headers: dict[str, str] | None = None
    output_format: str = "markdown"


class BatchResult(BaseModel):
    url: str
    pattern: str = ""
    method: str = "GET"
    success: bool
    content: Any = None
    error: str | None = None


@mcp.tool()
async def fetch_json(
    url: str, 
    pattern: str = "", 
    method: str = "GET", 
    data: dict | str | None = None,
    headers: dict[str, str] | None = None
) -> list:
    """
    Extract JSON content from a URL using JSONPath with support for different HTTP methods.
    If 'pattern' is omitted or empty, the entire JSON document is returned.
    
    Args:
        url: The URL to get raw JSON from
        pattern: JSONPath pattern, e.g. 'foo[*].baz', 'bar.items[*]'
        method: HTTP method to use (GET, POST, PUT, DELETE, etc.). Default is GET.
        data: Request body data for POST/PUT/PATCH requests. Can be a JSON object or string.
        headers: Additional HTTP headers to include in the request
    
    Returns:
        List of extracted values
    """
    try:
        content = await fetch_url_content(url, as_json=True, method=method, data=data, headers=headers)
        result = extract_json(content, pattern)
        # Ensure the result is JSON serializable
        return ensure_json_serializable(result)
    except Exception as e:
        # If JSON parsing fails, provide helpful error message
        error_msg = str(e)
        if "Expecting value" in error_msg:
            raise ValueError(f"URL '{url}' did not return valid JSON content. Use 'get_text' tool for non-JSON content.")
        else:
            raise ValueError(f"Failed to process JSON from '{url}': {error_msg}")


@mcp.tool()
async def fetch_text(
    url: str, 
    method: str = "GET", 
    data: dict | str | None = None,
    headers: dict[str, str] | None = None,
    output_format: str = "markdown"
) -> str:
    """
    Fetch text content from a URL with support for different HTTP methods.
    Defaults to converting HTML to Markdown format.
    
    Args:
        url: The URL to fetch text content from
        method: HTTP method to use (GET, POST, PUT, DELETE, etc.). Default is GET.
        data: Request body data for POST/PUT/PATCH requests. Can be a JSON object or string.
        headers: Additional HTTP headers to include in the request
        output_format: Output format - 'markdown' (default), 'clean_text', or 'raw_html'
    
    Returns:
        Text content from the URL in the specified format
    """
    return await fetch_url_content(url, as_json=False, method=method, data=data, headers=headers, output_format=output_format)


@mcp.tool()
async def batch_fetch_json(requests: list[BatchRequest]) -> list[dict]:
    """
    Batch extract JSON content from multiple URLs with different JSONPath patterns.
    Supports different HTTP methods. Executes requests concurrently for better performance.
    
    Args:
        requests: Array of request objects with 'url', optional 'pattern', 'method', 'data', 'headers'
    
    Returns:
        List of results with success/failure information
    """
    # Convert Pydantic models to dicts for utility function
    request_dicts = [
        {
            "url": req.url, 
            "pattern": req.pattern,
            "method": req.method,
            "data": req.data,
            "headers": req.headers
        } 
        for req in requests
    ]
    results = await batch_extract_json(request_dicts)
    
    # Ensure all results are JSON serializable
    return ensure_json_serializable(results)


@mcp.tool()
async def batch_fetch_text(requests: list[BatchTextRequest | str], output_format: str = "markdown") -> list[dict[str, Any]]:
    """
    Batch fetch text content from multiple URLs with support for different HTTP methods.
    Defaults to converting HTML to Markdown format. Executes requests concurrently for better performance.
    
    Args:
        requests: Array of URLs (strings) or request objects with 'url', 'method', 'data', 'headers', 'output_format'
        output_format: Default output format - 'markdown' (default), 'clean_text', or 'raw_html' (can be overridden per request)
    
    Returns:
        List of results with success/failure information
    """
    # Convert mixed input to consistent format
    converted_requests = []
    for req in requests:
        if isinstance(req, str):
            converted_requests.append(req)
        else:
            converted_requests.append({
                "url": req.url,
                "method": req.method,
                "data": req.data,
                "headers": req.headers,
                "output_format": req.output_format
            })
    
    results = await batch_fetch_urls(converted_requests, as_json=False, output_format=output_format)
    
    # Ensure all results are JSON serializable
    return ensure_json_serializable(results)


def run():
    """Entry point for the FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    run()