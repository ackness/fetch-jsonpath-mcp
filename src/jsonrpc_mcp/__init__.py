"""JSONRPC MCP Server - A Model Context Protocol server for JSON data extraction."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fetch-jsonpath-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"
