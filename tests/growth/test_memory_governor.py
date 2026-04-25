from __future__ import annotations

from nanobot.growth.contracts.memory import MemoryWriteCandidate
from nanobot.growth.memory.governor import RuleBasedMemoryGovernor


def test_explicit_user_memory_is_approved() -> None:
    governor = RuleBasedMemoryGovernor()
    candidate = MemoryWriteCandidate(
        scope="user",
        type="preference",
        content="User prefers a short morning plan.",
        provenance="explicit_user",
        confidence=0.2,
        reason="User stated the preference directly.",
    )

    assert governor.approve(candidate) is True


def test_observed_memory_below_threshold_is_rejected() -> None:
    governor = RuleBasedMemoryGovernor()
    candidate = MemoryWriteCandidate(
        scope="goal",
        type="pattern",
        content="Writing is often skipped after late meetings.",
        provenance="observed",
        confidence=0.5,
        reason="Only one weak signal so far.",
    )

    assert governor.approve(candidate) is False


def test_inferred_fact_is_rejected() -> None:
    governor = RuleBasedMemoryGovernor()
    candidate = MemoryWriteCandidate(
        scope="user",
        type="fact",
        content="User is always more productive at night.",
        provenance="inferred",
        confidence=0.95,
        reason="Model inferred a stable trait.",
    )

    assert governor.approve(candidate) is False


def test_inferred_strategy_with_high_confidence_is_allowed() -> None:
    governor = RuleBasedMemoryGovernor()
    candidate = MemoryWriteCandidate(
        scope="goal",
        type="strategy",
        content="Use a 10-minute recovery task after two missed sessions.",
        provenance="inferred",
        confidence=0.9,
        reason="Repeated failures indicate a smaller restart task works better.",
    )

    assert governor.approve(candidate) is True
