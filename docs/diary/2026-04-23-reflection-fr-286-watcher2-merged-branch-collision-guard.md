---

## 2026-04-23: Reflection — FR-286 Merged-Branch Collision Guard

**Context:** Evaluating and demonstrating FR-286, which adds a merged-PR branch-collision guard in `worktree_setup.sh`, routes collision to skip flow in `watcher2.sh`, and documents the behavior in `.chaplain/README.md`.

**Trap:** **false_duplicate** — I initially treated regex quantifier braces in a demo shell check as ordinary literals, but YAMLGraph command templating interpreted `{0,250}` as variable syntax (`Missing variable: '0,250'`). The text looked syntactically familiar while semantics differed at the template boundary.

**Heuristic:** **Boundary-aware assertions over templated regex** — inside YAMLGraph shell command templates, avoid brace-heavy regex unless escaped explicitly; prefer deterministic string/index assertions for infrastructure demos to prove behavior without template-language collisions.

**Seed:** Could watcher2 infrastructure demos have a built-in “template-safe assertion” helper (string contains / ordering predicates) so acceptance demonstrations stay robust without regex-template edge cases?
