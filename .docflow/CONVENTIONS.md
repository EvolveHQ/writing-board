# Repository conventions

## Layout and decisions

The artifact root is `.docflow/`. Root `AGENT.md` is the instruction source;
`AGENTS.md` discovers it and `CLAUDE.md` contains only `@AGENT.md`.
One decision per ADR. Numbers are contiguous across both declared `shape` values:
`capability` and `technology`. Both templates use number `0000`. Never encode
shape in number ranges. Use relative links between decision documents.

Capability sections: Context, Capability statement, User stories / scenarios,
Acceptance criteria, Out of scope, Open questions, References, Revision History,
Approvals. Technology sections: Context, Decision, Rationale, Consequences,
Acceptance criteria, Out of scope, Open questions, References, Revision History,
Approvals. Rationale names alternatives and specific rejection reasons.
Acceptance criteria are numbered and testable.

## Lifecycle and audit

`Proposed -> Accepted -> Implemented -> Superseded/Deprecated`.
Terminal states may be reached from an earlier state. Accepted means implementation
is authorized; Implemented means the completion push succeeded. Substantive
changes append revision and approval rows. Editorial-only changes are marked
`editorial` in the commit message. Regenerate the catalog using
`python scripts/docflow.py` after changing any decision.
Decisions and their identifiers belong in contributor documentation, never the
writing interface or generated book content.

## Work queue and integration

Create a numbered `plan/todo/` item before substantive implementation. Reserve
numbers across todo and done; never restart the sequence. The queue number is
recorded in the first heading. Name owning decisions, scope, dependencies and
observable exit criteria. The sole integrator commits on `main` or fast-forwards
a work branch. No duplicate roles, lock, worklog or dashboard files are required.
Helpers edit only assigned disjoint paths; overlapping work uses worktrees.

Gate: `python scripts/verify.py` (Python 3.11+ and Node 18+ for tests).
After validation, commit implementation. Then move the plan to
`plan/done/YYYY-MM-DD-slug.md`, name the implementation tip SHA in its completion
footer, advance the owning decisions and regenerate the catalog in a separate
completion commit. Push both commits; successful push to `main` is completion.
CI repeats the gate, but does not replace local validation. Contributor pull
requests require review and the same gate before fast-forward integration.

Use signed Conventional Commits. ADR changes require a `Rationale:` footer.
Do not add co-author trailers unless asked. No force pushes or revision tags.

## Bootstrap authorization

The repository owner explicitly delegated design decisions, plan authorship and
public repository creation on 2026-09-10. Initial decisions record that delegated
authority; they do not claim a separate manual review. MIT applies to the generic
tool and original sample. Private project material is excluded by default.
