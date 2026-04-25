from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from nanobot.agent.memory import MemoryStore
from nanobot.growth.contracts.memory import MemoryWriteCandidate

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class RelevantHistoryHit(BaseModel):
    timestamp: str
    content: str
    score: float


class CoreMemorySnapshot(BaseModel):
    user_content: str = ""
    memory_content: str = ""
    history_candidates: int = 0
    history_hits: list[RelevantHistoryHit] = Field(default_factory=list)

    def render_memory_section(self) -> str:
        parts: list[str] = []
        if self.user_content:
            parts.append(f"## USER.md\n{self.user_content}")
        if self.memory_content:
            parts.append(f"## MEMORY.md\n{self.memory_content}")
        return "\n\n".join(parts)

    def render_history_section(self) -> str:
        if not self.history_hits:
            return ""
        return "\n".join(
            f"- [{hit.timestamp}] {hit.content}"
            for hit in self.history_hits
        )


class HermesStyleMemoryService:
    """Small-core memory service built on nanobot's file-based memory store."""

    def __init__(self, workspace: str | Path, *, history_limit: int = 5) -> None:
        self._store = MemoryStore(Path(workspace).expanduser().resolve())
        self._history_limit = history_limit
        self._history_index_file = self._store.memory_dir / "history_index.sqlite3"

    @property
    def store(self) -> MemoryStore:
        return self._store

    def build_snapshot(
        self,
        query: str,
        *,
        history_limit: int | None = None,
    ) -> CoreMemorySnapshot:
        entries = self._store.read_unprocessed_history(0)
        hits = self._search_history(
            query,
            entries,
            limit=history_limit or self._history_limit,
        )
        return CoreMemorySnapshot(
            user_content=self._store.read_user().strip(),
            memory_content=self._store.read_memory().strip(),
            history_candidates=len(entries),
            history_hits=hits,
        )

    def search_history(self, query: str, *, limit: int = 5) -> list[RelevantHistoryHit]:
        entries = self._store.read_unprocessed_history(0)
        return self._search_history(query, entries, limit=limit)

    def _search_history(
        self,
        query: str,
        entries: list[dict[str, Any]],
        *,
        limit: int,
    ) -> list[RelevantHistoryHit]:
        if not entries or limit <= 0:
            return []

        query_tokens = self._tokenize(query)
        if query_tokens:
            indexed_hits = self._search_history_with_index(
                query_tokens,
                entries,
                limit=limit,
            )
            if indexed_hits is not None:
                return indexed_hits
        return self._search_history_lexical(query_tokens, entries, limit=limit)

    def _search_history_with_index(
        self,
        query_tokens: set[str],
        entries: list[dict[str, Any]],
        *,
        limit: int,
    ) -> list[RelevantHistoryHit] | None:
        if not query_tokens:
            return None

        try:
            with sqlite3.connect(self._history_index_file) as conn:
                conn.row_factory = sqlite3.Row
                self._ensure_history_index(conn, entries)
                rows = conn.execute(
                    """
                    SELECT entries.timestamp, entries.content, entries.row_order
                    FROM history_fts
                    JOIN history_entries AS entries ON entries.entry_id = history_fts.rowid
                    WHERE history_fts MATCH ?
                    LIMIT ?
                    """,
                    (_fts_match_query(query_tokens), max(limit * 5, limit)),
                ).fetchall()
        except (OSError, sqlite3.DatabaseError):
            return None

        total = len(entries)
        scored: list[RelevantHistoryHit] = []
        for row in rows:
            content = str(row["content"] or "").strip()
            if not content:
                continue
            overlap = len(query_tokens & self._tokenize(content)) / len(query_tokens)
            if overlap <= 0.0:
                continue

            recency = int(row["row_order"]) / total
            scored.append(
                RelevantHistoryHit(
                    timestamp=str(row["timestamp"] or "?"),
                    content=content,
                    score=overlap * 0.7 + recency * 0.3,
                )
            )

        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:limit]

    def _ensure_history_index(
        self,
        conn: sqlite3.Connection,
        entries: list[dict[str, Any]],
    ) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS history_index_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS history_entries (
                entry_id INTEGER PRIMARY KEY,
                cursor TEXT,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                row_order INTEGER NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS history_fts USING fts5(content);
            """
        )

        state = self._history_index_state(entries)
        current = {
            str(row[0]): str(row[1])
            for row in conn.execute("SELECT key, value FROM history_index_meta").fetchall()
        }
        if current == state:
            return

        rows = [
            (
                index,
                str(entry.get("cursor") or ""),
                str(entry.get("timestamp") or "?"),
                str(entry.get("content") or "").strip(),
                index,
            )
            for index, entry in enumerate(entries, start=1)
            if str(entry.get("content") or "").strip()
        ]

        with conn:
            conn.execute("DELETE FROM history_entries")
            conn.execute("DELETE FROM history_fts")
            conn.execute("DELETE FROM history_index_meta")
            if rows:
                conn.executemany(
                    """
                    INSERT INTO history_entries (entry_id, cursor, timestamp, content, row_order)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                conn.executemany(
                    "INSERT INTO history_fts(rowid, content) VALUES (?, ?)",
                    [(row[0], row[3]) for row in rows],
                )
            conn.executemany(
                "INSERT INTO history_index_meta(key, value) VALUES (?, ?)",
                list(state.items()),
            )

    def _history_index_state(self, entries: list[dict[str, Any]]) -> dict[str, str]:
        try:
            stat = self._store.history_file.stat()
        except OSError:
            return {
                "mtime_ns": "0",
                "size": "0",
                "count": str(len(entries)),
            }
        return {
            "mtime_ns": str(stat.st_mtime_ns),
            "size": str(stat.st_size),
            "count": str(len(entries)),
        }

    def _search_history_lexical(
        self,
        query_tokens: set[str],
        entries: list[dict[str, Any]],
        *,
        limit: int,
    ) -> list[RelevantHistoryHit]:
        total = len(entries)
        scored: list[RelevantHistoryHit] = []
        for index, entry in enumerate(entries):
            content = str(entry.get("content") or "").strip()
            if not content:
                continue

            content_tokens = self._tokenize(content)
            overlap = 0.0
            if query_tokens and content_tokens:
                overlap = len(query_tokens & content_tokens) / len(query_tokens)

            recency = (index + 1) / total
            score = overlap * 0.7 + recency * 0.3
            if query_tokens and overlap <= 0.0:
                continue

            scored.append(
                RelevantHistoryHit(
                    timestamp=str(entry.get("timestamp") or "?"),
                    content=content,
                    score=score,
                )
            )

        if not query_tokens and not scored:
            tail = entries[-limit:]
            return [
                RelevantHistoryHit(
                    timestamp=str(entry.get("timestamp") or "?"),
                    content=str(entry.get("content") or "").strip(),
                    score=(index + 1) / len(tail),
                )
                for index, entry in enumerate(tail)
                if str(entry.get("content") or "").strip()
            ]

        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:limit]

    def persist_candidate(self, candidate: MemoryWriteCandidate) -> bool:
        """Persist one approved candidate into the small core memory files."""

        if candidate.scope == "session":
            return False

        target = "user" if self._use_user_file(candidate) else "memory"
        existing = (
            self._store.read_user()
            if target == "user"
            else self._store.read_memory()
        )
        lines = [line.rstrip() for line in existing.splitlines()]
        entry = f"- {candidate.content.strip()}"
        normalized = {line.casefold() for line in lines if line.strip()}
        if entry.casefold() in normalized:
            return False

        lines.append(entry)
        updated = "\n".join(line for line in lines if line.strip()).strip()
        if updated:
            updated += "\n"

        if target == "user":
            self._store.write_user(updated)
        else:
            self._store.write_memory(updated)
        return True

    @staticmethod
    def _use_user_file(candidate: MemoryWriteCandidate) -> bool:
        return candidate.scope == "user" or candidate.type == "preference"

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {match.group(0).lower() for match in _TOKEN_RE.finditer(text)}


def _fts_match_query(tokens: set[str]) -> str:
    return " OR ".join(f'"{token}"' for token in sorted(tokens))
