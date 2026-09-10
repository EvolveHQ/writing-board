---
adr: 0003
title: Guidelines and character bible
status: Accepted
date: 2026-09-10
owner: writing-board-maintainers
shape: capability
supersedes:
superseded-by:
depends-on: []
tags: [bootstrap]
---

# ADR 0003 — Guidelines and character bible

## Context

Book rules and character knowledge must belong to the selected project rather than being embedded in a tool written for one fictional world.

## Capability statement

Authors can configure audience, languages, craft guidelines and budgets, and maintain stable character dossiers, sourced facts, places, relationships, world rules, a timeline and glossary. Story validation checks these references and communication rules.

## User stories / scenarios

As an author, I can change my writing profile without editing application code. As a continuity editor, I can distinguish a draft invention from an established fact and find its source.

## Acceptance criteria

1. Project, guidelines and bible editors and source files are available for an empty workspace.
2. Characters have stable identifiers and editable profile, backstory, motivation and speech settings.
3. Invalid character/location references, missing established sources and contradictory structured speech modes fail validation.

## Out of scope

Automatic truth verification, inferred character facts and automatic promotion of draft facts to established canon.

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
