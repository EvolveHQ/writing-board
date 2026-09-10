# Contributing

Read [AGENT.md](AGENT.md), the [file contract](docs/contracts.md),
[repository conventions](.docflow/CONVENTIONS.md) and
[decision catalog](.docflow/INDEX.md) before changing the tool. Follow the owning
plan in [.docflow/plan](.docflow/plan/README.md); create a plan before substantive
implementation. Record changed decisions explicitly.

The runtime is Python's standard library plus an offline browser. Preserve stable
IDs, unknown extension data, safe JSON embedding and revision-aware review
invalidation. Source JSON is authoritative; rebuild generated output. Tests
should exercise these behaviors rather than duplicate implementation details.

Run the full local gate with Python 3.11+ and Node 18+:

```sh
python scripts/verify.py
```

For interface changes, also build the original sample and exercise the affected
flow in a browser, including an export/import round trip when saving changes.
Inspect small and wide screens and keyboard operation where relevant. Report
what was checked and any remaining limits in the change description.

External contributors submit pull requests. The integrator uses signed
Conventional Commits and fast-forward integration after validation. Include a
`Rationale:` footer when changing decisions. Do not force-push `main` or add
co-author trailers unless requested.

Keep examples original and small. Do not contribute private manuscripts,
character assets, source-library copies, credentials or machine-specific paths.
Changes to skills should keep task routing specific and link shared guidance.
Update both documentation entrypoints through the repository's index generator.

See the [bootstrap verification record](docs/verification.md) for checks performed
and the limits of the initial interface verification.
