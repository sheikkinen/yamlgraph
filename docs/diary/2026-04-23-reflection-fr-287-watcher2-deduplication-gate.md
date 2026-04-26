## 2026-04-23: Reflection — FR-287 Watcher2 Deduplication Gate

**Context:** Implementing and validating FR-287 to skip watcher2 cycles when a topic references an already-completed FR, including a pre-preflight dedup gate, skip-path metrics, documentation updates, and executable demo proof.

**Trap:** **false_duplicate** — in the first demo run, shell snippets that looked valid (`{...}` patterns/functions) were interpreted by YAMLGraph template substitution as variable placeholders, causing a runtime failure (`Missing variable ...`). The syntax looked familiar, but semantics differed at the template boundary.

**Heuristic:** **Template-safe shell in graph tool commands** — when building infrastructure demos in YAML graph tool nodes, avoid brace-heavy literals and compact brace blocks; prefer explicit `if` blocks and plain string outputs so demonstration logic is robust under template rendering.

**Seed:** Should YAMLGraph provide an opt-out flag or raw-shell block mode for tool command templating so shell demos can use native bash syntax without template-collision risk?
