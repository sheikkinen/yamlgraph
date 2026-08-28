# Feature Request: Ledger cache-price fix + monthly repo×model cost report

**Priority:** MEDIUM
**Type:** Bug + Enhancement
**Status:** Enforced — 2026-08-28 (all ACs green; report reconciles with the August invoice within ~5%)
**Effort:** 0.5 days
**Requested:** 2026-08-28
**First consumer / first event:** The operator, reconciling the August 2026
Copilot invoice ($7,500 actual vs $796 ledger estimate — a 10× gap reported
2026-08-28). The fixed ledger and the `--month --by-repo` report answer
"which repo and model spent it" the next time a monthly bill arrives.
**Research:** In-body dispositioned alternatives table (FR-889 style) — see
[Alternatives Considered](#alternatives-considered). The defect was located
by direct raw-artifact read (below), not by candidate exploration; the
alternatives table dispositions the repair options.

## Summary

`scripts/vscode/ledger.py::load_prices()` reads the nonexistent key
`cache_price` from models.json price sheets; the real schema key is
`cache_read_price`. Every model therefore gets cache-read price **0**, and
the calibrated "98%-cached best" estimate prices 98% of all prompt tokens
as free — a ~5× underestimate. The estimator also ignores
`cache_write_price` (1.25× input for fable) entirely. Fix the parser, add
the cache-write term, and promote the ad-hoc August analysis
(tmp/aug_cost_by_repo_model.py) into ledger.py as a `--month YYYY-MM
--by-repo` report that splits cost by workspace/repo and model.

## Value Statement

The operator gets cost attribution that reconciles with the actual invoice
(verified within ~5% for August 2026), split by repo and model, from one
command — instead of a silently 10×-low number that misinforms model- and
project-level spend decisions.

## Problem

- **Bug (P1):** models.json `token_prices.default` uses keys
  `input_price`, `output_price`, `cache_read_price`, `cache_write_price`,
  `cache_write_1h_price`. `load_prices()` reads `cache_price` → 0 for all
  34 models in the current sheet. With `CACHE_RATIO_BEST = 0.98`, the best
  bound becomes `0.02 × input + 0.98 × 0` — August best-bound reported
  $796 while the actual bill was $7,500 (this device ≈ 50% of it).
- **Bug (P2):** cache *writes* are billed (fable: 1250 cr/M = 1.25× input)
  but never costed. At an agent-turn cache ratio of 98%, every fresh token
  is also written to cache once — the write term belongs in the best bound.
- **Stale calibration note:** the `credits()` docstring's anchor-2 claim
  ("pure-cache pricing of the full turn hit 814 cr vs 820.5 actual") is
  arithmetically impossible under the cache=0 bug (pure-cache would have
  priced ≈0). The comment must be corrected or re-derived — as written it
  lends false authority to broken arithmetic.
- **Missing report:** ledger.py aggregates by period and model only. The
  invoice reconciliation question — *which repo* spent it — required a
  one-off script. Workspace attribution (workspaceStorage hash →
  workspace.json → folder name) is cheap and answers it.

## Raw Output Read (measurement / metric-tooling FRs only)

- **Samples read:** committed evidence artifact
  [FR-900-evidence.md](FR-900-evidence.md) (R-1: promoted from tmp/fr900-raw/ —
  raw billing blocks for claude-fable-5 / claude-sonnet-5 / gpt-5.6-sol,
  old-parser price table, corrected August report; source models.json path
  recorded inside).
- **What I saw:**
  - fable's billing block has **two tiers** — `default` (max_prompt_tokens
    200,000) and `long_context` (max_prompt_tokens **936,000**, same
    prices) — a tier structure the parser silently flattens to `default`.
  - `cache_write_1h_price: 2000` exists alongside `cache_write_price:
    1250` — there are *two* write prices (5-min vs 1-h TTL), neither read.
  - The old parser output shows `'cache': 0` for **every** family
    including gpt-3.5-turbo whose *all* prices are 0 — zero is both
    "free model" and "missing key", indistinguishable downstream.
  - Corrected August total: $3,927 best on this device; +~equal second
    device ≈ $7.9K vs $7,500 actual — within 5%.

## Ideal Result

`python3 scripts/vscode/ledger.py --month 2026-08 --by-repo` prints a
repo×model cost table whose best-bound total reconciles with the actual
invoice within the estimator's stated noise, using cache-read and
cache-write prices actually present in the price sheet; the docstring's
calibration claims are consistent with the arithmetic that produced them.

## Proposed Solution

Minimal path back from the ideal, all inside `scripts/vscode/ledger.py`
(stdlib-only spike suite conventions preserved):

1. **Parser fix.** Extract a pure `parse_price_sheet(data) -> dict`
   (testable without the filesystem); read `cache_read_price` as `cache`
   and `cache_write_price` as `cache_w`. `load_prices()` becomes
   glob-newest + `parse_price_sheet`.
2. **Estimator fix.** Extract module-level
   `credits(prices, model, prompt, out) -> (best, worst)`. Best bound:
   `fresh × (in + cache_w) + cached × cache` per prompt token, plus
   output. Worst bound unchanged (all-fresh, no write term — ceiling
   semantics preserved). `UNKNOWN_MODEL_PRICE` gains `cache_w: 1250`.
3. **Repo attribution.** `iter_requests()` additionally yields the
   workspace name resolved from `<ws>/workspace.json` (`folder` |
   `workspace` | `configuration` basename, hash-prefix fallback).
