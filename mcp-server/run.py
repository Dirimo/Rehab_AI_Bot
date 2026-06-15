"""Launch the RehabBot MCP server (Member 3).

Usage (from mcp-server/ folder, venv active):
    python run.py
"""

from app.config import settings
from app.server import mcp

if __name__ == "__main__":
    mcp.run(transport="http", host=settings.MCP_HOST, port=settings.MCP_PORT)
