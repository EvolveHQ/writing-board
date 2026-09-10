# Documentation index
Start with the [README](../README.md), follow the [writing workflow](workflow.md), or open the [offline HTML reader](index.html). This index includes every maintained Markdown guide, skill, worksheet and contributor decision. Regenerate with `python scripts/build_docs.py`.

## Start and contribute
- [Agent instructions](../AGENT.md)
- [Agents](../AGENTS.md)
- [Claude](../CLAUDE.md)
- [Contributing](../CONTRIBUTING.md)
- [Writing Board](../README.md)

## Writing guides
- [Character and world bible](bible.md)
- [Using the board](board.md)
- [Compose words and pictures](composition.md)
- [Implementation contracts](contracts.md)
- [Set writing guidelines](guidelines.md)
- [Prepare language editions](localization.md)
- [Production handoff](production.md)
- [Review a story](review.md)
- [Agent skills](skills.md)
- [Bootstrap verification](verification.md)
- [Writing workflow](workflow.md)

## Agent skills
- [Maintain the bible](../skills/writing-bible/SKILL.md)
- [Compose the book](../skills/writing-composition/SKILL.md)
- [Set project guidelines](../skills/writing-guidelines/SKILL.md)
- [Localize a story](../skills/writing-localization/SKILL.md)
- [Prepare production handoff](../skills/writing-production/SKILL.md)
- [Review and repair](../skills/writing-review/SKILL.md)
- [Set up a writing project](../skills/writing-setup/SKILL.md)
- [Develop the story](../skills/writing-story/SKILL.md)

## Worksheets
- [Writing worksheets](../templates/README.md)
- [Character dossier](../templates/character-dossier.md)
- [Localization record](../templates/localization.md)
- [Location and map notes](../templates/location-map.md)
- [Premise alternatives](../templates/premise-alternatives.md)
- [Production handoff record](../templates/production-handoff.md)
- [Read-aloud log](../templates/read-aloud.md)
- [Story review](../templates/review.md)
- [Scene and art brief](../templates/scene-art-brief.md)

## Contributor decisions and plans
- [Repository conventions](../.docflow/CONVENTIONS.md)
- [Decision catalog](../.docflow/INDEX.md)
- [Run an authorized queue item](../.docflow/_agent/prompts/autonomous.md)
- [ADR NNNN — <Title>](../.docflow/adr/0000-template-technology.md)
- [ADR NNNN — <Title>](../.docflow/adr/0000-template.md)
- [ADR 0001 — Documentation-led development](../.docflow/adr/0001-documentation-led-development.md)
- [ADR 0002 — Portable offline workspaces](../.docflow/adr/0002-portable-offline-workspaces.md)
- [ADR 0003 — Guidelines and character bible](../.docflow/adr/0003-guidelines-and-character-bible.md)
- [ADR 0004 — Story board and evidence](../.docflow/adr/0004-story-board-and-evidence.md)
- [ADR 0005 — Guided writing workflow](../.docflow/adr/0005-guided-writing-workflow.md)
- [Work queue](../.docflow/plan/README.md)
- [Plan 0001 — Portable writing workspace](../.docflow/plan/done/2026-09-10-portable-writing-workspace.md)

## Data and commands
- [Workspace contracts](contracts.md) and `python scripts/writing_board.py --help`.
- [bible.schema.json](../schemas/bible.schema.json)
- [guidelines.schema.json](../schemas/guidelines.schema.json)
- [project.schema.json](../schemas/project.schema.json)
- [story.schema.json](../schemas/story.schema.json)
- [Original sample](../examples/rainy-day/project.json). Build it with `python scripts/writing_board.py build examples/rainy-day`.
