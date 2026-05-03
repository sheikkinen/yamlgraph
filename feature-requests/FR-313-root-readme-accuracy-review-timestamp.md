# Feature Request: FR-313 Root README Accuracy Review + Timestamp

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-03

## Summary

Review the root `README.md` against current codebase capabilities, correct stale claims, and add an explicit end-of-document review timestamp.

## Value Statement

New and returning users get a trustworthy front-door document that reflects real capabilities and includes a clear freshness signal.

## Problem

GitHub issue #285 requests: "Review README.md for accuracy against current codebase state. Update the review timestamp at the end of the document."

Current gaps:

1. `README.md` still contains stale provider coverage text (for example, `PROVIDER` row currently lists only `anthropic/mistral/openai`).
2. `README.md` contains a hardcoded "all 18 reference docs" claim while `reference/*.md` currently contains 29 files.
3. `README.md` has no explicit review timestamp marker at the end of the document.

Research confirmed there is no dedicated root README accuracy gate today:

- `tests/unit/test_examples_readme_audit.py` validates `examples/README.md` consistency.
- `tests/unit/test_chaplain_readme_documentation.py` validates `.chaplain/README.md`.
- Root `README.md` is only indirectly touched by unrelated tests (e.g., obsolete script reference checks), not by a comprehensive accuracy contract.

## Objectives

1. Align root README provider claims with implemented provider support.
2. Remove brittle hardcoded reference-document count wording from root README.
3. Add an explicit `Last reviewed: YYYY-MM-DD` marker at the end of root README.
4. Define failing acceptance checks that prove the current state is non-compliant before implementation.

## Constraints

- Scope is limited to root README accuracy and its verification.
- Do not change runtime behavior, graph execution, node semantics, or provider logic.
- Keep edits minimal and localized (`README.md` plus acceptance tests/documentation traceability as needed).
- Preserve the existing README structure; only correct inaccurate claims and add review metadata.

## Proposed Solution

1. Update root `README.md` provider references to match actual supported providers in:
   - `yamlgraph/config.py` (`DEFAULT_MODELS` keys)
   - `yamlgraph/utils/llm_providers.py` (`dispatch_provider()` branches)
2. Replace hardcoded "all 18 reference docs" phrasing with non-fragile wording that does not drift as docs are added.
3. Add a review metadata line at the end of `README.md`:
   - `Last reviewed: 2026-05-03`
4. Add a dedicated root README accuracy test file (documentation contract test) that validates provider list coverage, absence of fragile hardcoded reference-doc count text, and presence of the review timestamp.

## Acceptance Criteria

- [x] **AC-01:** Root `README.md` includes all currently supported provider identifiers in provider documentation sections (`anthropic`, `azure`, `deepseek`, `google`, `inception`, `lmstudio`, `mistral`, `openai`, `replicate`, `vertex`, `xai`).
- [x] **AC-02:** Root `README.md` no longer contains hardcoded `all <number> reference docs` phrasing.
- [x] **AC-03:** Root `README.md` ends with an explicit review timestamp line: `Last reviewed: 2026-05-03`.
- [x] **AC-04:** A dedicated unit documentation test exists for root README accuracy (provider coverage + stale count removal + timestamp presence).
- [x] **AC-05:** Changes remain docs/test only; no runtime/module behavior changes.

## Failing Acceptance Tests (RED)

Current failing checks in this worktree (run from repository root):

```bash
rg -n '^Last reviewed: 2026-05-03$' README.md
# exits 1 (timestamp line missing)

rg -n 'anthropic/azure/deepseek/google/inception/lmstudio/mistral/openai/replicate/vertex/xai' README.md
# exits 1 (provider row is incomplete)

! rg -n 'all [0-9]+ reference docs' README.md
# exits 1 (README still contains: "all 18 reference docs")

python - <<'PY'
from pathlib import Path
readme = Path("README.md").read_text()
row = [line for line in readme.splitlines() if line.startswith("| `PROVIDER` |")][0]
expected = ["anthropic","azure","deepseek","google","inception","lmstudio","mistral","openai","replicate","vertex","xai"]
missing = [p for p in expected if p not in row]
assert not missing, f"missing providers: {missing}"
PY
# exits 1 (missing providers today)
```

Planned RED test command after adding acceptance test file:

```bash
pytest tests/unit/test_root_readme_accuracy.py -q --no-cov
```

## Alternatives Considered

1. **Timestamp-only update** — Rejected. Satisfies freshness marker but not the core "accuracy against current codebase state" requirement.
2. **Manual review without tests** — Rejected. Drifts again without an enforcement mechanism.
3. **Generate README automatically from code metadata** — Rejected for now as overkill relative to this focused docs-correction scope.

## Related

- Topic source: GitHub issue #285 (`https://github.com/sheikkinen/yamlgraph/issues/285`)
- Requested local topic file: `.chaplain/processing/gh-285.md` (not present in this worktree)
- Target document: `README.md`
- Provider truth sources: `yamlgraph/config.py`, `yamlgraph/utils/llm_providers.py`
- Prior-art docs contract tests:
  - `tests/unit/test_examples_readme_audit.py`
  - `tests/unit/test_chaplain_readme_documentation.py`
  - `tests/unit/test_a2a_server_docs.py`

## Research Brief

### Existing Abstractions

- The repository already uses pytest-based documentation contracts for README-like artifacts.
- Root README lacks a comparable contract, creating a drift gap.

### Prior Art in This Codebase

- FR-086 and FR-091 are targeted README correctness edits with acceptance criteria-driven scope.
- FR-306 demonstrates minimal root README hygiene correction and shell-level RED checks.

### Classification Signal

- Abstraction level: **documentation contract**
- Recommended approach: **build** (small docs + tests change)
- Key risk: over-scoping into broad README rewrites; mitigation is strict AC-bound edits only.
