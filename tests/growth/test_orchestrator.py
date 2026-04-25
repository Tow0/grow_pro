from __future__ import annotations

import asyncio
from datetime import datetime

from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.memory.snapshot import HermesStyleMemoryService
from nanobot.growth.orchestrator.service import HermesStyleGrowthOrchestrator
from nanobot.nanobot import RunResult


class FakeRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def run_text_turn(self, message: str, *, session_key: str, hooks=None) -> RunResult:
        del hooks
        self.calls.append((message, session_key))
        return RunResult(content="runtime-ok", tools_used=[], messages=[])


def test_orchestrator_persists_explicit_memory_and_calls_runtime(tmp_path) -> None:
    runtime = FakeRuntime()
    memory_service = HermesStyleMemoryService(tmp_path)
    orchestrator = HermesStyleGrowthOrchestrator(
        runtime,
        memory_service=memory_service,
    )

    event = GrowthEvent(
        id="evt-1",
        type="user_message",
        userId="user-1",
        sessionId="session-1",
        timestamp=datetime(2026, 4, 22, 9, 0, 0),
        payload={
            "text": "Please plan my day.",
            "remember": "User prefers short morning plans.",
        },
        source="chat",
    )

    result = asyncio.run(orchestrator.handle(event))

    assert result == "runtime-ok"
    assert runtime.calls
    prompt, session_key = runtime.calls[0]
    assert session_key == "growth:user-1:session-1"
    assert "[Task]" in prompt
    assert "[Memory Snapshot]" in prompt
    assert "User prefers short morning plans." in (tmp_path / "USER.md").read_text(encoding="utf-8")


def test_orchestrator_rejects_inferred_fact_candidate(tmp_path) -> None:
    runtime = FakeRuntime()
    memory_service = HermesStyleMemoryService(tmp_path)
    orchestrator = HermesStyleGrowthOrchestrator(
        runtime,
        memory_service=memory_service,
    )

    event = GrowthEvent(
        id="evt-2",
        type="user_message",
        userId="user-1",
        sessionId="session-1",
        timestamp=datetime(2026, 4, 22, 9, 30, 0),
        payload={
            "text": "How should I recover this week?",
            "memory_candidates": [
                {
                    "scope": "user",
                    "type": "fact",
                    "content": "User always performs best at night.",
                    "provenance": "inferred",
                    "confidence": 0.95,
                    "reason": "Model inferred a stable trait.",
                }
            ],
        },
        source="chat",
    )

    result = asyncio.run(orchestrator.handle(event))

    assert result == "runtime-ok"
    user_file = tmp_path / "USER.md"
    assert user_file.exists() is False or "always performs best at night" not in user_file.read_text(encoding="utf-8")


def test_orchestrator_extracts_explicit_memory_from_user_message(tmp_path) -> None:
    runtime = FakeRuntime()
    memory_service = HermesStyleMemoryService(tmp_path)
    orchestrator = HermesStyleGrowthOrchestrator(
        runtime,
        memory_service=memory_service,
    )

    event = GrowthEvent(
        id="evt-3",
        type="user_message",
        userId="user-1",
        sessionId="session-2",
        timestamp=datetime(2026, 4, 24, 8, 0, 0),
        payload={
            "text": "\u4ee5\u540e\u56de\u7b54\u76f4\u63a5\u4e00\u70b9\uff0c\u5c3d\u91cf\u7b80\u6d01\u3002"
        },
        source="chat",
    )

    result = asyncio.run(orchestrator.handle(event))

    assert result == "runtime-ok"
    assert (
        "\u4ee5\u540e\u56de\u7b54\u76f4\u63a5\u4e00\u70b9\uff0c\u5c3d\u91cf\u7b80\u6d01\u3002"
        in (tmp_path / "USER.md").read_text(encoding="utf-8")
    )


def test_orchestrator_uses_recovery_mode_for_blocked_task_update(tmp_path) -> None:
    runtime = FakeRuntime()
    memory_service = HermesStyleMemoryService(tmp_path)
    orchestrator = HermesStyleGrowthOrchestrator(
        runtime,
        memory_service=memory_service,
    )

    event = GrowthEvent(
        id="evt-4",
        type="task_update",
        userId="user-1",
        sessionId="session-3",
        timestamp=datetime(2026, 4, 24, 10, 0, 0),
        payload={
            "text": "Task blocked on design review.",
            "status": "blocked",
        },
        source="todo",
        priority="high",
    )

    result = asyncio.run(orchestrator.handle(event))

    assert result == "runtime-ok"
    prompt, session_key = runtime.calls[0]
    assert session_key == "growth:user-1:session-3"
    assert "Mode: recovery" in prompt
    assert "Event Type: task_update" in prompt


def test_orchestrator_includes_evidence_without_persisting_it(tmp_path) -> None:
    runtime = FakeRuntime()
    memory_service = HermesStyleMemoryService(tmp_path)
    orchestrator = HermesStyleGrowthOrchestrator(
        runtime,
        memory_service=memory_service,
    )

    event = GrowthEvent(
        id="evt-5",
        type="user_message",
        userId="user-1",
        sessionId="session-4",
        timestamp=datetime(2026, 4, 24, 11, 0, 0),
        payload={
            "text": "Help me summarize this review.",
            "evidence_texts": ["Weekly review: missed workouts followed two late-night coding sessions."],
        },
        source="chat",
    )

    result = asyncio.run(orchestrator.handle(event))

    assert result == "runtime-ok"
    prompt, _session_key = runtime.calls[0]
    assert "[Current Evidence]" in prompt
    assert "missed workouts followed two late-night coding sessions" in prompt
    user_file = tmp_path / "USER.md"
    assert user_file.exists() is False
