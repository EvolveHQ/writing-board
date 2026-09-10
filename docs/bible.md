# Character and world bible

`bible.json` is the shared reference for every story. Create a character with the
CLI, then complete its fields in source JSON or the board's bible editor:

```sh
python scripts/writing_board.py character projects/my-book --id hero --name "Hero"
```

A useful profile records appearance, backstory, current want, underlying need,
voice and speech mode. Add distinctive habits, limitations, family or age details
only when established or useful. Use `extensions` for additional structured
fields. Unknown details stay unknown; do not fill gaps from guesswork or a
generated image. The [dossier worksheet](../templates/character-dossier.md)
supports deeper exploration.

## Evidence and canon

| Bible status | Meaning | Reference |
| --- | --- | --- |
| `proposed` | An idea being considered; it may change. | Optional; retain one when it explains the proposal. |
| `sourced` | An assertion found in an identified source. | Required; identify the source and passage or record. |
| `established` | A fact adopted for continuity in this project. | Required; point to the accepted source, story or decision record. |

A source citation does not settle conflicting authority. Define source precedence
in project notes, compare contradictory accounts and retain the decision's
reason. Change status only when the project's authority supports it. A new draft,
artwork or successful validation does not establish canon.

Story packets also permit `interpretation` for inferred facts. Keep such inferences
explicit; when carrying one into the bible, use `proposed` until supported.
A story relying on an established bible fact can record it as `sourced` with a
reference to that bible record. Do not invent a packet status that its schema
does not support.

## Connect the world

- Use stable IDs for characters, locations, facts and relationships. Names may
  change without breaking references.
- Describe relationships as directed when needed: one character's trust does not
  imply equal trust in return. Record the event behind each lasting change.
- Track what a character knows separately from what is true. Story knowledge
  records identify the beat where a belief or understanding changes.
- Keep chronology separate from presentation order. Use `timeline` for dated or
  ordered events; unknown dates remain null. Record ages, travel time or seasons
  when readers could infer a contradiction.
- Give locations consistent geography and objects consistent ownership and
  condition. The [location worksheet](../templates/location-map.md) helps record
  routes and distances without pretending an illustrative map is measured.
- Maintain `glossary` entries per language for names, invented terms and recurring
  phrases. Shared word choices belong in the [style sheet](../templates/style-sheet.csv).

After a story is accepted, re-read it and log every new fact, changed relationship,
learned fact and unresolved promise. Promote only supported facts; include story
ID, revision and beat reference. Use the [series grid](../templates/series-arc.csv)
to track growth across books or episodes without changing a character's core
traits accidentally. A new series outline remains a proposal until adopted.
