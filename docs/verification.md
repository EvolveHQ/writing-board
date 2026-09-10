# Bootstrap verification

Checked on 2026-09-10. Run `python scripts/verify.py` to repeat the maintained gate.

- Python regression checks cover story structure, causal and chronological
  references, page coverage, bible rules, revisions, source edits, malformed JSON,
  safe output paths and export/import preservation.
- Node checks execute the actual board script for editing, board selection,
  context changes, empty projects, complete bundle export, metadata preservation,
  stale evidence and save failures. These are DOM-stubbed state checks.
- The documented new-project journey was run through setup, character and story
  creation, validation, build, export, import, status and production handoff.
- The original sample validates without warnings. Skills validate, documentation
  links resolve, and the Markdown/HTML indexes match their generator.
- The decision catalog and work queue were audited against repository conventions.
  Intended public files were checked for private source material and credentials.

The in-app browser security policy blocked opening the local HTML during this
run. Rendered visual, responsive, keyboard and physical print checks therefore
remain unverified; the automated gate does not claim to replace them.

The sample remains a draft. No artwork, PDF, EPUB, language certification or
publication-ready book is claimed by this infrastructure verification.
