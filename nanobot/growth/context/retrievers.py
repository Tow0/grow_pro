from __future__ import annotations

from typing import Protocol

from nanobot.growth.context.ranking import RetrievedItem


class StructuredStateRetriever(Protocol):
    """Reads domain state such as goals, habits, tasks, and feedback."""

    async def retrieve(self, *, user_id: str, limit: int = 10) -> list[RetrievedItem]: ...


class LexicalMemoryRetriever(Protocol):
    """Reads durable markdown memory with keyword or lexical matching."""

    async def retrieve(self, *, query: str, limit: int = 10) -> list[RetrievedItem]: ...


class RecentHistoryRetriever(Protocol):
    """Reads near-term session/history summaries for recency-sensitive context."""

    async def retrieve(
        self,
        *,
        session_id: str | None,
        user_id: str,
        limit: int = 10,
    ) -> list[RetrievedItem]: ...


class VectorRetriever(Protocol):
    """Reserved extension point for optional vector search in later versions."""

    async def retrieve(self, *, query: str, limit: int = 10) -> list[RetrievedItem]: ...
