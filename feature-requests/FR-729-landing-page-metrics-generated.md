# Feature Request: FR-729 Landing Page Metrics — Generate, Don't Hand-Maintain

**Priority:** LOW
**Type:** Enhancement (docs infrastructure)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-07-14
**Spawned by:** Pages outage repair (fix 013ff5ae, 2026-07-14). The site's
first deploy in ~2 months went live and immediately revealed a second,
quieter failure: every quality claim on the landing page is stale by up to
5×. Detection without enforcement, in marketing form.
**Related:** docs/index.html (the page), NC-372 (ninchat's generated-map +
drift-gate precedent), FR-335 (module-map generator + budget gate),
`detection_without_enforcement` / `gate_checks_shape_not_substance`
(Scripture traps), scripts/aggregate_capabilities.py (generator precedent)

## Summary

`docs/index.html` hand-codes quality metrics that were true once
(footer says v1.0): **1026 tests / 91% coverage / ~6,100 LOC / 14 example
graphs / "7 node types"**. Reality on 2026-07-14: **~4,930 tests, 90.4%
coverage, ~21k LOC, ~50 demo dirs, 15 node types**. Replace the hand-typed
numbers with generated values and add a drift gate so the page can never
silently lie again — the NC-372 pattern (generate + gate), applied to the
shop window.

## Value Statement

The landing page is the project's most-viewed artifact and currently its
least accurate one; a generated metrics block turns it from a liability
(claims falsifiable by `pytest --collect-only` in 10 seconds) into evidence.

## Problem

1. Metrics are string literals in `docs/index.html` (L64–72, L450–458,
   L253). Nothing regenerates them; nothing fails when they drift.
2. The drift is not cosmetic: "7 node types" undersells the framework by
   half (NodeType enum has 15); "1026 tests" undersells by ~4,000. Stale
   *under*-claims are still substance failures — the gate class is
   identical to the one that let Pages stay red for two months.
3. The footer version ("v1.0") contradicts the release stream (v0.5.13
   today), which reads as abandonment.

## Proposed Solution

### 1. `scripts/generate_site_metrics.py` (stdlib only, no LLM)

Computes, from the repo, a single JSON dict:
- `tests`: `pytest --collect-only -q` count (or cheaper: count of
  `def test_` via AST over tests/ — pick one, pin it in the FR at judge)
- `coverage`: read from the CI-published coverage value or `.coverage`
  summary — if neither is cheaply available offline, drop the decimal
  ("90%+") and source it from the last CI badge value; no fabrication
- `loc`: `wc -l` over `yamlgraph/**/*.py`
- `node_types`: `len(NodeType)` imported from `yamlgraph.constants`
- `examples`: count of `examples/demos/*/graph.yaml`
- `version`: from `pyproject.toml`

### 2. Injection markers in `docs/index.html`

Metrics values sit between HTML comments
(`<!-- metrics:tests -->4930<!-- /metrics -->`); the generator rewrites in
place, idempotently. The "7 node types" copy becomes generated
(`{n} node types`), and the footer version becomes `v{version}`.

### 3. Drift gate (pre-commit, same ring as module-map/NC-372)

Hook: run generator in `--check` mode; fail the commit when the committed
HTML differs from regenerated output. Files-scoped to `docs/index.html`,
`yamlgraph/constants.py`, `pyproject.toml`, `tests/**` so it stays cheap.

### Out of scope (purge list)

- Redesigning the page, adding FR-723 marketing copy, or new sections.
- Live badges / client-side fetching (static site stays static).
- Generating the eBook links or any prose.

## Acceptance Criteria

- [ ] AC-01 RED — `--check` mode exits non-zero against today's stale
      index.html (the condemning test is the current page).
- [ ] AC-02 — generator run rewrites only marker spans; `git diff` shows
      numbers and version, no markup churn; idempotent (second run = no-op).
- [ ] AC-03 — pre-commit hook wired; a doctored stale value blocks commit.
- [ ] AC-04 — node-type count imports the enum (no second hand-count);
      test count method pinned and tested against a fixture tree.
- [ ] AC-05 — changelog fragment; REQ under CAP-10 or a docs CAP; diary
      reflection (trap: the shop window had no gate; cure: generate + gate,
      third instance of the NC-372 pattern — candidate for Scripture
      graduation as `generated_or_gated_claims`).

## Alternatives Considered

- **Hand-fix the numbers once:** repeats the original sin; they were
  hand-true once too. Rejected — fix ships *with* the gate or not at all.
- **Delete the metrics section:** honest but wasteful; the numbers are
  genuinely good marketing when true.
- **CI-only check (no pre-commit):** acceptable fallback if the hook is
  too slow; judge decides placement, but *some* blocking ring is
  non-negotiable (`audit_gate`).
