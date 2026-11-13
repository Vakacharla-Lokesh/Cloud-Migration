"""
api/session_store.py — In-memory session registry.

Maps session_id → thread state so FastAPI endpoints and the SSE stream
can look up graph state without hitting the LangGraph checkpointer directly.

For production: swap the dict for Redis or a DB-backed store.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Literal, Optional


SessionStatus = Literal[
    "running",
    "awaiting_human",
    "completed",
    "failed",
]


@dataclass
class SessionEntry:
    session_id: str
    status: SessionStatus = "running"
    current_step: str = "initialising"
    errors: list[str] = field(default_factory=list)
    iac_file_path: Optional[str] = None
    generated_iac: Optional[str] = None
    # asyncio.Queue used to push SSE events to the streaming endpoint
    event_queue: asyncio.Queue = field(default_factory=asyncio.Queue)


class SessionStore:
    """Thread-safe (single-process) session registry."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionEntry] = {}

    def create(self, session_id: str) -> SessionEntry:
        entry = SessionEntry(session_id=session_id)
        self._sessions[session_id] = entry
        return entry

    def get(self, session_id: str) -> Optional[SessionEntry]:
        return self._sessions.get(session_id)

    def get_or_raise(self, session_id: str) -> SessionEntry:
        entry = self.get(session_id)
        if entry is None:
            raise KeyError(f"Session '{session_id}' not found")
        return entry

    def update(self, session_id: str, **kwargs: Any) -> None:
        entry = self.get_or_raise(session_id)
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

    async def push_event(self, session_id: str, event: dict) -> None:
        """Push an SSE event dict into the session's queue."""
        entry = self.get(session_id)
        if entry:
            await entry.event_queue.put(event)

    def all(self) -> list[SessionEntry]:
        return list(self._sessions.values())


# Module-level singleton — imported by routers and the graph runner
session_store = SessionStore()