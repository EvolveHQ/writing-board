---
adr: 0004
title: Story board and evidence
status: Accepted
date: 2026-09-10
owner: writing-board-maintainers
shape: capability
supersedes:
superseded-by:
depends-on: []
tags: [bootstrap]
---

# ADR 0004 — Story board and evidence

## Context

Editing a story changes its pacing, physical composition and the validity of previous review evidence.

## Capability statement

Provide managed story selection, editable beat cards, story purpose, scene grid, page plan, chronology, continuity, review records and complete packet import/export. Preserve stable event IDs and chronological order independently from reading order. Invalidate evidence when content or project context changes.

## User stories / scenarios

As a writer, I can reorder scenes while preserving causality. As a reviewer, I can see which packet revision an observation or proof actually inspected.

## Acceptance criteria

1. Board selection and packet export preserve edits, extensions and independent chronology.
2. Page plans cover every interior page exactly once with physical even-left spreads.
3. Edits invalidate review/proof status; stale bundle imports are rejected.
4. Browser output escapes author content and works without fetching remote resources.

## Out of scope

A browser file editor with silent autosave, automated editorial approval and a full word processor.

## Open questions

None for this implementation.

## References

- [Implementation plan](../plan/todo/0001-portable-writing-workspace.md)
- [Conventions](../CONVENTIONS.md)

## Revision History

| Date | Revision | Author | Change |
|---|---|---|---|
| 2026-09-10 | r1 | Codex | Initial decision under delegated owner authority. |

## Approvals

| Role | Name | Date | Signature |
|---|---|---|---|
| Delegated implementer | Codex | 2026-09-10 | Owner explicitly delegated design decisions and publication in the task request. |
