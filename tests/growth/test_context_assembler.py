from __future__ import annotations

import asyncio
import json
from datetime import datetime

from nanobot.growth.context.assembler import (
    ContextAssemblyInput,
    HermesStyleContextAssembler,
    render_context_packet,
)
from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.contracts.execution import RuntimeSnapshot
from nanobot.growth.memory.snapshot import HermesStyleMemoryService


def _write_history(workspace, entries: list[dict[str, object]]) -> None:
    memory_dir = workspace / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    history_file = memory_dir / "history.jsonl"
    with history_file.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def test_context_assembler_builds_stable_sections(tmp_path) -> None:
    (tmp_path / "USER.md").write_text("- Prefers concise plans.\n", encoding="utf-8")
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "MEMORY.md").write_text("- Recover after missed days with a tiny task.\n", encoding="utf-8")
    _write_history(
        tmp_path,
        [
            {"cursor": 1, "timestamp": "2026-04-21 08:00", "content": "Asked for a concise morning plan."},
        ],
    )

    assembler = HermesStyleContextAssembler(HermesStyleMemoryService(tmp_path))
    event = GrowthEvent(
        id="evt-1",
        type="user_message",
        userId="user-1",
        sessionId="session-1",
        timestamp=datetime(2026, 4, 22, 9, 0, 0),
        payload={
            "text": "Plan my morning workout.",
            "evidence_texts": ["The attached review says consistency dropped after late nights."],
        },
        source="chat",
    )
    snapshot = RuntimeSnapshot(
        user_id="user-1",
        session_id="session-1",
        active_goal_ids=["goal-fitness"],
        open_task_ids=["task-run"],
    )

    packet = asyncio.run(
        assembler.assemble(
            ContextAssemblyInput(event=event, snapshot=snapshot, mode="conversational")
        )
    )
    prompt = render_context_packet(packet)

    assert "Plan my morning workout." in packet.task_section
    assert "goal-fitness" in packet.goal_section
    assert "consistency dropped after late nights" in packet.evidence_section
    assert "Asked for a concise morning plan." in packet.history_section
    assert "[Role & Policies]" in prompt
    assert "[Current Evidence]" in prompt
    assert "[Memory Snapshot]" in prompt
    assert "[Relevant History]" in prompt
