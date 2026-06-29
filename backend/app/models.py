"""Database schema for RehabBot (tables: sessions, messages, tool_logs).

Each class with `table=True` becomes a real PostgreSQL table. SQLModel turns
these Python classes into both the DB schema AND the data-validation models.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    """Current time as a timezone-aware UTC datetime (stored consistently)."""
    return datetime.now(timezone.utc)


# Roles a message can have, kept as plain strings for simplicity.
# "system"    -> instructions to the model (system prompt)
# "user"      -> what the human typed
# "assistant" -> what the LLM answered
# "tool"      -> the result returned by an MCP tool, fed back to the model
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_TOOL = "tool"


class Session(SQLModel, table=True):
    """A single conversation. Its `id` is what the browser stores to resume."""

    __tablename__ = "sessions"

    # A random URL-safe id (e.g. "a1b2c3..."). The frontend keeps this in
    # localStorage to reconnect to the same conversation.
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)

    created_at: datetime = Field(default_factory=_now)

    # When this session becomes invalid. Computed at creation time by the
    # sessions router using settings.SESSION_EXPIRATION_DAYS.
    expires_at: datetime | None = Field(default=None)

    # Automatically set to the first message's text (truncated) to display in the UI history.
    title: str | None = Field(default=None)


class Message(SQLModel, table=True):
    """One message belonging to a session."""

    __tablename__ = "messages"

    id: int | None = Field(default=None, primary_key=True)

    # Links this message to its conversation. index=True speeds up
    # "fetch all messages for session X" queries.
    session_id: str = Field(foreign_key="sessions.id", index=True)

    role: str  # one of the ROLE_* constants above
    content: str

    created_at: datetime = Field(default_factory=_now)


class ToolLog(SQLModel, table=True):
    """Audit record of one MCP tool call made during the agent loop."""

    __tablename__ = "tool_logs"

    id: int | None = Field(default=None, primary_key=True)

    session_id: str = Field(foreign_key="sessions.id", index=True)

    tool_name: str  # e.g. "search_exercises"

    # Free-form JSON for the tool's input arguments and its output result.
    # On PostgreSQL this maps to a JSON column.
    arguments: dict = Field(default_factory=dict, sa_column=Column(JSON))
    result: dict = Field(default_factory=dict, sa_column=Column(JSON))

    status: str = "success"  # "success" or "error"
    duration_ms: int | None = None

    created_at: datetime = Field(default_factory=_now)
