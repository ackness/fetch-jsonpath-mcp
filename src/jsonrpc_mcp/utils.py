import asyncio
import json
from typing import Any

import httpx
from bs4 import BeautifulSoup
from jsonpath_ng import parse
from jsonpath_ng.ext import parse as ext_parse


def extract_json(json_str: str, pattern: str) -> list:
    """
    Extract JSON values from a JSON string using a JSONPath pattern.
    
    Supports both standard JSONPath and extended JSONPath features including:
    - Extensions: len, keys, str(), sub(), split(), sorted, filter
    - Arithmetic operations: +, -, *, /
    - Advanced filtering: [?(@.field > value)]
    - And more extended features from jsonpath-ng.ext

    If the pattern is empty or refers to the root ("$", "$.", or "@"),
    the entire JSON document is returned as a single-element list.
    
    Args:
        json_str: JSON string to parse
        pattern: JSONPath pattern to extract data (supports extensions)
        
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
    
    # Try extended parser first (supports all extensions)
    try:
        jsonpath_expr = ext_parse(pattern)
        return [match.value for match in jsonpath_expr.find(d)]
    except Exception as ext_error:
        # Fallback to basic parser if extended parsing fails
        try:
            jsonpath_expr = parse(pattern)
            return [match.value for match in jsonpath_expr.find(d)]
        except Exception as basic_error:
            # Report the more descriptive error from extended parser if available
            error_msg = str(ext_error) if ext_error else str(basic_error)
            raise Exception(f"Invalid JSONPath pattern '{pattern}': {error_msg}")


def extract_text_content(html_content: str, output_format: str = "markdown") -> str:
    """
    Extract text content from HTML in different formats.
    
    Args:
        html_content: Raw HTML content
        output_format: Output format - "markdown" (default), "clean_text", or "raw_html"
    
    Returns:
        Extracted content in the specified format
    """
    if output_format == "raw_html":
        return html_content
    
    try:
        from markdownify import markdownify as md
        
        if output_format == "markdown":
            # Convert HTML to Markdown
            markdown_text = md(html_content, 
                               heading_style="ATX",  # Use # for headings
                               bullets="*",          # Use * for bullets
                               strip=["script", "style", "noscript"])
            
            # Clean up extra whitespace
            lines = (line.rstrip() for line in markdown_text.splitlines())
            markdown_text = '\n'.join(line for line in lines if line.strip() or not line)
            
            return markdown_text.strip()
            
        elif output_format == "clean_text":
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Drop blank lines
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        else:
            # Unknown format, return raw HTML
            return html_content
            
    except Exception:
        # If processing fails, return original content
        return html_content


def get_default_browser_headers() -> dict[str, str]:
    """Get default browser headers to simulate real browser access."""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }


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

    # Start with default browser headers
    headers = get_default_browser_headers().copy()
    
    # Optional headers as JSON string (will override defaults)
    headers_env = os.getenv("JSONRPC_MCP_HEADERS", "").strip()
    if headers_env:
        try:
            parsed = json.loads(headers_env)
            if isinstance(parsed, dict):
                custom_headers = {str(k): str(v) for k, v in parsed.items()}
                headers.update(custom_headers)
        except Exception:
            # If parsing fails, keep the default headers
            pass

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


async def fetch_url_content(
    url: str, 
    as_json: bool = True, 
    method: str = "GET", 
    data: dict | str | None = None,
    headers: dict[str, str] | None = None,
    output_format: str = "markdown"
) -> str:
    """
    Fetch content from a URL using different HTTP methods.
    
    Args:
        url: URL to fetch content from
        as_json: If True, validates content as JSON; if False, returns text content
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        data: Request body data (for POST/PUT requests)
        headers: Additional headers to include in the request
        output_format: If as_json=False, output format - "markdown", "clean_text", or "raw_html"
        
    Returns:
        String content from the URL (JSON, Markdown, clean text, or raw HTML)
        
    Raises:
        httpx.RequestError: For network-related errors
        json.JSONDecodeError: If as_json=True and content is not valid JSON
    """
    config = await get_http_client_config()
    
    # Merge additional headers with config headers (user headers override defaults)
    if headers:
        if config.get("headers"):
            config["headers"].update(headers)
        else:
            config["headers"] = headers
    
    async with httpx.AsyncClient(**config) as client:
        # Handle different HTTP methods
        method = method.upper()
        
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            if isinstance(data, dict):
                response = await client.post(url, json=data)
            else:
                response = await client.post(url, content=data)
        elif method == "PUT":
            if isinstance(data, dict):
                response = await client.put(url, json=data)
            else:
                response = await client.put(url, content=data)
        elif method == "DELETE":
            response = await client.delete(url)
        elif method == "PATCH":
            if isinstance(data, dict):
                response = await client.patch(url, json=data)
            else:
                response = await client.patch(url, content=data)
        elif method == "HEAD":
            response = await client.head(url)
        elif method == "OPTIONS":
            response = await client.options(url)
        else:
            # For any other method, use the generic request method
            if isinstance(data, dict):
                response = await client.request(method, url, json=data)
            else:
                response = await client.request(method, url, content=data)
        
        response.raise_for_status()
        
        if as_json and response.text:
            # Validate that it's valid JSON
            json.loads(response.text)
            return response.text
        elif not as_json:
            # For text content, apply format conversion
            return extract_text_content(response.text, output_format)
        else:
            return response.text


async def batch_fetch_urls(requests: list[str | dict[str, Any]], as_json: bool = True, output_format: str = "markdown") -> list[dict[str, Any]]:
    """
    Batch fetch content from multiple URLs concurrently.
    
    Args:
        requests: List of URLs (strings) or request objects with url, method, data, headers, output_format
        as_json: If True, validates content as JSON; if False, returns text content
        output_format: Default output format - "markdown", "clean_text", or "raw_html" (can be overridden per request)
        
    Returns:
        List of dictionaries with 'url', 'success', 'content', and optional 'error' keys
    """
    async def fetch_single(request: str | dict[str, Any]) -> dict[str, Any]:
        try:
            if isinstance(request, str):
                # Simple URL string
                content = await fetch_url_content(request, as_json=as_json, output_format=output_format)
                return {"url": request, "success": True, "content": content}
            else:
                # Request object with additional parameters
                url = request.get("url", "")
                method = request.get("method", "GET")
                data = request.get("data")
                headers = request.get("headers")
                request_output_format = request.get("output_format", output_format)
                
                content = await fetch_url_content(
                    url, as_json=as_json, method=method, data=data, headers=headers, 
                    output_format=request_output_format
                )
                return {"url": url, "success": True, "content": content}
        except Exception as e:
            url = request if isinstance(request, str) else request.get("url", "")
            return {"url": url, "success": False, "error": str(e)}
    
    tasks = [fetch_single(request) for request in requests]
    results = await asyncio.gather(*tasks)
    return list(results)


async def batch_extract_json(url_patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Batch extract JSON data from multiple URLs with different patterns.
    Optimized to fetch each unique URL only once for the same method/data combination.
    
    Args:
        url_patterns: List of dicts with 'url', optional 'pattern', 'method', 'data', 'headers' keys
        
    Returns:
        List of dictionaries with extraction results
    """
    # Group requests by URL and request parameters to minimize HTTP requests
    request_groups = {}
    for i, item in enumerate(url_patterns):
        url = item.get("url", "")
        pattern = item.get("pattern", "")
        method = item.get("method", "GET")
        data = item.get("data")
        headers = item.get("headers")
        
        if not url:
            # Handle missing URL case immediately
            continue
        
        # Create a unique key for the same URL with same request parameters
        import hashlib
        request_key = f"{url}:{method}:{json.dumps(data, sort_keys=True) if data else ''}:{json.dumps(headers, sort_keys=True) if headers else ''}"
        request_hash = hashlib.md5(request_key.encode()).hexdigest()
        
        if request_hash not in request_groups:
            request_groups[request_hash] = {"url": url, "method": method, "data": data, "headers": headers, "patterns": []}
        request_groups[request_hash]["patterns"].append((i, pattern))
    
    # Fetch each unique request once
    async def fetch_and_extract_for_request(request_info: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
        url = request_info["url"]
        method = request_info["method"]
        data = request_info["data"]
        headers = request_info["headers"]
        patterns_with_indices = request_info["patterns"]
        
        try:
            content = await fetch_url_content(url, as_json=True, method=method, data=data, headers=headers)
            results = []
            
            for index, pattern in patterns_with_indices:
                try:
                    extracted = extract_json(content, pattern)
                    results.append((index, {
                        "url": url, 
                        "pattern": pattern, 
                        "method": method,
                        "success": True, 
                        "content": extracted
                    }))
                except Exception as e:
                    results.append((index, {
                        "url": url, 
                        "pattern": pattern, 
                        "method": method,
                        "success": False, 
                        "error": str(e)
                    }))
            return results
        except Exception as e:
            # If URL fetch fails, all patterns for this request fail
            results = []
            for index, pattern in patterns_with_indices:
                results.append((index, {
                    "url": url, 
                    "pattern": pattern, 
                    "method": method,
                    "success": False, 
                    "error": str(e)
                }))
            return results
    
    # Create tasks for each unique request
    tasks = [fetch_and_extract_for_request(request_info) for request_info in request_groups.values()]
    request_results = await asyncio.gather(*tasks)
    
    # Flatten results and sort by original index to maintain order
    all_results = []
    for request_result_group in request_results:
        all_results.extend(request_result_group)
    
    # Handle missing URLs
    for i, item in enumerate(url_patterns):
        url = item.get("url", "")
        pattern = item.get("pattern", "")
        method = item.get("method", "GET")
        if not url:
            all_results.append((i, {
                "url": url, 
                "pattern": pattern, 
                "method": method,
                "success": False, 
                "error": "Missing URL"
            }))
    
    # Sort by index and return just the results
    all_results.sort(key=lambda x: x[0])
    return [result for _, result in all_results]
