# growth Multimodal Evidence

This document describes the current-turn evidence lane used by the growth path.

## Scope

The goal is narrow:

- accept evidence for the current turn
- make that evidence visible in context assembly
- keep long-term memory governance unchanged

This is not:

- perceptual memory
- cross-modal retrieval
- a vector store
- a second multimodal runtime

## What Exists

The growth path can now ingest:

- inline evidence text
- workspace-relative file paths
- textualized document content when extraction succeeds
- image references as lightweight evidence items

Evidence is rendered into a dedicated `[Current Evidence]` section inside the
assembled context packet.

## File Handling

The current implementation reuses `nanobot.utils.document.extract_text(...)`.

That means:

- plain text and markdown files are read directly
- PDF, DOCX, XLSX, and PPTX files are textualized when supported libraries are available
- unsupported file types become soft-failure evidence items
- image files are represented as references, not as extracted text

## Security Boundary

Evidence paths are restricted to the active workspace.

If a path is:

- outside the workspace
- missing
- unsupported

the turn still proceeds, but the evidence item is marked unavailable instead of
failing the whole run.

## Memory Boundary

Evidence affects the current turn only.

Evidence does not automatically write to:

- `USER.md`
- `memory/MEMORY.md`

If any evidence-derived content should become long-term memory, it must still
go through:

1. `MemoryWriteCandidate`
2. `RuleBasedMemoryGovernor`

## Current Limitations

The evidence lane is intentionally narrow.

It does not yet provide:

- image understanding blocks in the growth runtime adapter
- audio evidence
- perceptual memory persistence
- cross-modal retrieval
- evidence-aware ranking beyond section placement

## Recommended Narrative

The best description is:

The project supports a current-turn evidence lane, not a multimodal memory
system. User-provided documents, text snippets, and file references can shape
the current response, but durable memory remains governed and intentionally
small.
