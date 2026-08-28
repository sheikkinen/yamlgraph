# Judgement: FR-900 Ledger cache-price fix + monthly repo x model cost report

**Verdict:** APPROVED WITH REVISIONS — the defect and monthly attribution need are evidenced, but formal authority activates only after the FR/evidence are promoted into committed input-closure artifacts and the acceptance criteria are tightened to the exact callable seams.

**Reviewed against:** `feature-requests/FR-900-ledger-cache-price-fix-repo-report.md`; `scripts/vscode/ledger.py`; `tmp/fr900-raw/billing-blocks.json`; `tmp/fr900-raw/old-parser-prices.txt`; `tmp/fr900-raw/aug-report-corrected.txt`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; repository index status for those paths via `git ls-files`.

## What is sound

The core bug is real and localized. The target script reads `cache_price` in `load_prices()` (`scripts/vscode/ledger.py:43`, `scripts/vscode/ledger.py:64`) while the cited price-sheet evidence exposes `cache_read_price` and `cache_write_price` fields (`tmp/fr900-raw/billing-blocks.json:13-15`, `tmp/fr900-raw/billing-blocks.json:42-44`, `tmp/fr900-raw/billing-blocks.json:70-78`). The old parser output shows cache priced at zero across every listed family (`tmp/fr900-raw/old-parser-prices.txt:1-34`), matching the FR's defect statement (`feature-requests/FR-900-ledger-cache-price-fix-repo-report.md:21-24`, `feature-requests/FR-900-ledger-cache-price-fix-repo-report.md:39-45`).

The proposed parser and estimator seams are minimal and testable. Extracting `parse_price_sheet(data)` and a module-level `credits(prices, model, prompt, out)` makes the filesystem and arithmetic independently testable (`feature-requests/FR-900-ledger-cache-price-fix-repo-report.md:91-99`), and directly follows the repo doctrine to normalize external data at the boundary (`.github/copilot-instructions.md:50-52`) rather than compensating downstream.

The raw-output requirement for measurement work is substantively satisfied in the FR text: it names three raw samples and records concrete surprising details, including two-tier price blocks, two write-price keys, all-zero parsed cache fields, and a corrected August total (`feature-requests/FR-900-ledger-cache-price-fix-repo-report.md:57-74`). Those claims are corroborated by the cited files: fable has default and `long_context` prices (`tmp/fr900-raw/billing-blocks.json:13-24`), the corrected August total is `$3,927 .. $25,743` (`tmp/fr900-raw/aug-report-corrected.txt:24`), and the repo split directly answers the first consumer/event (`feature-requests/FR-900-ledger-cache-price-fix-repo-report.md:8-11`).

The strategic classification is **contrib/internal diagnostic tooling**: this is not a framework primitive, but it has a named recurring operator event and an existing script surface. Keeping the work in `scripts/vscode/ledger.py` aligns with the current spike/tooling location (`scripts/vscode/ledger.py:1-14`) and avoids graph or core framework expansion.

## Required revisions

### R-1: Promote input-closure evidence before enforcement

Commit the FR and either commit the cited `tmp/fr900-raw/*` evidence files or move their contents into a committed evidence artifact under `feature-requests/` before enforcement starts. The judge doctrine requires evaluation of committed artifacts only (`.github/skills/judge-fr/doctrine.md:16-23`); the repository index check showed only doctrine and `scripts/vscode/ledger.py` are currently tracked among the reviewed paths, while the FR and `tmp/fr900-raw/*` are not.

### R-2: Name the test and capability surfaces mechanically

Replace the unnumbered acceptance items "Tests added under `tests/unit/`..." and "Changelog fragment (fix) added" with numbered criteria naming the expected surfaces: a concrete `tests/unit/test_vscode_ledger.py` or equivalent unit-test file, a `capabilities/CAP-XXX-*.yaml` registry entry with the requirement ID used by `@pytest.mark.req`, and a `changelog/unreleased/*.md` fragment. This folds repo doctrine on requirement traceability into the FR instead of leaving the enforcer to infer it (`.github/copilot-instructions.md:175-176`).

### R-3: Specify the CLI smoke commands

