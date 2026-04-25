from __future__ import annotations

from datetime import datetime

from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.memory.extractor import extract_memory_candidates


def _user_message(text: str) -> GrowthEvent:
    return GrowthEvent(
        id="evt-test",
        type="user_message",
        userId="user-1",
        sessionId="session-1",
        timestamp=datetime(2026, 4, 24, 9, 0, 0),
        payload={"text": text},
        source="chat",
    )


def test_extractor_recognizes_explicit_preference() -> None:
    candidates = extract_memory_candidates(
        _user_message("\u4ee5\u540e\u56de\u7b54\u76f4\u63a5\u4e00\u70b9\uff0c\u5c3d\u91cf\u7b80\u6d01\u3002")
    )

    assert len(candidates) == 1
    assert candidates[0].type == "preference"
    assert candidates[0].provenance == "explicit_user"


def test_extractor_recognizes_english_preference_request() -> None:
    candidates = extract_memory_candidates(
        _user_message("Can you remember that I prefer bullet lists in future answers?")
    )

    assert len(candidates) == 1
    assert candidates[0].type == "preference"


def test_extractor_recognizes_explicit_warning() -> None:
    candidates = extract_memory_candidates(
        _user_message(
            "\u5de5\u4f5c\u65e5\u665a10\u70b9\u540e\u4e0d\u8981\u7ed9\u6211\u5b89\u6392\u9ad8\u8ba4\u77e5\u4efb\u52a1\u3002"
        )
    )

    assert len(candidates) == 1
    assert candidates[0].type == "warning"


def test_extractor_recognizes_english_warning() -> None:
    candidates = extract_memory_candidates(
        _user_message("Please avoid scheduling deep work after 10 pm on weekdays.")
    )

    assert len(candidates) == 1
    assert candidates[0].type == "warning"


def test_extractor_recognizes_explicit_strategy() -> None:
    candidates = extract_memory_candidates(
        _user_message(
            "\u6211\u66f4\u9002\u5408\u65e9\u4e0a\u505a\u8f7b\u91cf\u4efb\u52a1\uff0c\u665a\u4e0a\u505a\u590d\u76d8\u3002"
        )
    )

    assert len(candidates) == 1
    assert candidates[0].type == "strategy"


def test_extractor_recognizes_english_strategy() -> None:
    candidates = extract_memory_candidates(_user_message("I focus best before lunch."))

    assert len(candidates) == 1
    assert candidates[0].type == "strategy"


def test_extractor_skips_temporary_state() -> None:
    candidates = extract_memory_candidates(
        _user_message("\u6211\u4eca\u5929\u6709\u70b9\u7d2f\uff0c\u8fd9\u5468\u72b6\u6001\u4e0d\u592a\u597d\u3002")
    )

    assert candidates == []


def test_extractor_skips_goal_statement() -> None:
    candidates = extract_memory_candidates(_user_message("I want to finish this report today."))

    assert candidates == []


def test_extractor_skips_situational_like_statement() -> None:
    candidates = extract_memory_candidates(_user_message("I like this plan."))

    assert candidates == []


def test_extractor_skips_speculative_question() -> None:
    candidates = extract_memory_candidates(
        _user_message("\u6211\u662f\u4e0d\u662f\u4e0d\u9002\u5408\u665a\u4e0a\u5b66\u4e60\uff1f")
    )

    assert candidates == []


def test_extractor_only_runs_for_user_messages() -> None:
    event = GrowthEvent(
        id="evt-checkin",
        type="checkin",
        userId="user-1",
        sessionId="session-1",
        timestamp=datetime(2026, 4, 24, 9, 0, 0),
        payload={"text": "I focus best before lunch."},
        source="chat",
    )

    assert extract_memory_candidates(event) == []
