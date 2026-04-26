# Reflection: FR-289 watcher2 post-merge inbox consumption

**Context:** Implementing FR-289 to consume stale `.chaplain/inbox/*.md` items after merge when they reference the same `FR-[0-9]+` token, while preserving successful-merge behavior on cleanup errors.

**Trap:** `plausible_wrong_answer` — the first demo failure looked like a feature bug, but the real fault was shell-brace syntax in a YAMLGraph tool command being treated as template variables.

**Heuristic:** In YAMLGraph shell-tool demos, avoid brace-group conditionals (`|| { ... }`); prefer explicit `if ...; then ...; fi` so command text cannot be misparsed as templating input.

**Seed:** Should watcher demo graphs get a lightweight lint rule that rejects shell brace-groups inside tool commands to prevent this class of false-negative demo failures?