4. **Report.** `--month YYYY-MM` (filter) + `--by-repo` (group by
   (repo, model), sorted by best-bound cost, with per-repo totals and a
   grand total) — the promoted tmp/aug_cost_by_repo_model.py output shape.
5. **Docstring truth.** Rewrite the `credits()` calibration note: state
   that anchor-2's "814 vs 820.5" was computed under the cache=0 bug and
   is void; record the new external anchor (August 2026 invoice $7,500,
   two devices, this device $3,927 best-bound ≈ 50% — within ~5%).

## Acceptance Criteria (revised per judgement, binding)

- [x] AC-01: `parse_price_sheet(data)` on a fixture containing
  `token_prices.default.cache_read_price: 100`, `cache_write_price: 1250`,
  `input_price: 1000`, `output_price: 5000` returns
  `{"in": 1000, "out": 5000, "cache": 100, "cache_w": 1250}` — RED first
  against the current `cache_price` reader.
- [x] AC-02: `load_prices()` delegates JSON parsing to `parse_price_sheet`
  after selecting the newest models.json; filesystem absence / unreadable
  JSON preserves existing empty-price behavior; parse errors are not hidden
  inside `parse_price_sheet`.
- [x] AC-03: `credits(prices, "claude-fable-5", 1_000_000, 0)` best ≈ 143 cr
  (`0.02×(1000+1250) + 0.98×100`), worst exactly 1000 cr before output.
- [x] AC-04: `UNKNOWN_MODEL_PRICE` includes `cache_w`; unknown-model
  estimation remains conservative relative to fable.
- [x] AC-05: workspace/repo resolution tested from tmp `workspace.json`
  fixtures for `folder`, `workspace`, `configuration` forms, with
  hash-prefix fallback.
- [x] AC-06: `iter_requests()` yields the resolved repo name in addition to
  its current fields; `tap_seam_report()` unpacks the new shape and still
  returns a report instead of raising.
- [x] AC-07: `--month 2026-08 --by-repo` groups fixture requests by
  `(repo, model)`, sorts by best-bound cost descending, prints per-repo
  totals and a grand total (exercised with monkeypatched `WS_STORAGE`).
- [x] AC-08: stale anchor-2 cache-pricing claim removed/rewritten; August
  2026 invoice anchor ($7,500, two devices, this device $3,927 best-bound)
  recorded in the module docstring.
- [x] AC-09: `python3 scripts/vscode/ledger.py --help` and `--tap` exit 0.
- [x] AC-10: tests in `tests/unit/test_vscode_ledger.py` with
  `@pytest.mark.req("REQ-YG-626")`; `capabilities/CAP-251-*.yaml` defines
  that requirement.
- [x] AC-11: `changelog/unreleased/*.md` fix fragment names FR-900 and
  REQ-YG-626.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Fix only the key name, skip cache-write term | REJECTED — write cost at 98% cache ratio is ~2.5% of prompt cost for fable but the fix is one term; leaving it out repeats the "known billed component priced at zero" defect class just corrected |
| Keep the repo report as tmp/ one-off | REJECTED — the invoice question recurs monthly; tmp/ is unversioned and already diverged from the fixed pricing once (this session) |
| Read `long_context` tier prices per-request by token count | REJECTED (scope) — both tiers carry identical prices in the current sheet; tier selection adds complexity with zero present-day cost difference; revisit if sheets diverge |
| Query cloud session store (chronicle) for token usage | REJECTED — local SQLite store records no per-event token usage; cloud sync not enabled; chatSessions jsonl is the only local witness |
| Re-derive CACHE_RATIO_BEST from the new anchor | REJECTED (scope) — invoice reconciles within 5% at 0.98; recalibration needs per-turn billed data we don't have locally |

## Related

- [scripts/vscode/ledger.py](../scripts/vscode/ledger.py) — the fix target
- tmp/fr900-raw/ — raw evidence (billing blocks, old parser output, corrected report)
- FR-739 (tap seam), FR-888 (worktree route), session-introspection skill
- Scripture: `read_raw_output_first` — the defect was found by reading the
  raw billing block after the aggregate looked wrong, not by instrumenting

**Prior art:** FR-884 (chat-session task-shape mining) reads the same
chatSessions store but mines task shapes, not billing — no overlap in
deliverable. FR-219 (Anthropic prompt-caching demo) and FR-381 (batch_llm
node) concern framework LLM-call caching/batching, not local cost
estimation tooling; keyword-only hits ("cache", "price"). None constrains
or duplicates this scope.

## Judgement (2026-08-28)

**Verdict:** APPROVED with corrections — see
[FR-900-ledger-cache-price-fix-repo-report.judgement.md](FR-900-ledger-cache-price-fix-repo-report.judgement.md)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | FR + raw evidence untracked | FR, judgement, and FR-900-evidence.md committed before enforcement |
| R-2 | Test/CAP/changelog surfaces unnamed | tests/unit/test_vscode_ledger.py, CAP-251 / REQ-YG-626, changelog fragment — folded into ACs |
| R-3 | Smoke commands unspecified | exact `--help`, `--tap`, `--month --by-repo` commands folded into AC-07/AC-09 |

**Purge list:** none (no invented interfaces yet).

**Scope frozen:** D-1..D-5 per judgement; not authorized: graph/prompt
authoring, non-stdlib deps, cloud stores, CACHE_RATIO_BEST recalibration,
long-context tier selection, hook/CI/release edits.

### Questions for the human (as options, or 'none')

none
