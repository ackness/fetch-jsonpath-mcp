import json

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from jsonrpc_mcp.utils import batch_extract_json, batch_fetch_urls, extract_json, fetch_url_content

server = Server("fetch-jsonpath-mcp", version="1.1.2")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="fetch-json",
            description=(
                "Extract JSON content from a URL using JSONPath with extended features. "
                "Supports extensions like len, keys, filtering, arithmetic operations, and more. "
                "If 'pattern' is omitted or empty, the entire JSON document is returned. "
                "Supports different HTTP methods (default: GET)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to get raw JSON from",
                    },
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Extended JSONPath pattern supporting: "
                            "Basic: 'foo[*].baz', 'bar.items[*]'; "
                            "Extensions: '$.data.`len`', '$.users.`keys`', '$.field.`str()`'; "
                            "Filtering: '$.items[?(@.price > 10)]', '$.users[?name = \"John\"]'; "
                            "Arithmetic: '$.a + $.b', '$.items[*].price * 1.2'; "
                            "Text ops: '$.text.`sub(/old/, new)`', '$.csv.`split(\",\")'"
                        ),
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method to use (GET, POST, PUT, DELETE, PATCH, etc.). Default is GET.",
                        "default": "GET"
                    },
                    "data": {
                        "type": ["object", "string", "null"],
                        "description": "Request body data for POST/PUT/PATCH requests. Can be a JSON object or string.",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Additional HTTP headers to include in the request",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="fetch-text",
            description="Fetch text content from a URL using various HTTP methods. Defaults to converting HTML to Markdown format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to get text content from",
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method to use (GET, POST, PUT, DELETE, PATCH, etc.). Default is GET.",
                        "default": "GET"
                    },
                    "data": {
                        "type": ["object", "string", "null"],
                        "description": "Request body data for POST/PUT/PATCH requests. Can be a JSON object or string.",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Additional HTTP headers to include in the request",
                        "additionalProperties": {"type": "string"}
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format: 'markdown' (default), 'clean_text', or 'raw_html'.",
                        "enum": ["markdown", "clean_text", "raw_html"],
                        "default": "markdown"
                    }
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="batch-fetch-json",
            description=(
                "Batch extract JSON content from multiple URLs with different extended JSONPath patterns. "
                "Supports all JSONPath extensions and optimizes by fetching each unique request only once. "
                "Executes requests concurrently for better performance. Supports different HTTP methods."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "requests": {
                        "type": "array",
                        "description": "Array of request objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "The URL to get JSON from",
                                },
                                "pattern": {
                                    "type": "string",
                                    "description": (
                                        "Extended JSONPath pattern (optional) supporting: "
                                        "Basic: 'foo[*].baz'; Extensions: '$.data.`len`'; "
                                        "Filtering: '$.items[?(@.price > 10)]'; "
                                        "Arithmetic: '$.a + $.b'; Text ops: '$.text.`sub(/old/, new)`'"
                                    ),
                                },
                                "method": {
                                    "type": "string",
                                    "description": "HTTP method to use (GET, POST, PUT, DELETE, PATCH, etc.). Default is GET.",
                                    "default": "GET"
                                },
                                "data": {
                                    "type": ["object", "string", "null"],
                                    "description": "Request body data for POST/PUT/PATCH requests. Can be a JSON object or string.",
                                },
                                "headers": {
                                    "type": "object",
                                    "description": "Additional HTTP headers to include in the request",
                                    "additionalProperties": {"type": "string"}
                                }
                            },
                            "required": ["url"],
                        },
                    },
                },
                "required": ["requests"],
            },
        ),
        types.Tool(
            name="batch-fetch-text",
            description=(
                "Batch fetch raw text content from multiple URLs using various HTTP methods. "
                "Executes requests concurrently for better performance."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "requests": {
                        "type": "array",
                        "description": "Array of URLs (strings) or request objects",
                        "items": {
                            "oneOf": [
                                {"type": "string"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "url": {
                                            "type": "string",
                                            "description": "The URL to get text content from",
                                        },
                                        "method": {
                                            "type": "string",
                                            "description": "HTTP method to use (GET, POST, PUT, DELETE, PATCH, etc.). Default is GET.",
                                            "default": "GET"
                                        },
                                        "data": {
                                            "type": ["object", "string", "null"],
                                            "description": "Request body data for POST/PUT/PATCH requests. Can be a JSON object or string.",
                                        },
                                        "headers": {
                                            "type": "object",
                                            "description": "Additional HTTP headers to include in the request",
                                            "additionalProperties": {"type": "string"}
                                        },
                                        "output_format": {
                                            "type": "string",
                                            "description": "Output format: 'markdown' (default), 'clean_text', or 'raw_html'.",
                                            "enum": ["markdown", "clean_text", "raw_html"],
                                            "default": "markdown"
                                        }
                                    },
                                    "required": ["url"]
                                }
                            ]
                        },
                    },
                },
                "required": ["requests"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(tool_name: str, args: dict) -> list[types.TextContent]:
    try:
        if tool_name == "fetch-json":
            url = args.get("url")
            if not url or not isinstance(url, str):
                result = "Failed to call tool, error: Missing required property: url"
            else:
                method = args.get("method", "GET")
                data = args.get("data")
                headers = args.get("headers")
                pattern = args.get("pattern", "")
                response_result = await handle_get_json(url, pattern, method, data, headers)
                result = json.dumps(response_result)
                
        elif tool_name == "fetch-text":
            url = args.get("url")
            if not url or not isinstance(url, str):
                result = "Failed to call tool, error: Missing required property: url"
            else:
                method = args.get("method", "GET")
                data = args.get("data")
                headers = args.get("headers")
                output_format = args.get("output_format", "markdown")
                result = await fetch_url_content(url, as_json=False, method=method, data=data, headers=headers, output_format=output_format)
                
        elif tool_name == "batch-fetch-json":
            requests = args.get("requests", [])
            if not isinstance(requests, list) or not requests:
                result = "Failed to call tool, error: Missing or empty 'requests' array"
            else:
                response_result = await batch_extract_json(requests)
                result = json.dumps(response_result)
                
        elif tool_name == "batch-fetch-text":
            requests = args.get("requests", [])
            if not isinstance(requests, list) or not requests:
                result = "Failed to call tool, error: Missing or empty 'requests' array"
            else:
                output_format = args.get("output_format", "markdown")
                response_result = await batch_fetch_urls(requests, as_json=False, output_format=output_format)
                result = json.dumps(response_result)
                
        else:
            result = f"Unknown tool: {tool_name}"
    except Exception as e:
        result = f"Failed to call tool, error: {e}"

    return [types.TextContent(type="text", text=result)]


async def handle_get_json(
    url: str, 
    pattern: str = "", 
    method: str = "GET", 
    data: dict | str | None = None,
    headers: dict[str, str] | None = None
) -> list:
    """Handle single JSON extraction request."""
    content = await fetch_url_content(url, as_json=True, method=method, data=data, headers=headers)
    return extract_json(content, pattern)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fetch-jsonpath-mcp",
                server_version="1.1.2",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def run():
    """Entry point for the MCP server."""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    run()
