from __future__ import annotations

from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.contracts.memory import MemoryWriteCandidate

_PREFERENCE_HINTS = (
    "i prefer",
    "remember that i prefer",
    "prefer answers",
    "\u56de\u7b54\u76f4\u63a5",
    "\u56de\u7b54\u7b80\u6d01",
    "\u56de\u7b54\u7cbe\u70bc",
    "\u4ee5\u540e\u56de\u7b54",
    "\u6211\u504f\u597d",
    "\u6211\u5e0c\u671b\u4f60",
)

_WARNING_HINTS = (
    "do not",
    "don't",
    "avoid",
    "please avoid",
    "\u4e0d\u8981",
    "\u522b",
    "\u907f\u514d",
    "\u4e0d\u8981\u7ed9\u6211\u5b89\u6392",
)

_STRATEGY_HINTS = (
    "i work best",
    "i do better",
    "i focus best",
    "i am more likely to",
    "works better for me",
    "\u66f4\u9002\u5408",
    "\u66f4\u5bb9\u6613\u575a\u6301",
    "\u66f4\u5bb9\u6613\u4e13\u6ce8",
    "\u6548\u7387\u66f4\u9ad8",
    "\u72b6\u6001\u66f4\u597d",
)

_TEMPORARY_STATE_HINTS = (
    "today",
    "this week",
    "right now",
    "currently",
    "\u4eca\u665a",
    "\u4eca\u5929",
    "\u8fd9\u5468",
    "\u73b0\u5728",
)

_STATE_WORDS = (
    "tired",
    "stressed",
    "busy",
    "exhausted",
    "anxious",
    "\u7d2f",
    "\u56f0",
    "\u7126\u8651",
    "\u5fd9",
    "\u6ca1\u72b6\u6001",
)

_SPECULATION_HINTS = (
    "am i",
    "do you think",
    "maybe i",
    "might i",
    "\u662f\u4e0d\u662f",
    "\u4e5f\u8bb8\u6211",
)

_DIRECTIVE_HINTS = (
    "remember",
    "can you",
    "could you",
    "please",
    "\u8bf7",
    "\u4ee5\u540e",
)


def extract_memory_candidates(event: GrowthEvent) -> list[MemoryWriteCandidate]:
    """Extract small, high-confidence explicit-user candidates from chat text."""

    if event.type != "user_message":
        return []

    text = _event_text(event)
    if not text:
        return []

    candidate = _classify_explicit_memory(text)
    if candidate is None:
        return []
    return [candidate]


def _event_text(event: GrowthEvent) -> str:
    payload = event.payload or {}
    for key in ("text", "message", "content"):
        value = payload.get(key)
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                return cleaned
    return ""


def _classify_explicit_memory(text: str) -> MemoryWriteCandidate | None:
    normalized = _normalize(text)
    if not normalized:
        return None

    if _looks_temporary_state(normalized):
        return None
    if _looks_speculative_question(normalized):
        return None

    memory_type = _detect_memory_type(normalized)
    if memory_type is None:
        return None

    return MemoryWriteCandidate(
        scope="user",
        type=memory_type,
        content=text.strip(),
        provenance="explicit_user",
        confidence=0.95,
        reason=f"User explicitly stated a stable preference or rule: {text.strip()}",
    )


def _detect_memory_type(normalized: str) -> str | None:
    if _contains_any(normalized, _WARNING_HINTS):
        return "warning"
    if _contains_any(normalized, _STRATEGY_HINTS):
        return "strategy"
    if _contains_any(normalized, _PREFERENCE_HINTS):
        return "preference"
    return None


def _looks_temporary_state(normalized: str) -> bool:
    return _contains_any(normalized, _TEMPORARY_STATE_HINTS) and _contains_any(
        normalized, _STATE_WORDS
    )


def _looks_speculative_question(normalized: str) -> bool:
    if _contains_any(normalized, _SPECULATION_HINTS):
        return True
    if "?" not in normalized and "\uff1f" not in normalized:
        return False
    if _contains_any(normalized, _DIRECTIVE_HINTS):
        return False
    return True


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def _normalize(text: str) -> str:
    return " ".join(text.strip().casefold().split())
