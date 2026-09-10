# Production handoff

Writing Board exports the materials needed by an illustrator, designer or a
separate publishing pipeline. It does not generate images, PDFs or EPUBs, purchase
assets or upload books to a publisher.

```sh
python scripts/writing_board.py build projects/my-book
python scripts/writing_board.py validate projects/my-book
python scripts/writing_board.py handoff projects/my-book --output projects/handoff
```

The handoff contains manuscript, art briefs and an inventory of requested
deliverables. Use a new output directory so different handoffs remain identifiable.
Record project revision, story revisions, language, edition and references to
the approved visual sources. Send referenced assets separately: JSON references
do not embed the files or convey a license to use them.

## Specify the actual deliverables

| Deliverable | Decisions and checks |
| --- | --- |
| Reading PDF | Page or spread presentation, screen readability, file size, selectable text and navigation where useful. |
| Publishing PDF | Chosen printer, trim size, bleed, safe areas, binding, paper, color profile, image resolution, embedded fonts and required cover template. |
| EPUB | Fixed or reflowable layout, supported devices, editable text, reading order, navigation, accessibility descriptions and package validation. |
| Artwork | Cover, interior scenes, branding supplied by the project, editable source files and text-free versions for localization. |

Exact production settings depend on the chosen vendor and format; a universal
"publishing PDF" preset cannot establish compliance. Keep those specifications
with the handoff. The [production checklist](../templates/production-handoff.md)
records assignments and acceptance evidence.

Review exported files in their intended form. Inspect every page, compare each
language with its manuscript and verify illustrations against the bible. Check
physical object support, count and continuity as well as visual style. Record
the actual file and packet revision in proof records, then update the series
bible with supported story facts. Unfinished reviews remain visible; generating
a handoff does not mark the story approved.
