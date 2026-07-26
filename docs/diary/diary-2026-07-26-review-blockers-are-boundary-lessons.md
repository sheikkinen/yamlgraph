# 2026-07-26 — Review blockers are boundary lessons in miniature

**Context:** Remediating independent-review blockers on PRs 462–465
(FR-759..762 dependency-governance arc). Four PRs, four "Not approved"
verdicts, each fixed in its own worktree via RED→GREEN.

**Observation:** Every blocker was the same defect wearing different
clothes: a check that validated *shape* instead of *substance* at a
boundary.

- PR 463 P1: `try:`-wrapped imports classified as lazy — but a top-level
  try executes at import time. The scanner modeled *syntax nesting*, not
  *execution semantics*.
- PR 463 P2: name-only `PENDING_GAPS` — a disposition granted for one
  file silently covered the whole tree. Exemption scope wider than the
  evidence that justified it.
- PR 464 P1: substring `"nodes:" in text` admitted prompt schemas
  (`affected_nodes:`) as graph definitions. String matching where a
  parser was one `yaml.safe_load` away — the `regex_fourth_exclusion`
  trap, caught by an external reviewer instead of by me.
- PR 464 P2: hook wiring changed outside frozen scope — scope creep with
  momentum, invisible to the author because it felt like "completing"
  the feature.

**Trap named:** `author_cannot_see_own_scope` — the same continuation
bias that writes plausible code also widens exemptions and hook triggers,
because from inside the change every widening feels like coherence, not
creep. The independent reviewer's value was not finding *bugs* but
finding *boundaries I had quietly moved*.

**Heuristic:** When writing any allowlist/exemption entry, key it by the
narrowest surface the evidence covers (file > directory > package >
never global-by-name). The GREEN fix for a too-wide exemption is always
a *key-type change*, not a value change — if fixing an exemption means
retyping the dict, the original schema encoded the bug.

**Validation bonus:** The P1 fix (try-imports are module-level)
immediately surfaced 7 real findings (`export/mcp.py`, `utils/fsm/`,
`a2a_client.py` protobuf) — the corrected boundary model paid for
itself in the same run that verified it.

**Seed:** Could the scanner's exemption schema be generalized into a
doctrine-level lint — any dict named `*_GAPS`/`*_ALLOWLIST`/`*_EXEMPT`
in `scripts/` whose keys are bare strings (not path-scoped tuples) gets
flagged at pre-commit? The key-type *is* the scope policy; make the
type checker enforce the doctrine.
