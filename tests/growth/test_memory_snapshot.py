from __future__ import annotations

import json
import sqlite3

from nanobot.growth.contracts.memory import MemoryWriteCandidate
from nanobot.growth.memory.snapshot import HermesStyleMemoryService


def _write_history(workspace, entries: list[dict[str, object]]) -> None:
    memory_dir = workspace / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    history_file = memory_dir / "history.jsonl"
    with history_file.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def test_build_snapshot_reads_core_memory_and_history(tmp_path) -> None:
    (tmp_path / "USER.md").write_text("Prefers short plans.\n", encoding="utf-8")
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "MEMORY.md").write_text("Goal: finish weekly review.\n", encoding="utf-8")
    _write_history(
        tmp_path,
        [
            {"cursor": 1, "timestamp": "2026-04-20 09:00", "content": "Went for a long run."},
            {"cursor": 2, "timestamp": "2026-04-21 08:00", "content": "Asked for a short morning plan."},
        ],
    )

    service = HermesStyleMemoryService(tmp_path)
    snapshot = service.build_snapshot("short morning plan")

    assert snapshot.user_content == "Prefers short plans."
    assert snapshot.memory_content == "Goal: finish weekly review."
    assert snapshot.history_candidates == 2
    assert snapshot.history_hits[0].content == "Asked for a short morning plan."


def test_persist_candidate_routes_preferences_to_user_file_and_dedupes(tmp_path) -> None:
    service = HermesStyleMemoryService(tmp_path)
    candidate = MemoryWriteCandidate(
        scope="user",
        type="preference",
        content="User prefers short morning plans.",
        provenance="explicit_user",
        confidence=1.0,
        reason="The user explicitly asked to remember this.",
    )

    assert service.persist_candidate(candidate) is True
    assert service.persist_candidate(candidate) is False

    assert (
        (tmp_path / "USER.md").read_text(encoding="utf-8")
        == "- User prefers short morning plans.\n"
    )


def test_session_scope_candidate_is_not_persisted(tmp_path) -> None:
    service = HermesStyleMemoryService(tmp_path)
    candidate = MemoryWriteCandidate(
        scope="session",
        type="strategy",
        content="Use a one-off nudge in this session.",
        provenance="observed",
        confidence=0.8,
        reason="Only relevant to the current session.",
    )

    assert service.persist_candidate(candidate) is False
    assert (tmp_path / "memory" / "MEMORY.md").exists() is False


def test_search_history_builds_sqlite_index(tmp_path) -> None:
    _write_history(
        tmp_path,
        [
            {"cursor": 1, "timestamp": "2026-04-20 09:00", "content": "Went for a long run."},
            {"cursor": 2, "timestamp": "2026-04-21 08:00", "content": "Asked for a short morning plan."},
        ],
    )

    service = HermesStyleMemoryService(tmp_path)
    hits = service.search_history("short morning plan")

    assert hits
    assert hits[0].content == "Asked for a short morning plan."
    assert (tmp_path / "memory" / "history_index.sqlite3").exists()


def test_search_history_rebuilds_index_when_history_changes(tmp_path) -> None:
    _write_history(
        tmp_path,
        [
            {"cursor": 1, "timestamp": "2026-04-20 09:00", "content": "Went for a long run."},
        ],
    )
    service = HermesStyleMemoryService(tmp_path)

    first_hits = service.search_history("long run")
    assert first_hits[0].content == "Went for a long run."

    _write_history(
        tmp_path,
        [
            {"cursor": 1, "timestamp": "2026-04-20 09:00", "content": "Went for a long run."},
            {"cursor": 2, "timestamp": "2026-04-22 08:00", "content": "Finished a focused writing sprint."},
        ],
    )

    second_hits = service.search_history("writing sprint")
    assert second_hits[0].content == "Finished a focused writing sprint."


def test_search_history_falls_back_when_sqlite_is_unavailable(monkeypatch, tmp_path) -> None:
    _write_history(
        tmp_path,
        [
            {"cursor": 1, "timestamp": "2026-04-20 09:00", "content": "Asked for a short morning plan."},
        ],
    )
    service = HermesStyleMemoryService(tmp_path)

    def _boom(*_args, **_kwargs):
        raise sqlite3.DatabaseError("fts unavailable")

    monkeypatch.setattr("nanobot.growth.memory.snapshot.sqlite3.connect", _boom)

    hits = service.search_history("short morning plan")
    assert hits[0].content == "Asked for a short morning plan."
