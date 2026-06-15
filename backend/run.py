"""Development launcher for the RehabBot backend.

Why this file exists:
On Windows, psycopg async cannot use the default ProactorEventLoop.
We must start uvicorn on a SelectorEventLoop. On Python 3.14+ the old
WindowsSelectorEventLoopPolicy is deprecated and no longer reliable, so we
use asyncio.run(..., loop_factory=...) instead.

Usage (from the backend/ folder, venv active):
    python run.py
"""

from __future__ import annotations

import asyncio
import selectors
import sys

import uvicorn


def _windows_loop_factory() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


async def _serve() -> None:
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(_serve(), loop_factory=_windows_loop_factory)
    else:
        asyncio.run(_serve())
