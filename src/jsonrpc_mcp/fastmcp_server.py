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
        if isinstance(obj, (list, tuple)):
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


class BatchResult(BaseModel):
    url: str
    pattern: str = ""
    success: bool
    content: Any = None
    error: str | None = None


@mcp.tool()
async def get_json(url: str, pattern: str = "") -> list:
    """
    Extract JSON content from a URL using JSONPath.
    If 'pattern' is omitted or empty, the entire JSON document is returned.
    
    Args:
        url: The URL to get raw JSON from
        pattern: JSONPath pattern, e.g. 'foo[*].baz', 'bar.items[*]'
    
    Returns:
        List of extracted values
    """
    try:
        content = await fetch_url_content(url, as_json=True)
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
async def get_text(url: str) -> str:
    """
    Get raw text content from a URL (not limited to JSON).
    
    Args:
        url: The URL to get text content from
    
    Returns:
        Raw text content from the URL
    """
    return await fetch_url_content(url, as_json=False)


@mcp.tool()
async def batch_get_json(requests: list[BatchRequest]) -> list[dict]:
    """
    Batch extract JSON content from multiple URLs with different JSONPath patterns.
    Executes requests concurrently for better performance.
    
    Args:
        requests: Array of request objects with 'url' and optional 'pattern'
    
    Returns:
        List of results with success/failure information
    """
    # Convert Pydantic models to dicts for utility function
    request_dicts = [{"url": req.url, "pattern": req.pattern} for req in requests]
    results = await batch_extract_json(request_dicts)
    
    # Ensure all results are JSON serializable
    return ensure_json_serializable(results)


@mcp.tool()
async def batch_get_text(urls: list[str]) -> list[dict[str, Any]]:
    """
    Batch get raw text content from multiple URLs.
    Executes requests concurrently for better performance.
    
    Args:
        urls: Array of URLs to fetch
    
    Returns:
        List of results with success/failure information
    """
    results = await batch_fetch_urls(urls, as_json=False)
    
    # Ensure all results are JSON serializable
    return ensure_json_serializable(results)


def run():
    """Entry point for the FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    run()