State the exact smoke commands as acceptance criteria: `python3 scripts/vscode/ledger.py --help` and `python3 scripts/vscode/ledger.py --tap` must exit 0, and the new report path must be exercised with `python3 scripts/vscode/ledger.py --month 2026-08 --by-repo` against a fixture or monkeypatched `WS_STORAGE`. The current AC-05 mentions `--help` and `--tap` (`feature-requests/FR-900-ledger-cache-price-fix-repo-report.md:123-124`) but does not give the report command a testable execution context.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/vscode/ledger.py`: extract `parse_price_sheet(data)`, parse `cache_read_price` and `cache_write_price`, expose/test module-level `credits(...)`, add workspace/repo attribution, add `--month` and `--by-repo`, and update stale calibration text. |
| D-2 | Unit tests under `tests/unit/` for price parsing, credit arithmetic, workspace-name resolution, repo/model report grouping, and `--tap` unpacking. |
| D-3 | One capability registry entry under `capabilities/` and matching `@pytest.mark.req` markers for the new behavior. |
| D-4 | One fix changelog fragment under `changelog/unreleased/`. |
| D-5 | Committed evidence artifact preserving the raw price-sheet/parser/report observations currently cited from `tmp/fr900-raw/`. |

Not authorized: changing graph or prompt artifacts; adding non-stdlib dependencies; querying cloud session stores; recalibrating `CACHE_RATIO_BEST`; implementing long-context tier selection unless needed only to preserve current default-tier behavior; changing VS Code/Copilot data collection outside the existing local `workspaceStorage` read path; modifying judge/review doctrine, hooks, CI, or release tooling.

## Revised acceptance criteria

- [ ] AC-01: `parse_price_sheet(data)` on a fixture containing `token_prices.default.cache_read_price: 100`, `cache_write_price: 1250`, `input_price: 1000`, and `output_price: 5000` returns `{"in": 1000, "out": 5000, "cache": 100, "cache_w": 1250}` for the model family.
- [ ] AC-02: `load_prices()` delegates JSON parsing to `parse_price_sheet(data)` after selecting the newest `models.json`; filesystem absence or unreadable JSON preserves the existing empty-price behavior without hiding parse errors inside `parse_price_sheet`.
- [ ] AC-03: `credits(prices, "claude-fable-5", 1_000_000, 0)` returns best approximately `143` credits using `0.02 * (1000 + 1250) + 0.98 * 100`, and worst exactly `1000` credits before output cost.
- [ ] AC-04: `UNKNOWN_MODEL_PRICE` includes `cache_w`, and unknown-model estimation remains conservative relative to the known fable price family.
- [ ] AC-05: Workspace/repo resolution is tested from temporary `workspace.json` fixtures for `folder`, `workspace`, and `configuration` forms, with hash-prefix fallback when no basename can be resolved.
- [ ] AC-06: `iter_requests()` yields the resolved workspace/repo name in addition to timestamp, model, prompt tokens, output tokens, and session id; `tap_seam_report()` is updated to unpack the new shape and still returns a report instead of raising.
- [ ] AC-07: `python3 scripts/vscode/ledger.py --month 2026-08 --by-repo` groups fixture requests by `(repo, model)`, sorts rows by best-bound cost descending, prints per-repo totals, and prints a grand total.
- [ ] AC-08: The stale anchor-2 cache-pricing claim is removed or rewritten so the module docstring no longer asserts arithmetic produced under the `cache_price` bug; the August 2026 invoice anchor from the FR is recorded with its two-device assumption.
- [ ] AC-09: `python3 scripts/vscode/ledger.py --help` and `python3 scripts/vscode/ledger.py --tap` exit 0 in the test environment.
- [ ] AC-10: Tests are added under `tests/unit/` with `@pytest.mark.req("REQ-YG-XXX")`, and the matching `capabilities/CAP-XXX-*.yaml` entry defines that requirement.
- [ ] AC-11: A `changelog/unreleased/*.md` fix fragment names FR-900 and the requirement ID.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Enforcement may begin only after R-1 through R-3 are folded into the FR or captured in an updated judgement artifact. | GATE |
| C-2 | No implementation may rely on uncommitted `tmp/fr900-raw/*` files at runtime; they are evidence only. | GATE |
| C-3 | The price parser must fail loudly in tests for schema drift at `parse_price_sheet(data)`; only filesystem discovery in `load_prices()` may preserve the current empty-price behavior when no sheet exists. | GATE |
| C-4 | The report must use local VS Code `workspaceStorage` witnesses only; cloud session-store reconciliation and cache-ratio recalibration are out of scope. | GATE |
| C-5 | No graph/prompt authoring, judge/review doctrine edits, hook edits, CI edits, or release-process edits are authorized by this FR. | GATE |

Authority granted: after the required revisions are folded, implement the ledger parser, estimator, workspace attribution, monthly repo-by-model report, documentation correction, tests, capability entry, changelog fragment, and committed evidence artifact exactly within the frozen scope above.

**Prior art:** dispositioned in the FR body (FR-884 different deliverable; FR-219/FR-381 framework caching/batching, keyword-only hits).
