# Using the board

Run `build` for a workspace, then open its `build/board.html`. The selector lists
the actual story packets packaged with that workspace. A generated board is a
snapshot: rebuild and reopen it to see later source changes.

| View | Use it to |
| --- | --- |
| Corkboard | Read, edit and reorder beats; inspect causes, consequences and character choices. |
| Story purpose | State the teaching goal, lesson, meaning and the actions that deliver them. |
| Scene grid | Check reading order, chronology, cast, location, causes and consequences. |
| Page plan | Assign spreads, choose framing and separate the contribution of words and images. |
| Continuity | Inspect props, knowledge, relationships, facts and open threads. |
| Review | Inspect structural findings and the revision-specific review record. |

Use the shared project, guidelines and bible editors to change the context for
all stories. Keep stable IDs when editing characters, places and beats. Moving a
card changes reading order; check chronological order and causal references too.
Print cards when a physical board helps planning.

## Save work from the browser

The browser does not write into workspace source files. Export before closing or
refreshing the tab. **Export project** includes project settings, guidelines, the
bible and every current story. A packet export contains one story only; it is not
a backup of the shared project context. Keep one active editing copy at a time.

After exporting a project bundle to `projects/edited.json`:

```sh
python scripts/writing_board.py import projects/my-book --bundle projects/edited.json --output projects/revised
python scripts/writing_board.py validate projects/revised
python scripts/writing_board.py build projects/revised
```

Continue from `projects/revised/build/board.html`. Import requires the matching
project ID and base revision and creates a new directory. It advances the project
revision and invalidates review evidence for imported stories. The original
workspace is retained. If the base differs, reconcile the changes against the
current workspace; do not edit revision numbers to bypass the conflict.

To export the source workspace directly:

```sh
python scripts/writing_board.py export projects/my-book --output projects/snapshot.json
```

You may also edit source JSON directly. Rebuilding compares source documents with
the baseline from the last managed write and invalidates review evidence when authored content
changes. Recording reviews alone keeps the current revision. Run `build` after
source edits; other commands reject unbuilt content changes so an older bundle
cannot silently replace them. Do not edit
generated HTML as a substitute for updating the source. Referenced artwork and
supplemental worksheets need their own backup; the bundle contains structured
documents, not the referenced files.
