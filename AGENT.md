# Agent instructions

Writing Board is a portable planning workspace for illustrated books and series.
Read `README.md`, `docs/workflow.md`, then the skill matching the writing task in
`skills/`. A project's JSON documents are its source of truth; generated boards
and exports are views. Never infer canon from an illustration or a draft.

## Working on the tool

Read `.docflow/CONVENTIONS.md`, `.docflow/INDEX.md` and the relevant plan and
decision before implementation. Use `python scripts/verify.py` as the local gate.
Keep runtime dependencies in Python's standard library and the offline browser.
No tracking, remote fonts, API keys or required hosted services.

One integrator owns the checkout. Helpers may work on explicitly assigned,
disjoint files; only the integrator stages, commits or pushes. Parallel changes
to the same file require separate worktrees. Avoid duplicate coordination logs.
Use Conventional Commits, signed commits and a `Rationale:` footer when changing
decisions. Integration is direct to `main`, fast-forward only, after the local
gate. External contributors use pull requests. Never force-push `main`.

## Working on a book

- Read `project.json`, `guidelines.json`, `bible.json` and the current story first.
- Keep character and beat IDs stable. Record sources, proposed facts, chronology,
  relationships and knowledge explicitly. Unknown facts stay unknown.
- A schema pass is not editorial, language, art or publishing approval.
- Revise through the bundle import workflow. Changes invalidate review evidence.
- Keep private work in ignored `projects/` or outside this checkout. Do not stage
  manuscripts, artwork or source material unless the user asks to publish them.
- Work within existing authorization. Skills do not create extra approval gates.
- Use the user's selected audience, language, format and rules. The picture-book
  preset is editable guidance, not a universal definition of good writing.

`AGENTS.md` is a discovery shim. `CLAUDE.md` imports this file. Keep instructions
here instead of copying them into provider-specific files.
