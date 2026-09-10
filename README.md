# Writing Board

Writing Board is a portable workspace for planning illustrated books and keeping
a series consistent. It combines an editable corkboard, writing guidelines,
character and world bibles, page plans, continuity records and reusable agent
skills. Authors and agents work from the same JSON documents.

The generated board works offline in a browser. Python 3.11+ builds and validates
projects; no Python packages, account or hosted service are required. Node 18+ is
needed only to run the contributor checks.

## Try the board

Clone the repository, then run commands from its root:

```sh
git clone https://github.com/EvolveHQ/writing-board.git
cd writing-board
python scripts/writing_board.py build examples/rainy-day
```

Open `examples/rainy-day/build/board.html` in a browser. Select a story, review its
purpose, move or edit beats, inspect continuity and plan its pages. Project,
guidelines and bible editors provide the shared context for every story.

## Start your book

```sh
python scripts/writing_board.py init projects/my-book --interactive
python scripts/writing_board.py character projects/my-book --id hero --name "Hero"
python scripts/writing_board.py story projects/my-book --id first-story --title "First story" --protagonist hero
python scripts/writing_board.py build projects/my-book
```

Open `projects/my-book/build/board.html`. Browser edits remain in memory until
exported. Use **Export project**, then import that bundle into a new workspace;
see the [save workflow](docs/board.md). Private work belongs in ignored
`projects/` or outside this repository.

## Documentation

| Need | Read |
| --- | --- |
| Find every guide and worksheet | [Documentation index](docs/index.md) · [HTML index](docs/index.html) |
| Follow the whole process | [Writing workflow](docs/workflow.md) |
| Edit, save and exchange boards | [Using the board](docs/board.md) |
| Set audience, voice and craft rules | [Writing guidelines](docs/guidelines.md) |
| Create characters and maintain canon | [Character and world bible](docs/bible.md) |
| Plan images, text and page turns | [Composition](docs/composition.md) |
| Check story quality and continuity | [Review](docs/review.md) |
| Prepare language editions | [Localization](docs/localization.md) |
| Prepare artwork and publishing work | [Production handoff](docs/production.md) |
| Direct an agent | [Agent skills](docs/skills.md) · [Agent instructions](AGENT.md) |
| Integrate or extend the tool | [File and command contracts](docs/contracts.md) · [Contributing](CONTRIBUTING.md) |

The initial format is illustrated books. Word counts and picture-book pacing are
editable preferences. The tool prepares manuscripts, art briefs and a production
inventory; it does not generate artwork, PDF files or EPUB files. Validation
checks structure and consistency, while editorial and production reviews remain
separate recorded work.

Code, guides and the original sample are available under the [MIT license](LICENSE).
