# Implementation contracts

This page specifies the stable workspace format. See the JSON schemas for field
types; extensions objects preserve author metadata.

Workspace files are `project.json`, `guidelines.json`, `bible.json`, and
`stories/<stable-id>.json`. `build/` is generated. No directory is inferred from
user-controlled JSON paths. A bundle is a single JSON object with
`bundle_version: 1`, `base_revision` (project revision at export), `project`,
`guidelines`, `bible`, and `stories` (array of complete story packets).

Project fields: `schema_version: 1`, `id`, `title`, `revision` (positive integer),
`audience`, `languages` (array of language tags), `format: "illustrated-book"`,
`default_spreads`, `extensions`.

Guidelines fields: `schema_version: 1`, `profile`, `voice`, `teaching`,
`content_boundaries` (string arrays), `composition` (string array), `word_budget`
(`min`, `max`, nonnegative integers), `required_reviews` (review kind strings),
`extensions`. All craft targets are project choices; counts yield reminders.

Bible fields: `schema_version: 1`, `characters`, `locations`, `world_rules`,
`relationships`, `timeline`, `glossary`, `extensions`.
Character: `id`, `name`, `summary`, `appearance`, `backstory`, `want`, `need`,
`voice`, `speech_mode` (`verbal`, `nonverbal`, `unspecified`), `facts` array,
`extensions`. Location: `id`, `name`, `description`, `facts`, `extensions`.
Fact/world rule: `id`, `statement`, `status` (`proposed`, `sourced`, `established`),
`source_ref` (string or null). Sourced or established facts require a reference.
Relationship: `id`, `from_id`, `to_id`, `description`, `status`, `source_ref`.
Timeline: `id`, `when` (string or null), `description`, `character_ids`,
`source_ref` (string or null). Glossary: `term`, `language`, `preferred`, `notes`.

Story packets retain schema version 1 and the existing generic beat, purpose,
page plan and continuity structure. The story engine takes optional `known_ids`
for cast validation; project validation adds bible locations and speech modes.
No implicit story-specific world rules belong in the generic engine.

## Commands

Run from the tool repository; project arguments may be absolute paths.

```sh
python scripts/writing_board.py init projects/my-book --title "My book" --languages en it es cs sk
python scripts/writing_board.py character projects/my-book --id hero --name "Hero"
python scripts/writing_board.py story projects/my-book --id first-story --title "First story" --protagonist hero
python scripts/writing_board.py validate projects/my-book
python scripts/writing_board.py build projects/my-book
python scripts/writing_board.py export projects/my-book --output projects/snapshot.json
python scripts/writing_board.py import projects/my-book --bundle projects/edited.json --output projects/revised
python scripts/writing_board.py handoff projects/my-book --output projects/handoff
python scripts/writing_board.py status projects/my-book
```

`init --interactive` guides initial choices. Edit structured source files directly,
or use the board's project/guidelines/bible editors and export a project bundle.
`build` generates `build/board.html` and readable story views. The bundle import
requires a matching project ID and base revision, creates a new directory,
advances the project revision and invalidates evidence on all imported stories.
It never overwrites the base project. Root edits followed by `build` are detected
against `build/source-state.json`, a baseline updated by every managed write;
`build/snapshot.json` records the last HTML build. Rebuild invalidates story
evidence for authored changes. Evidence-only
updates preserve the current revision. Other commands reject unbuilt source
changes: rebuild before exchanging bundles or reporting current review status.

The board template is `web/board.html`, with inert JSON script markers
`embedded-project` (bundle, default `{}`), `embedded-packets` (story array, `[]`),
and `packet-schema` (full schema). The builder injects them with `<` escaped.
Board context edits remain in memory until exported; “Export project” includes
all boards and retains the original base revision. Packet export remains available.
The browser doesn't write into repository source paths.

Production handoff exports manuscript, art briefs and an inventory of requested
PDF/EPUB deliverables. It does not generate artwork or claim print-ready output.
