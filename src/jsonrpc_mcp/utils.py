import asyncio
import json
from typing import Any

import httpx
from jsonpath_ng import parse


def extract_json(json_str: str, pattern: str) -> list:
    """
    Extract JSON values from a JSON string using a JSONPath pattern.

    If the pattern is empty or refers to the root ("$", "$.", or "@"),
    the entire JSON document is returned as a single-element list.
    
    Args:
        json_str: JSON string to parse
        pattern: JSONPath pattern to extract data
        
    Returns:
        List of extracted values
        
    Raises:
        json.JSONDecodeError: If json_str is not valid JSON
        Exception: If JSONPath pattern is invalid
    """
    try:
        d = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON: {e.msg}", e.doc, e.pos)
    
    if not pattern or pattern.strip() in {"", "$", "$.", "@"}:
        return [d]
    
    try:
        jsonpath_expr = parse(pattern)
        return [match.value for match in jsonpath_expr.find(d)]
    except Exception as e:
        raise Exception(f"Invalid JSONPath pattern '{pattern}': {e}")


async def get_http_client_config() -> dict[str, Any]:
    """Get HTTP client configuration from environment variables."""
    import os
    
    # Timeout (seconds)
    timeout_str = os.getenv("JSONRPC_MCP_TIMEOUT", "").strip()
    timeout = float(timeout_str) if timeout_str else 10.0

    # SSL verification
    verify_str = os.getenv("JSONRPC_MCP_VERIFY", "").strip().lower()
    verify = True if verify_str == "" else verify_str in {"1", "true", "yes", "on"}

    # Follow redirects
    redirects_str = os.getenv("JSONRPC_MCP_FOLLOW_REDIRECTS", "").strip().lower()
    follow_redirects = True if redirects_str == "" else redirects_str in {"1", "true", "yes", "on"}

    # Optional headers as JSON string
    headers_env = os.getenv("JSONRPC_MCP_HEADERS", "").strip()
    headers = None
    if headers_env:
        try:
            parsed = json.loads(headers_env)
            if isinstance(parsed, dict):
                headers = {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            # Ignore malformed headers; proceed without custom headers
            headers = None

    # Optional proxy configuration
    proxy_env = os.getenv("JSONRPC_MCP_PROXY", "").strip()
    if proxy_env:
        os.environ.setdefault("HTTP_PROXY", proxy_env)
        os.environ.setdefault("HTTPS_PROXY", proxy_env)

    return {
        "timeout": timeout,
        "verify": verify,
        "follow_redirects": follow_redirects,
        "headers": headers,
        "trust_env": True,
    }


async def fetch_url_content(url: str, as_json: bool = True) -> str:
    """
    Fetch content from a URL.
    
    Args:
        url: URL to fetch content from
        as_json: If True, validates content as JSON; if False, returns raw text
        
    Returns:
        String content from the URL
        
    Raises:
        httpx.RequestError: For network-related errors
        json.JSONDecodeError: If as_json=True and content is not valid JSON
    """
    config = await get_http_client_config()
    
    async with httpx.AsyncClient(**config) as client:
        response = await client.get(url)
        response.raise_for_status()
        
        if as_json:
            # Validate that it's valid JSON
            json.loads(response.text)
        
        return response.text


async def batch_fetch_urls(urls: list[str], as_json: bool = True) -> list[dict[str, Any]]:
    """
    Batch fetch content from multiple URLs concurrently.
    
    Args:
        urls: List of URLs to fetch
        as_json: If True, validates content as JSON; if False, returns raw text
        
    Returns:
        List of dictionaries with 'url', 'success', 'content', and optional 'error' keys
    """
    async def fetch_single(url: str) -> dict[str, Any]:
        try:
            content = await fetch_url_content(url, as_json=as_json)
            return {"url": url, "success": True, "content": content}
        except Exception as e:
            return {"url": url, "success": False, "error": str(e)}
    
    tasks = [fetch_single(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return list(results)


async def batch_extract_json(url_patterns: list[dict[str, str]]) -> list[dict[str, Any]]:
    """
    Batch extract JSON data from multiple URLs with different patterns.
    
    Args:
        url_patterns: List of dicts with 'url' and optional 'pattern' keys
        
    Returns:
        List of dictionaries with extraction results
    """
    async def extract_single(item: dict[str, str]) -> dict[str, Any]:
        url = item.get("url", "")
        pattern = item.get("pattern", "")
        
        if not url:
            return {"url": url, "pattern": pattern, "success": False, "error": "Missing URL"}
        
        try:
            content = await fetch_url_content(url, as_json=True)
            extracted = extract_json(content, pattern)
            return {
                "url": url, 
                "pattern": pattern, 
                "success": True, 
                "content": extracted
            }
        except Exception as e:
            return {
                "url": url, 
                "pattern": pattern, 
                "success": False, 
                "error": str(e)
            }
    
    tasks = [extract_single(item) for item in url_patterns]
    results = await asyncio.gather(*tasks)
    return list(results)
