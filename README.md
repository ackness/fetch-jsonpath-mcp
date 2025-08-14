# JSONRPC MCP

A Model Context Protocol (MCP) server that provides tools for fetching and extracting JSON data from URLs using JSONPath patterns.

## Quick Start

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
uv run jsonrpc-mcp
```

## Available Tools

### `get-json`
Extract JSON data using JSONPath patterns.

```json
{
  "name": "get-json",
  "arguments": {
    "url": "http://localhost:8080",
    "pattern": "foo[*].baz"
  }
}
```
Returns: `[1, 2]`

### `get-text`
Get raw text content from any URL.

```json
{
  "name": "get-text",
  "arguments": {
    "url": "http://localhost:8080"
  }
}
```

### `batch-get-json`
Process multiple URLs with different JSONPath patterns.

```json
{
  "name": "batch-get-json",
  "arguments": {
    "requests": [
      {"url": "http://localhost:8080", "pattern": "foo[*].baz"},
      {"url": "http://localhost:8080", "pattern": "bar.items[*]"}
    ]
  }
}
```

### `batch-get-text`
Get text content from multiple URLs.

```json
{
  "name": "batch-get-text",
  "arguments": {
    "urls": ["http://localhost:8080", "http://localhost:8080"]
  }
}
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

## JSONPath Examples

| Pattern | Result | Description |
|---------|--------|-------------|
| `foo[*].baz` | `[1, 2]` | Get all baz values |
| `bar.items[*]` | `[10, 20, 30]` | Get all items |
| `metadata.version` | `["1.0.0"]` | Get version |

## Configuration

Set environment variables:

```bash
export JSONRPC_MCP_TIMEOUT=30
export JSONRPC_MCP_HEADERS='{"Authorization": "Bearer token"}'
export JSONRPC_MCP_PROXY="http://proxy.example.com:8080"
```

## Development

```bash
# Run tests
pytest

# Check code quality
ruff check --fix
```