from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from nanobot.growth.contracts.context import ContextPacket
from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.contracts.execution import RuntimeSnapshot
from nanobot.growth.contracts.memory import MemoryWriteCandidate
from nanobot.growth.contracts.tasks import ScheduledTaskRecord, TaskStateMachine


def test_growth_event_accepts_alias_fields() -> None:
    event = GrowthEvent(
        id="evt-1",
        type="user_message",
        userId="user-1",
        sessionId="session-1",
        timestamp=datetime(2026, 4, 21, 9, 0, 0),
        payload={"text": "hello"},
        source="chat",
    )

    assert event.user_id == "user-1"
    assert event.session_id == "session-1"


def test_memory_candidate_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        MemoryWriteCandidate(
            scope="user",
            type="pattern",
            content="User slips on Monday mornings.",
            provenance="observed",
            confidence=1.5,
            reason="Derived from repeated missed check-ins.",
        )


def test_runtime_snapshot_uses_independent_lists() -> None:
    first = RuntimeSnapshot(user_id="user-1")
    second = RuntimeSnapshot(user_id="user-2")

    first.active_goal_ids.append("goal-1")

    assert second.active_goal_ids == []


def test_context_packet_has_default_retrieval_meta() -> None:
    packet = ContextPacket()

    assert packet.retrieval_meta.candidates == 0
    assert packet.retrieval_meta.selected == 0


def test_task_state_machine_allows_expected_transition() -> None:
    record = ScheduledTaskRecord(id="task-1", kind="daily_checkin", status="created")
    TaskStateMachine.assert_transition(record.status, "queued")


def test_task_state_machine_rejects_invalid_transition() -> None:
    with pytest.raises(ValueError):
        TaskStateMachine.assert_transition("completed", "queued")
