from __future__ import annotations

from pydantic import BaseModel

from nanobot.growth.contracts.memory import MemoryWriteCandidate


class MemoryDecision(BaseModel):
    approved: bool
    reason: str


class RuleBasedMemoryGovernor:
    """Blocks low-confidence or weakly-grounded long-term memory writes."""

    def __init__(
        self,
        *,
        observed_min_confidence: float = 0.6,
        inferred_min_confidence: float = 0.8,
    ) -> None:
        self._observed_min_confidence = observed_min_confidence
        self._inferred_min_confidence = inferred_min_confidence

    def decide(self, candidate: MemoryWriteCandidate) -> MemoryDecision:
        if candidate.provenance == "explicit_user":
            return MemoryDecision(approved=True, reason="Explicit user statement.")

        if candidate.provenance == "observed":
            approved = candidate.confidence >= self._observed_min_confidence
            reason = (
                "Observed signal cleared confidence threshold."
                if approved
                else "Observed signal is below confidence threshold."
            )
            return MemoryDecision(approved=approved, reason=reason)

        approved = (
            candidate.confidence >= self._inferred_min_confidence
            and candidate.type != "fact"
        )
        reason = (
            "Inference cleared threshold and is not stored as a fact."
            if approved
            else "Inferred memories need higher confidence and cannot be stored as facts."
        )
        return MemoryDecision(approved=approved, reason=reason)

    def approve(self, candidate: MemoryWriteCandidate) -> bool:
        return self.decide(candidate).approved
