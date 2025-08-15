import json

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from jsonrpc_mcp.utils import batch_extract_json, batch_fetch_urls, extract_json, fetch_url_content

server = Server("fetch-jsonpath-mcp", version="1.0.2")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get-json",
            description=(
                "Extract JSON content from a URL using JSONPath with extended features. "
                "Supports extensions like len, keys, filtering, arithmetic operations, and more. "
                "If 'pattern' is omitted or empty, the entire JSON document is returned."
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
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="get-text",
            description="Get raw text content from a URL (not limited to JSON).",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to get text content from",
                    },
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="batch-get-json",
            description=(
                "Batch extract JSON content from multiple URLs with different extended JSONPath patterns. "
                "Supports all JSONPath extensions and optimizes by fetching each unique URL only once. "
                "Executes requests concurrently for better performance."
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
                            },
                            "required": ["url"],
                        },
                    },
                },
                "required": ["requests"],
            },
        ),
        types.Tool(
            name="batch-get-text",
            description=(
                "Batch get raw text content from multiple URLs. "
                "Executes requests concurrently for better performance."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "description": "Array of URLs to fetch",
                        "items": {
                            "type": "string",
                        },
                    },
                },
                "required": ["urls"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(tool_name: str, args: dict) -> list[types.TextContent]:
    try:
        if tool_name == "get-json":
            url = args.get("url")
            if not url or not isinstance(url, str):
                result = "Failed to call tool, error: Missing required property: url"
            else:
                response_result = await handle_get_json(url, args.get("pattern", ""))
                result = json.dumps(response_result)
                
        elif tool_name == "get-text":
            url = args.get("url")
            if not url or not isinstance(url, str):
                result = "Failed to call tool, error: Missing required property: url"
            else:
                result = await fetch_url_content(url, as_json=False)
                
        elif tool_name == "batch-get-json":
            requests = args.get("requests", [])
            if not isinstance(requests, list) or not requests:
                result = "Failed to call tool, error: Missing or empty 'requests' array"
            else:
                response_result = await batch_extract_json(requests)
                result = json.dumps(response_result)
                
        elif tool_name == "batch-get-text":
            urls = args.get("urls", [])
            if not isinstance(urls, list) or not urls:
                result = "Failed to call tool, error: Missing or empty 'urls' array"
            else:
                response_result = await batch_fetch_urls(urls, as_json=False)
                result = json.dumps(response_result)
                
        else:
            result = f"Unknown tool: {tool_name}"
    except Exception as e:
        result = f"Failed to call tool, error: {e}"

    return [types.TextContent(type="text", text=result)]


async def handle_get_json(url: str, pattern: str = "") -> list:
    """Handle single JSON extraction request."""
    content = await fetch_url_content(url, as_json=True)
    return extract_json(content, pattern)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fetch-jsonpath-mcp",
                server_version="1.0.2",
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
