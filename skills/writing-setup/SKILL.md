---
name: writing-setup
description: Initialize or inspect a Writing Board workspace and identify the next writing stage from its existing project documents.
---

# Set up a writing project

Read [the workflow](../../docs/workflow.md) and
[the command contract](../../docs/contracts.md). Identify the requested workspace
before writing. Inspect an existing project instead of initializing over it.

Use the user's audience, languages and format. Resolve ordinary defaults from
the brief; ask only for missing choices that materially affect the work. For a
new workspace use `python scripts/writing_board.py init PROJECT --title "TITLE"
--languages en` with the actual title and language tags. Keep private projects
under ignored `projects/` or outside the tool checkout. `--interactive` supports
human-led setup; an agent with the needed choices should use explicit arguments.

Read the resulting project, guidelines and bible. Explain any assumptions in
project notes, then route to the relevant writing skill. Do not create filler
characters or prose merely to make progress indicators look complete. Run
`validate`, `status` and `build` for the workspace as appropriate. Return the
source path, generated board path and the next concrete writing step.
