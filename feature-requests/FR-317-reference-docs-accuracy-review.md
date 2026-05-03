# Feature Request: FR-317 Reference Docs Accuracy Review + Review Timestamps

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-03

## Summary

Review all `reference/*.md` documents for accuracy against the current codebase, correct discovered drift, and append an explicit `Last reviewed: YYYY-MM-DD` marker to each reviewed document.

## Value Statement

Users and contributors get trustworthy reference documentation with a visible freshness signal, reducing setup/debug time caused by stale commands, paths, and examples.

## Problem

GitHub issue #294 requests a full accuracy review for reference docs, including timestamp updates.

Current baseline findings in this worktree:

1. `reference/` contains 29 markdown documents and **none** currently includes `Last reviewed:`.
2. The repo has targeted doc tests for individual files/topics, but no global reference-doc review freshness contract.
3. At least one stale local cross-reference exists now: `reference/graph-yaml.md` links to `../examples/copilot/`, which is missing.

## Objectives

1. Review every markdown file under `reference/` for API/CLI/path/config accuracy against current code.
2. Correct any inaccuracies discovered during that review sweep.
3. Append `Last reviewed: 2026-05-03` at the end of each reviewed `reference/*.md` file.
4. Add a lightweight contract test so timestamp and local-link drift are caught by CI.

## Constraints

- Scope is docs + docs-tests only (`reference/*.md` and `tests/unit/*` as needed).
- Do not change runtime behavior, graph execution logic, providers, or CLI implementation.
- Keep edits minimal and evidence-based; use current source files as truth.
- Keep this FR single-purpose: reference documentation accuracy + freshness metadata.

## Proposed Solution

1. Perform a full reference-doc audit (`reference/*.md`) against code truth sources:
   - CLI behavior/flags: `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/graph_validate.py`
   - Graph/node semantics: `yamlgraph/models/graph_schema.py`, `yamlgraph/node_factory/*`, `yamlgraph/pipeline_template.py`, `yamlgraph/interactive_tool.py`
   - Prompt/schema behavior: `yamlgraph/executor.py`, `yamlgraph/schema_loader.py`
   - Release/break-glass procedures: `scripts/release.sh`, `.github/workflows/commitlint.yml`, current `reference/break-glass.md`
2. Fix stale commands, file paths, module references, and doc cross-references found during audit.
3. Add `Last reviewed: 2026-05-03` to each `reference/*.md` file.
4. Add one focused unit test (docs contract) asserting:
   - each `reference/*.md` includes `Last reviewed: 2026-05-03`
   - no broken local markdown links remain inside `reference/*.md`

## Acceptance Criteria

- [x] **AC-01:** Every `reference/*.md` file includes `Last reviewed: 2026-05-03` as an end-of-document review marker.
- [x] **AC-02:** Accuracy sweep covers all reference docs and fixes drift in commands, API/module references, config options, and doc cross-references discovered during audit.
- [x] **AC-03:** `reference/graph-yaml.md` no longer links to missing `../examples/copilot/` (and no equivalent broken local links remain in `reference/*.md`).
- [x] **AC-04:** A dedicated docs contract test exists and enforces review timestamp presence and local-link validity for all `reference/*.md`.
- [x] **AC-05:** Changes remain documentation/test-only; no runtime code changes.

## Failing Acceptance Tests (RED)

Current failing checks in this worktree:

```bash
python - <<'PY'
from pathlib import Path
missing = []
for path in sorted(Path("reference").glob("*.md")):
    if "Last reviewed:" not in path.read_text(encoding="utf-8"):
        missing.append(path.name)
assert not missing, f"Missing Last reviewed in {len(missing)} files: {', '.join(missing)}"
PY
# exits 1 (currently missing in all 29 reference docs)

python - <<'PY'
import re
from pathlib import Path
root = Path(".").resolve()
pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
broken = []
for md in sorted(Path("reference").glob("*.md")):
    content = md.read_text(encoding="utf-8")
    for link in pattern.findall(content):
        target = link.split("#", 1)[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        resolved = (md.parent / target).resolve()
        if root not in resolved.parents and resolved != root:
            continue
        if not resolved.exists():
            broken.append((str(md), link))
assert not broken, "Broken links: " + "; ".join(f"{src} -> {lnk}" for src, lnk in broken)
PY
# exits 1 (currently: reference/graph-yaml.md -> ../examples/copilot/)
```

Planned RED test command after adding the docs contract test file:

```bash
pytest tests/unit/test_reference_docs_accuracy_review.py -q --no-cov
```

## Alternatives Considered

1. **Timestamp-only update without accuracy audit** — Rejected. Satisfies freshness marker but not the issue’s core accuracy objective.
2. **Manual review without tests** — Rejected. Drift would recur without automated enforcement.
3. **Automated generation of all reference docs from code** — Rejected for this FR as over-scope relative to a focused audit + guard.

## Related

- Topic source: GitHub issue #294 (`https://github.com/sheikkinen/yamlgraph/issues/294`)
- Requested local topic file: `.chaplain/processing/gh-294.md` (not present in this worktree)
- Prior-art FRs:
  - `feature-requests/FR-313-root-readme-accuracy-review-timestamp.md`
  - `feature-requests/FR-314-chaplain-readme-retry-requeue-workflow.md`
  - `feature-requests/FR-155-reference-readme-stale-doc-count.md`
- Existing doc-contract tests (targeted, not global):
  - `tests/unit/test_race_pipeline_docs.py`
  - `tests/unit/test_branch_protection_docs.py`
  - `tests/unit/test_changelog_release_sync.py`
  - `tests/unit/test_guardrails_pattern_docs.py`

## Research Brief

### Existing Coverage

- The codebase already uses pytest documentation contracts for individual docs/sections.
- There is no single contract today requiring review timestamps across all reference docs.
- There is no global broken-link guard focused on `reference/*.md`.

### Scope Decision

- Keep this FR narrowly scoped to one concern: **reference docs accuracy and freshness metadata**.
- Avoid runtime or architectural changes; enforce via docs edits plus one focused docs contract test.
