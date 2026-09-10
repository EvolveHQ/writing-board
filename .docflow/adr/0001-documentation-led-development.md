---
adr: 0001
title: Documentation-led development
status: Accepted
date: 2026-09-10
owner: writing-board-maintainers
shape: technology
supersedes:
superseded-by:
depends-on: []
tags: [bootstrap]
---

# ADR 0001 — Documentation-led development

## Context

The owner requested a standalone public tool whose decisions, implementation queue and agent entrypoints can be understood without conversation history.

## Decision

Use a standalone .docflow catalog with two declared shapes, one numbering sequence, a work queue, a local verification gate and a single integrator. Keep canonical agent instructions in AGENT.md with discovery shims.

## Rationale

A root-only ad hoc README was rejected because decisions and unfinished implementation would be mixed with user instructions. A federation was rejected because this tool has no runtime dependency on its source product. Mandatory PRs for the sole bootstrap integrator were rejected because the owner explicitly authorized direct publication; external changes remain reviewed pull requests.

## Consequences

The tool remains portable and inspectable. The team must maintain explicit schemas and local checks; browser exports require a deliberate import into a new workspace.

## Acceptance criteria

1. Core instructions, conventions, two templates and a generated catalog are present.
2. The plan exists before implementation and records its implementation SHA at completion.
3. The local gate checks numbering, sections, documentation links and tests.

## Out of scope

Changing other repositories or installing global agent configuration.

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
