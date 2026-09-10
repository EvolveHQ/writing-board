---
adr: 0005
title: Guided writing workflow
status: Implemented
date: 2026-09-10
owner: writing-board-maintainers
shape: capability
supersedes:
superseded-by:
depends-on: []
tags: [bootstrap]
---

# ADR 0005 — Guided writing workflow

## Context

A reusable infrastructure needs operating instructions for both a person and an agent, beyond a collection of editable files.

## Capability statement

Provide a guided project workflow, repository-scoped skills and linked documentation for setup, guidelines, bible maintenance, story development, composition, review, localization and production handoff. Produce readable plans and production briefs without claiming to create finished books.

## User stories / scenarios

As a new author, I can follow the start guide to a reviewable story packet. As an agent, I can choose a bounded skill and record continuity changes with evidence.

## Acceptance criteria

1. README links a complete Markdown and HTML documentation index and a working quickstart.
2. Each writing stage has a specific skill with valid frontmatter and linked procedures.
3. A handoff contains manuscripts, spread art briefs, language coverage and required deliverables.
4. A fresh-project walkthrough and automated regression tests exercise the documented commands.

## Out of scope

Artwork generation, finished PDF/EPUB rendering, printer-specific preflight and professional translation certification.

## Open questions

None for this implementation.

## References

- [Implementation plan](../plan/done/2026-09-10-portable-writing-workspace.md)
- [Conventions](../CONVENTIONS.md)

## Revision History

| Date | Revision | Author | Change |
|---|---|---|---|
| 2026-09-10 | r1 | Codex | Initial decision under delegated owner authority. |
| 2026-09-10 | r2 | Codex | Implemented and validated; completion accompanies the authorized public push. |

## Approvals

| Role | Name | Date | Signature |
|---|---|---|---|
| Delegated implementer | Codex | 2026-09-10 | Owner explicitly delegated design decisions and publication in the task request. |
| Delegated implementer | Codex | 2026-09-10 | Implementation verified under the same owner authorization; visual-test limitation recorded. |
