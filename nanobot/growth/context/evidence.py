from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from nanobot.growth.contracts.events import GrowthEvent
from nanobot.growth.contracts.evidence import EvidenceItem
from nanobot.utils.document import extract_text

_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx"}
_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".log",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
_MAX_EVIDENCE_TEXT_CHARS = 4000


def load_evidence_items(event: GrowthEvent, workspace: str | Path) -> list[EvidenceItem]:
    payload = event.payload or {}
    workspace_path = Path(workspace).expanduser().resolve()
    items: list[EvidenceItem] = []

    for text in _normalize_string_list(payload.get("evidence_texts")):
        items.append(
            EvidenceItem(
                id=f"evidence-{uuid4().hex}",
                source="inline_text",
                kind="text",
                title="Inline evidence",
                extracted_text=_truncate(text),
                summary="Inline evidence provided for the current turn.",
            )
        )

    for raw_path in _normalize_string_list(payload.get("evidence_paths")):
        items.append(_load_path_evidence(raw_path, workspace_path))

    return items


def render_evidence_section(items: list[EvidenceItem]) -> str:
    if not items:
        return ""

    blocks: list[str] = []
    for item in items:
        title = item.title or item.id
        lines = [f"Kind: {item.kind}", f"Source: {item.source}"]
        if item.summary:
            lines.append(f"Summary: {item.summary}")
        if item.extracted_text:
            lines.append("Content:")
            lines.append(item.extracted_text.strip())
        blocks.append(f"### {title}\n" + "\n".join(lines))
    return "\n\n".join(blocks)


def _load_path_evidence(raw_path: str, workspace: Path) -> EvidenceItem:
    title = Path(raw_path).name or raw_path
    try:
        resolved = _resolve_workspace_path(raw_path, workspace)
    except ValueError as exc:
        return EvidenceItem(
            id=f"evidence-{uuid4().hex}",
            source="file_path",
            kind="unknown",
            title=title,
            summary=f"Unavailable evidence: {exc}.",
            metadata={"error": str(exc)},
        )

    if not resolved.exists():
        return EvidenceItem(
            id=f"evidence-{uuid4().hex}",
            source="file_path",
            kind="unknown",
            title=title,
            summary="Unavailable evidence: file not found.",
            metadata={"error": "file not found"},
        )

    suffix = resolved.suffix.lower()
    mime_type, _ = mimetypes.guess_type(resolved.name)
    if suffix in _IMAGE_EXTENSIONS:
        return EvidenceItem(
            id=f"evidence-{uuid4().hex}",
            source="file_path",
            kind="image",
            path=str(resolved),
            mime_type=mime_type,
            title=resolved.name,
            summary="Image evidence provided for the current turn. Text extraction is not enabled.",
        )

    extracted = extract_text(resolved)
    kind = "document" if suffix in _DOCUMENT_EXTENSIONS else "text"
    if extracted is None:
        return EvidenceItem(
            id=f"evidence-{uuid4().hex}",
            source="file_path",
            kind="unknown",
            path=str(resolved),
            mime_type=mime_type,
            title=resolved.name,
            summary="Unsupported evidence type.",
            metadata={"error": "unsupported type"},
        )
    if extracted.startswith("[error:"):
        return EvidenceItem(
            id=f"evidence-{uuid4().hex}",
            source="file_path",
            kind=kind,
            path=str(resolved),
            mime_type=mime_type,
            title=resolved.name,
            summary=extracted,
            metadata={"error": "extract failed"},
        )

    return EvidenceItem(
        id=f"evidence-{uuid4().hex}",
        source="file_path",
        kind=kind,
        path=str(resolved),
        mime_type=mime_type,
        title=resolved.name,
        extracted_text=_truncate(extracted),
        summary=f"Loaded {kind} evidence from {resolved.name}.",
    )


def _resolve_workspace_path(raw_path: str, workspace: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = (workspace / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise ValueError("evidence path is outside the workspace") from exc
    return candidate


def _normalize_string_list(value: object) -> list[str]:
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _truncate(text: str, limit: int = _MAX_EVIDENCE_TEXT_CHARS) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit] + f"... (truncated, {len(stripped)} chars total)"
