from __future__ import annotations

from datetime import datetime

from nanobot.growth.context.evidence import load_evidence_items, render_evidence_section
from nanobot.growth.contracts.events import GrowthEvent


def _event(payload: dict[str, object]) -> GrowthEvent:
    return GrowthEvent(
        id="evt-evidence",
        type="user_message",
        userId="user-1",
        sessionId="session-1",
        timestamp=datetime(2026, 4, 24, 12, 0, 0),
        payload=payload,
        source="chat",
    )


def test_load_evidence_items_reads_inline_and_file_evidence(tmp_path) -> None:
    report = tmp_path / "weekly_review.md"
    report.write_text("Weekly review:\n- Missed workouts after late nights.", encoding="utf-8")

    items = load_evidence_items(
        _event(
            {
                "evidence_texts": ["Focus on consistency this week."],
                "evidence_paths": ["weekly_review.md"],
            }
        ),
        tmp_path,
    )

    assert len(items) == 2
    assert items[0].kind == "text"
    assert items[0].extracted_text == "Focus on consistency this week."
    assert items[1].kind == "text"
    assert "Missed workouts" in (items[1].extracted_text or "")


def test_load_evidence_items_blocks_outside_workspace_paths(tmp_path) -> None:
    outside = tmp_path.parent / "secret.md"
    outside.write_text("secret", encoding="utf-8")

    items = load_evidence_items(
        _event({"evidence_paths": [str(outside)]}),
        tmp_path,
    )

    assert len(items) == 1
    assert items[0].kind == "unknown"
    assert "outside the workspace" in (items[0].summary or "")


def test_render_evidence_section_formats_items(tmp_path) -> None:
    evidence_file = tmp_path / "note.txt"
    evidence_file.write_text("A focused sprint helped today.", encoding="utf-8")
    items = load_evidence_items(_event({"evidence_paths": ["note.txt"]}), tmp_path)

    section = render_evidence_section(items)

    assert "Current turn" not in section
    assert "Kind: text" in section
    assert "A focused sprint helped today." in section
