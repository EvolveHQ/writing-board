# Writing workflow

Start with a project, then move through the stages below. Revisit an earlier
stage when a later review exposes a problem; a completed checklist does not
guarantee a successful story.

| Stage | Work | Durable result |
| --- | --- | --- |
| 1. Set up | Choose audience, languages, format and page allowance. | `project.json` |
| 2. Set guidelines | Separate required constraints from craft preferences; choose voice, boundaries and review needs. | `guidelines.json` |
| 3. Build the bible | Identify characters, world rules, relationships and sources; mark unknowns. | `bible.json` |
| 4. Find the story | Compare premises with different causes and solutions; select a protagonist, want and obstacle. | Story premise and purpose |
| 5. Build beats | Give each action a consequence that motivates the next choice. Track chronology separately from reading order. | Beat sheet and corkboard |
| 6. Draft | Write the spoken story; use pictures for information the reader can see. | Beat manuscript text |
| 7. Compose | Assign beats to pages, reserve text zones and specify what each image adds. | Page plan and art briefs |
| 8. Review | Check craft, continuity, read-aloud rhythm and layout against this revision. | Reviews, fixes and proof references |
| 9. Localize | Adapt each language edition from an identified source revision; review it aloud and in layout. | Linked story packets and glossary |
| 10. Hand off | Export manuscript, briefs and requested deliverables; inspect actual production files when supplied. | Production handoff and proof records |
| 11. Maintain the series | Re-read the accepted story and record new facts, knowledge, relationships and unresolved promises. | Updated bible, timeline and arc grid |

Create a project non-interactively when the choices are already known:

```sh
python scripts/writing_board.py init projects/my-book --title "My book" --languages en it es cs sk
python scripts/writing_board.py character projects/my-book --id hero --name "Hero"
python scripts/writing_board.py story projects/my-book --id first-story --title "First story" --protagonist hero
```

Use `init --interactive` for guided initial choices. Complete the new character's
profile and shared rules before relying on them in a story. Keep the ID stable
even if the display name changes.

During writing:

```sh
python scripts/writing_board.py build projects/my-book
python scripts/writing_board.py validate projects/my-book
python scripts/writing_board.py status projects/my-book
```

`validate` checks data; `status` reports progress; `build` creates the offline
board and readable views. Resolve errors, assess reminders and record actual
reviews. The [board guide](board.md) explains how browser changes return to source
files. [Skills](skills.md) route agents to the same stages.

Use [worksheets](../templates/README.md) for exploration that does not fit the
structured fields. Put decisions back into the JSON source. Supplemental files
and external assets are not embedded in project bundles; transfer them separately
when another writer needs them.
