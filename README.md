# Fetch JSONPath MCP

[![PyPI Downloads](https://img.shields.io/pypi/dm/fetch-jsonpath-mcp)](https://pypi.org/project/fetch-jsonpath-mcp/)
[![简体中文](https://img.shields.io/badge/docs-简体中文-red)](./docs/README.zh-CN.md)

A Model Context Protocol (MCP) server that provides tools for fetching JSON data and web content from URLs. Features intelligent content extraction, multiple HTTP methods, and browser-like headers for reliable web scraping.

## 🎯 Why Use This?

**Reduce LLM Token Usage & Hallucination** - Instead of fetching entire JSON responses and wasting tokens, extract only the data you need.

### Traditional Fetch vs JSONPath Extract

**❌ Traditional fetch (wasteful):**
```json
// API returns 2000+ tokens
{
  "data": [
    {
      "id": 1,
      "name": "Alice",
      "email": "alice@example.com", 
      "avatar": "https://...",
      "profile": {
        "bio": "Long bio text...",
        "settings": {...},
        "preferences": {...},
        "metadata": {...}
      },
      "posts": [...],
      "followers": [...],
      "created_at": "2023-01-01",
      "updated_at": "2024-01-01"
    },
    // ... 50 more users
  ],
  "pagination": {...},
  "meta": {...}
}
```

**✅ JSONPath extract (efficient):**
```json
// Only 10 tokens - exactly what you need!
["Alice", "Bob", "Charlie"]
```

Using pattern: `data[*].name` saves **99% tokens** and eliminates model hallucination from irrelevant data.

## Installation

For most IDEs, use the `uvx` tool to run the server.

```json
{
  "mcpServers": {
    "fetch-jsonpath-mcp": {
      "command": "uvx",
      "args": [
        "fetch-jsonpath-mcp"
      ]
    }
  }
}
```

<details>
<summary><b>Install in Claude Code</b></summary>

```bash
claude mcp add fetch-jsonpath-mcp -- uvx fetch-jsonpath-mcp
```

</details>

<details>
<summary><b>Install in Cursor</b></summary>

```json
{
  "mcpServers": {
    "fetch-jsonpath-mcp": {
      "command": "uvx",
      "args": ["fetch-jsonpath-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>Install in Windsurf</b></summary>

Add this to your Windsurf MCP config file. See [Windsurf MCP docs](https://docs.windsurf.com/windsurf/cascade/mcp) for more info.

#### Windsurf Local Server Connection

```json
{
  "mcpServers": {
    "fetch-jsonpath-mcp": {
      "command": "uvx",
      "args": ["fetch-jsonpath-mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>Install in VS Code</b></summary>

```json
"mcp": {
  "servers": {
    "fetch-jsonpath-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["fetch-jsonpath-mcp"]
    }
  }
}
```

</details>

## Development Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Start Demo Server (Optional)

```bash
# Install demo server dependencies
uv add fastapi uvicorn

# Start demo server on port 8080
uv run demo-server
```

### 3. Run MCP Server

```bash
uv run fetch-jsonpath-mcp
```

## Demo Server Data

The demo server at `http://localhost:8080` returns:

```json
{
  "foo": [{"baz": 1, "qux": "a"}, {"baz": 2, "qux": "b"}],
  "bar": {
    "items": [10, 20, 30], 
    "config": {"enabled": true, "name": "example"}
  },
  "metadata": {"version": "1.0.0"}
}
```

## Available Tools

### `fetch-json`
Extract JSON data using JSONPath patterns with support for all HTTP methods.

```json
{
  "name": "fetch-json",
  "arguments": {
    "url": "http://localhost:8080",
    "pattern": "foo[*].baz",
    "method": "GET"
  }
}
```
Returns: `[1, 2]`

**Parameters:**
- `url` (required): Target URL
- `pattern` (optional): JSONPath pattern for data extraction
- `method` (optional): HTTP method (GET, POST, PUT, DELETE, etc.) - Default: "GET"
- `data` (optional): Request body for POST/PUT requests
- `headers` (optional): Additional HTTP headers

### `fetch-text`
Fetch web content with intelligent text extraction. **Defaults to Markdown format** for better readability.

```json
{
  "name": "fetch-text",
  "arguments": {
    "url": "http://localhost:8080",
    "output_format": "clean_text"
  }
}
```
Returns: Clean text representation of the JSON data

**Output Formats:**
- `"markdown"` (default): Converts HTML to clean Markdown format
- `"clean_text"`: Pure text with HTML tags removed  
- `"raw_html"`: Original HTML content

**Parameters:**
- `url` (required): Target URL
- `method` (optional): HTTP method - Default: "GET"
- `data` (optional): Request body for POST/PUT requests
- `headers` (optional): Additional HTTP headers
- `output_format` (optional): Output format - Default: "markdown"

### `batch-fetch-json`
Process multiple URLs with different JSONPath patterns concurrently.

```json
{
  "name": "batch-fetch-json",
  "arguments": {
    "requests": [
      {"url": "http://localhost:8080", "pattern": "foo[*].baz"},
      {"url": "http://localhost:8080", "pattern": "bar.items[*]"}
    ]
  }
}
```
Returns: `[{"url": "http://localhost:8080", "pattern": "foo[*].baz", "success": true, "content": [1, 2]}, {"url": "http://localhost:8080", "pattern": "bar.items[*]", "success": true, "content": [10, 20, 30]}]`

**Request Object Parameters:**
- `url` (required): Target URL
- `pattern` (optional): JSONPath pattern
- `method` (optional): HTTP method - Default: "GET" 
- `data` (optional): Request body
- `headers` (optional): Additional HTTP headers

### `batch-fetch-text`
Fetch content from multiple URLs with intelligent text extraction.

```json
{
  "name": "batch-fetch-text",
  "arguments": {
    "requests": [
      "http://localhost:8080",
      {"url": "http://localhost:8080", "output_format": "raw_html"}
    ],
    "output_format": "markdown"
  }
}
```
Returns: `[{"url": "http://localhost:8080", "success": true, "content": "# Demo Server Data\n\n..."}, {"url": "http://localhost:8080", "success": true, "content": "{\"foo\": [{\"baz\": 1, \"qux\": \"a\"}, {\"baz\": 2, \"qux\": \"b\"}]..."}]`

**Supports:**
- Simple URL strings
- Full request objects with custom methods and headers
- Mixed input types in the same batch

## JSONPath Examples

This project uses [jsonpath-ng](https://github.com/h2non/jsonpath-ng) for JSONPath implementation.

| Pattern | Result | Description | 
|---------|--------|-------------|
| `foo[*].baz` | `[1, 2]` | Get all baz values | 
| `bar.items[*]` | `[10, 20, 30]` | Get all items | 
| `metadata.version` | `["1.0.0"]` | Get version | 

For complete JSONPath syntax reference, see the [jsonpath-ng documentation](https://github.com/h2non/jsonpath-ng#jsonpath-syntax).

## 🚀 Performance Benefits

- **Token Efficiency**: Extract only needed data, not entire JSON responses
- **Faster Processing**: Smaller payloads = faster LLM responses  
- **Reduced Hallucination**: Less irrelevant data = more accurate outputs
- **Cost Savings**: Fewer tokens = lower API costs
- **Better Focus**: Clean data helps models stay on task
- **Smart Headers**: Default browser headers prevent blocking and improve access
- **Markdown Conversion**: Clean, readable format that preserves structure

## Configuration

Set environment variables to customize behavior:

```bash
# Request timeout in seconds (default: 10.0)
export JSONRPC_MCP_TIMEOUT=30

# SSL verification (default: true)
export JSONRPC_MCP_VERIFY=false

# Follow redirects (default: true)
export JSONRPC_MCP_FOLLOW_REDIRECTS=true

# Custom headers (will be merged with default browser headers)
export JSONRPC_MCP_HEADERS='{"Authorization": "Bearer token"}'

# HTTP proxy configuration
export JSONRPC_MCP_PROXY="http://proxy.example.com:8080"
```

**Default Browser Headers**: The server automatically includes realistic browser headers to prevent blocking:
- User-Agent: Chrome browser simulation
- Accept: Standard browser content types
- Accept-Language, Accept-Encoding: Browser defaults
- Security headers: Sec-Fetch-* headers for modern browsers

Custom headers in `JSONRPC_MCP_HEADERS` will override defaults when there are conflicts.

## Development

```bash
# Run tests
pytest

# Check code quality
ruff check --fix

# Build and test locally
uv build
```

## What's New in v1.1.0

- ✨ **Multi-Method HTTP Support**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- 🔄 **Tool Renaming**: `get-json` → `fetch-json`, `get-text` → `fetch-text` 
- 📄 **Markdown Conversion**: Default HTML to Markdown conversion with `markdownify`
- 🌐 **Smart Browser Headers**: Automatic browser simulation headers
- 🎛️ **Format Control**: Three output formats for text content (markdown, clean_text, raw_html)
- 🚀 **Enhanced Batch Processing**: Support for different methods in batch operations