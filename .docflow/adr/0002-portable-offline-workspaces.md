---
adr: 0002
title: Portable offline workspaces
status: Implemented
date: 2026-09-10
owner: writing-board-maintainers
shape: technology
supersedes:
superseded-by:
depends-on: []
tags: [bootstrap]
---

# ADR 0002 — Portable offline workspaces

## Context

Writers and agents need the same editable files, including on a disconnected computer, without exposing private manuscripts.

## Decision

Store project configuration, guidelines, character bible and story packets as versioned JSON. Use Python standard-library tools to validate and package a self-contained HTML board. Keep private projects ignored; provide an original demonstration separately.

## Rationale

A hosted database was rejected because it requires account, network and service administration for a local workflow. A mandatory Electron application was rejected because installation and platform releases would be required to read a project. Markdown-only storage was rejected because reference and revision checks need explicit fields.

## Consequences

The tool remains portable and inspectable. The team must maintain explicit schemas and local checks; browser exports require a deliberate import into a new workspace.

## Acceptance criteria

1. A fresh project builds an offline HTML board without installing runtime dependencies.
2. Bundle export/import round-trips all authored fields and rejects unrelated or stale bases.
3. Import uses a new destination and rejects unsafe IDs and malformed JSON without overwriting sources.

## Out of scope

Cloud synchronization, collaboration servers, executable plugins and external image-generation integrations.

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
