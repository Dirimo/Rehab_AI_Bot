"""Development launcher for the RehabBot backend.

Why this file exists:
On Windows, uvicorn creates its asyncio event loop BEFORE importing the app,
so setting the event-loop policy inside app/main.py runs too late. Here we set
the SelectorEventLoop policy first (psycopg's async mode requires it), then
start uvicorn.

Usage (from the backend/ folder, venv active):
    python run.py
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # set True later for auto-reload during active dev
    )
