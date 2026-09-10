# Prepare language editions

Set intended language tags in `project.json`. Common tags include `en`, `it`,
`es`, `cs` and `sk`; use a regional tag such as `en-GB` when that distinction
matters. Czech uses `cs`; `CZ` is a country code. The selected languages are
project choices, not a fixed set built into the writing workflow.

Give each language edition a unique story ID and set `language` and
`source_story_id`. Record the source packet revision in `source_refs` or an
explicit extension field. Keep stable beat IDs across aligned editions so a
review can compare the same event. Record intentional structural changes in
`localization_notes` rather than silently dropping a beat.

1. Agree on the source revision and identify names, refrains, sounds, countable
   objects, teaching words, reader questions and text visible in art.
2. Add preferred terms to the shared glossary and note pronunciation or wording
   choices in the style sheet.
3. Adapt for natural speech. Preserve cause, emotional intent, agency and
   difficulty; translate a joke or sound by its function when literal wording
   fails. Do not add world facts to repair awkward phrasing.
4. Read the edition aloud with a competent reader of that language. A literal
   back-translation can reveal differences but does not prove naturalness.
5. Inspect the actual layout for accents, font coverage, line breaks, text length
   and image-text meaning. Avoid shrinking type to accommodate expansion.
6. Record translation and layout reviews for the edition's current revision.
   Reconcile every edition after a source story change.

There is no automatic translation service in the tool. Use the
[localization worksheet](../templates/localization.md) to document decisions and
remaining review needs. Language-sensitive font, hyphenation and final reading
direction are production responsibilities.
