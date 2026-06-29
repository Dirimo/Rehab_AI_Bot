"""API request/response shapes (Pydantic), separate from database models.

Why separate schemas from `models.py`?
- DB models describe tables (internal).
- Schemas describe what the API accepts/returns (public contract).
- We can add computed fields like `is_expired` without adding a DB column.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import ROLE_USER

# Roles the API accepts when creating a message.
MessageRole = Literal["user", "assistant", "system", "tool"]


class SessionRead(BaseModel):
    """What the client receives when it creates or fetches a session."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    expires_at: datetime
    is_expired: bool
    title: str | None = None


class MessageCreate(BaseModel):
    """Body for POST /messages — what the client sends to add one message."""

    session_id: str
    content: str = Field(min_length=1, max_length=16000)
    role: MessageRole = ROLE_USER


class MessageRead(BaseModel):
    """One message as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime


class ChatRequest(BaseModel):
    """Body for POST /chat — user sends a message, agent returns a reply."""

    session_id: str
    content: str = Field(min_length=1, max_length=16000)


class ChatResponse(BaseModel):
    """Agent loop result returned to the client."""

    session_id: str
    reply: str
    status: str = "completed"
