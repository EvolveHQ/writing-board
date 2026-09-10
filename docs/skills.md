# Agent skills

These repository-scoped skills give agents a focused workflow for each writing
stage. They are Markdown instructions, so humans can use the same steps. Start
with [AGENT.md](../AGENT.md), then read the relevant skill; no global installation
is required. Discovery varies by agent client, so provide the file path explicitly
when the client does not automatically discover this repository's `skills/`.

| Task | Skill |
| --- | --- |
| Start or inspect a workspace | [writing-setup](../skills/writing-setup/SKILL.md) |
| Set audience-specific rules | [writing-guidelines](../skills/writing-guidelines/SKILL.md) |
| Create or maintain characters and canon | [writing-bible](../skills/writing-bible/SKILL.md) |
| Develop alternatives, beats and a draft | [writing-story](../skills/writing-story/SKILL.md) |
| Plan pages and artwork | [writing-composition](../skills/writing-composition/SKILL.md) |
| Review and repair a story | [writing-review](../skills/writing-review/SKILL.md) |
| Adapt language editions | [writing-localization](../skills/writing-localization/SKILL.md) |
| Prepare production materials | [writing-production](../skills/writing-production/SKILL.md) |

Example request: "Use `skills/writing-story/SKILL.md` to develop two premise
alternatives for `projects/my-book`, then update the selected story's beats."
Provide the workspace path and the intended output; include an existing story ID
when applicable. Existing user choices and authorization take precedence over a
skill's defaults. Skills do not claim that unavailable generation, translation or
publishing services are installed.
