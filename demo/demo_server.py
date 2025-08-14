#!/usr/bin/env python3
"""
Demo HTTP server that returns test JSON data for testing the MCP server.
"""

import sys
from typing import Any

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    print("Error: FastAPI and uvicorn are required but not installed.")
    print("Please install them with: pip install fastapi uvicorn")
    sys.exit(1)

# Test JSON data
TEST_DATA = {
    "foo": [{"baz": 1, "qux": "a"}, {"baz": 2, "qux": "b"}],
    "bar": {
        "items": [10, 20, 30], 
        "config": {
            "enabled": True, 
            "name": "example", 
            "nested": {
                "key1": "value1", 
                "key2": "value2"
            }
        }
    },
    "metadata": {
        "version": "1.0.0", 
        "timestamp": "2023-01-01T00:00:00Z"
    },
}

# Create FastAPI app
app = FastAPI(title="Demo JSON Server", description="Returns test JSON data for MCP server testing")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_json() -> dict[str, Any]:
    """Return test JSON data."""
    return TEST_DATA

@app.post("/")
async def post_json() -> dict[str, Any]:
    """Return test JSON data (same as GET for simplicity)."""
    return TEST_DATA

def start_server(port: int = 8080, host: str = "localhost"):
    """Start the FastAPI server on port 8080 only."""
    print(f"Demo JSON server starting at http://{host}:{port}")
    print("Returns test JSON data for MCP server testing")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except OSError as e:
        if e.errno in (10048, 98):  # Windows/Linux EADDRINUSE
            print(f"Error: Port {port} is already in use. Please free up port {port} and try again.")
        else:
            print(f"Error: Cannot bind to port {port}: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)

if __name__ == "__main__":
    start_server(8080)