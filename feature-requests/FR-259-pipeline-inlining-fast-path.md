# Feature Request: FR-259 Pipeline Inlining — Fast Path for Trivial Changes

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1.5 days
**Requested:** 2026-04-20

## Summary

Add a severity classifier to the Chaplain pipeline that triages proposals into a fast path (direct PR without worktree) or the full path (Plan → Judge → Enforce via worktree). Trivial single-file changes — typo fixes, import cleanup, version bumps, dead code removal — bypass worktree creation and LLM enforce overhead while retaining all pre-commit safety gates and CI via a minimal PR.

## Value Statement

Pipeline operators reclaim ~17.5 minutes per trivial fix by eliminating worktree, LLM enforce, and post-assertion overhead for changes that pre-commit hooks and CI alone can validate, while preserving the full pipeline for behavioral changes.

## Problem

Every proposal — regardless of size — runs through the full Chaplain pipeline: Plan → Judge → Enforce (worktree, PR, CI). For a typo fix, variable rename, or version bump, this is disproportionate: worktree creation, branch, LLM enforce graph, post-assertions, PR, CI checks, diary reflection — all for a one-line change.

The Inquisitor already identifies micro-fixes (lint findings, dead code, naming inconsistencies), but these get promoted to full FRs. FR-256 metrics show enforce cycles range from 10 minutes to 2+ hours — even for changes that touch a single file and modify fewer than 10 lines.

**Observed overhead per trivial fix (current pipeline):**

| Phase               | Time     | Needed for typo fix? |
|---------------------|----------|----------------------|
| Worktree creation   | ~12s     | No                   |
| LLM enforce         | 10–120m  | No                   |
| Post-assertions     | ~3m      | No                   |
| PR creation + CI    | ~5m      | **Yes**              |
| Pre-commit hooks    | ~30s     | **Yes**              |

## Proposed Solution

### 1. Severity classifier in Plan prompt

After the Plan graph produces a draft FR, the Plan prompt classifies the change as `Type: Micro-fix` when all fast-path eligibility criteria are met. The Judge validates this classification and may override it to a standard type if criteria are not satisfied.

**Fast-path eligibility criteria (all must be true):**

1. Single file changed
2. Fewer than 10 lines changed
3. No new tests needed (no behavioral change)
4. No API change (no new public functions, no signature changes)
5. No new dependencies
6. FR `Type` field is `Micro-fix`
7. Commit type is NOT `fix` or `feat` (these require changelog/diary gates)

**Classification is conservative:** if any criterion is ambiguous, the full path is used.

Add the following instruction block to `.chaplain/graphs/copilot/prompts/plan.yaml`, appended to the existing user prompt:

```yaml
  # FR-259: Micro-fix severity classification
  If the proposal meets ALL of the following criteria, set `Type: Micro-fix`
  and add a `Commit-Type:` field with the appropriate conventional commit type:
  - Single file changed
  - Fewer than 10 lines changed
  - No new tests needed (no behavioral change)
  - No API surface change (no new public functions, no signature changes)
  - No new dependencies
  - Commit type is docs, chore, style, or refactor (NOT fix or feat)

  Commit-Type values: docs (docstring/comment), chore (version bump, config),
  style (import ordering, formatting), refactor (rename, dead code removal).

  When in doubt, do NOT classify as Micro-fix — use the standard Type value.
```

This adds two metadata fields to micro-fix FRs:

```markdown
**Type:** Micro-fix
**Commit-Type:** docs
```

### 2. TEMPLATE.md update

Update `feature-requests/TEMPLATE.md` line 4 to include `Micro-fix`:

```markdown
**Type:** Feature | Bug | Enhancement | Micro-fix
<!-- Micro-fix: single-file, <10 lines, no behavioral change, docs/chore/style/refactor only -->
```

### 3. watch.sh routing

Insert the Micro-fix fast-path check **between** the existing Rejected check and the Bug check, preserving the routing order invariant (Rejected → Micro-fix → Bug → default):

```bash
if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
    echo "⏭️  Skipping rejected FR: $new_fr"
# FR-259: Fast path for trivial changes
elif grep -q 'Type.*Micro-fix' "$new_fr" 2>/dev/null; then
    echo "⚡ Fast path (inline): $new_fr"
    mkdir -p tmp
    LOG="tmp/inline-$(basename "$new_fr" .md).log"
    EXIT_CODE=0
    scripts/inline_commit.sh "$new_fr" > "$LOG" 2>&1 || EXIT_CODE=$?
    echo "   Completed: exit $EXIT_CODE  Log: $LOG"
    if [[ $EXIT_CODE -ne 0 ]]; then
        echo "⚠️  Inline commit failed (exit $EXIT_CODE) — falling back to full enforce"
        EXIT_CODE=0
        scripts/enforce_worktree.sh "$new_fr" > "$LOG" 2>&1 || EXIT_CODE=$?
        echo "   Fallback completed: exit $EXIT_CODE  Log: $LOG"
    fi
# FR-173: Route Bug-type FRs to condemning test pipeline
elif grep -q 'Type.*Bug' "$new_fr" 2>/dev/null; then
    # ... existing bug routing unchanged
```

Cycle metrics JSON gains a `"path"` discriminator:

```json
{
  "pipeline": "chaplain-cycle",
  "inbox_item": "gh-140.md",
  "fr_generated": "FR-259",
  "verdict": "approved",
  "enforce_outcome": "success",
  "path": "inline",
  "total_seconds": 45
}
```

### 4. `scripts/inline_commit.sh` — fast-path executor

A new script (~80 lines) that:

1. **Checks working tree cleanliness** — aborts if uncommitted changes exist
2. **Validates** the FR has `Type: Micro-fix`
3. **Registers cleanup trap** — restores working tree on any failure
4. **Delegates** to the inline graph: `yamlgraph graph run .chaplain/graphs/inline/graph.yaml`
5. **Runs pre-commit hooks**: `pre-commit run --all-files` (no `--no-verify` bypass)
6. **Derives commit type** from FR `Commit-Type:` metadata field
7. **Creates a minimal PR** — branch, push, create PR with auto-merge via `gh`
8. **Falls back** to full pipeline on any failure (non-zero exit propagated to `watch.sh`)

```bash
#!/usr/bin/env bash
# scripts/inline_commit.sh — Fast-path commit for Micro-fix FRs (FR-259)
set -euo pipefail

# FR-256: Pipeline timing metrics
METRIC_DIR="tmp/pipeline-metrics"
mkdir -p "$METRIC_DIR"
T_START=$(date +%s)
STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PIPELINE_OUTCOME="failure"

FR_PATH="$1"

# Precondition: clean working tree
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "ERROR: Working tree is not clean. Cannot run inline commit."
    exit 1
fi

# Validate Type: Micro-fix
if ! grep -q 'Type.*Micro-fix' "$FR_PATH" 2>/dev/null; then
    echo "ERROR: FR is not Type: Micro-fix"
    exit 1
fi

# Cleanup trap — restore working tree on failure
INLINE_BRANCH=""
cleanup() {
    local exit_code=$?
    # FR-256: Write timing metrics JSON (best-effort)
    local t_end
    t_end=$(date +%s)
    local duration=$((t_end - T_START))
    local finished_at
    finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local ts_safe
    ts_safe=$(echo "$STARTED_AT" | tr -d ':' | tr -d '-' | sed 's/Z//')
    local fr_id
    fr_id=$(basename "$FR_PATH" .md | grep -oE 'FR-[0-9]+' || echo "unknown")
    if [[ $exit_code -eq 0 ]]; then PIPELINE_OUTCOME="success"; fi
    printf '{\n  "pipeline": "inline",\n  "fr": "%s",\n  "outcome": "%s",\n  "started_at": "%s",\n  "finished_at": "%s",\n  "duration_seconds": %d\n}\n' \
        "$fr_id" "$PIPELINE_OUTCOME" "$STARTED_AT" "$finished_at" "$duration" \
        > "$METRIC_DIR/inline-${fr_id}-${ts_safe}.json" 2>/dev/null || true
    if [[ $exit_code -ne 0 ]]; then
        echo "Cleaning up: restoring working tree..."
        git checkout -- . 2>/dev/null || true
        git clean -fd 2>/dev/null || true
        if [[ -n "$INLINE_BRANCH" ]]; then
            git checkout main 2>/dev/null || true
            git branch -D "$INLINE_BRANCH" 2>/dev/null || true
        fi
    fi
    exit $exit_code
}
trap cleanup EXIT

# Derive commit type from FR metadata
commit_type=$(grep -m1 'Commit-Type' "$FR_PATH" | sed 's/.*Commit-Type.*: *//' | tr -d '[:space:]')
if [[ -z "$commit_type" ]]; then
    commit_type="chore"  # Conservative default
fi

# Guard: fix/feat must use full pipeline (changelog-gate, diary-gate)
if [[ "$commit_type" == "fix" || "$commit_type" == "feat" ]]; then
    echo "ERROR: Commit type '$commit_type' requires full pipeline (changelog/diary gates)"
    exit 1
fi

# Derive FR identifiers
fr_basename=$(basename "$FR_PATH" .md)
fr_num=$(echo "$fr_basename" | grep -oE 'FR-[0-9]+')
fr_title=$(grep -m1 '^# Feature Request:' "$FR_PATH" | sed 's/# Feature Request: //' | sed "s/${fr_num} //" || echo "$fr_basename")

# Create branch for PR
INLINE_BRANCH="${commit_type}/inline-${fr_num,,}"
git checkout -b "$INLINE_BRANCH" main

# Delegate to inline graph
yamlgraph graph run .chaplain/graphs/inline/graph.yaml \
    --var fr_path="$FR_PATH" \
    --var date="$(date +%Y-%m-%d)" \
    --full

# Pre-commit validation (no --no-verify)
pre-commit run --all-files

# Commit with conventional commit message
mkdir -p ./tmp
printf '%s: %s %s\n' "$commit_type" "$fr_num" "$fr_title" > ./tmp/msg.txt
git add -A
git commit -F ./tmp/msg.txt

# Push and create PR with auto-merge
git push origin "$INLINE_BRANCH"
gh pr create --base main --head "$INLINE_BRANCH" \
    --title "${commit_type}: ${fr_num} ${fr_title}" \
    --body "Auto-generated by inline_commit.sh (FR-259). Fast-path micro-fix."
gh pr merge "$INLINE_BRANCH" --auto --squash
```

### 5. Inline graph specification

**Location:** `.chaplain/graphs/inline/graph.yaml`

A minimal graph that reads the FR, validates eligibility, and applies the change in the working tree. The `analyze` node uses `type: llm` with an inline schema so that the `eligible` field is promoted to top-level state for conditional edge evaluation. The `apply` node uses `type: copilot` for file editing via CLI.

```yaml
# .chaplain/graphs/inline/graph.yaml — Minimal graph for micro-fix application (FR-259)
metadata:
  name: inline-micro-fix
  description: Apply a micro-fix change described in an FR directly in the working tree
  provider: anthropic

state:
  fr_path: {type: str, description: "Path to the FR file"}
  date: {type: str, description: "Current date"}
  eligible: {type: bool, description: "Whether the change meets micro-fix criteria"}
  change_spec: {type: str, description: "Extracted change specification"}
  result: {type: str, description: "Application result summary"}

nodes:
  analyze:
    type: llm
    prompt: .chaplain/graphs/inline/prompts/analyze.yaml
    state_key: change_spec
    variables:
      fr_path: "{fr_path}"

  apply:
    type: copilot
    prompt: .chaplain/graphs/inline/prompts/apply.yaml
    state_key: result
    variables:
      change_spec: "{change_spec}"

edges:
  - from: START
    to: analyze
  - from: analyze
    to: apply
    condition: "eligible == True"
  - from: analyze
    to: END
    condition: "eligible != True"
  - from: apply
    to: END
```

**Design note (Issue 3 resolution):** The `analyze` node uses `type: llm` (not `type: copilot`) so that the inline schema's `eligible` field is promoted to top-level state via `state_builder.py`. Copilot nodes store a `CopilotResult` envelope under `state_key`, which would nest `eligible` at `state.change_spec.eligible` — inaccessible to conditional edge evaluation. The `llm` node type with inline schema auto-populates matching top-level state fields.

When `eligible != True`, the graph exits without applying changes. The `inline_commit.sh` script detects the absence of file modifications (nothing to `git add`) and exits non-zero, triggering fallback.

**Prompts:**

**`.chaplain/graphs/inline/prompts/analyze.yaml`:**
```yaml
system: |
  You are a code analyst. Read the feature request and extract a precise
  change specification. Output ONLY the structured change — no commentary.

user: |
  Read the feature request at {fr_path}.

  Extract:
  1. Target file path (must be exactly one file)
  2. The specific text to find (exact match)
  3. The replacement text
  4. A one-line summary of the change

  If the change affects more than one file or more than 10 lines,
  set eligible to false and stop.

schema:
  name: ChangeSpec
  fields:
    target_file: {type: str, description: "Path to the file to modify"}
    find_text: {type: str, description: "Exact text to find in the file"}
    replace_text: {type: str, description: "Replacement text"}
    summary: {type: str, description: "One-line summary of the change"}
    eligible: {type: bool, description: "True if change meets micro-fix criteria"}
```

**`.chaplain/graphs/inline/prompts/apply.yaml`:**
```yaml
system: |
  You are a code editor. Apply the specified change precisely.
  Do not modify anything beyond the specified change.

user: |
  Apply this change to the codebase:

  {change_spec}

  Rules:
  - Modify ONLY the specified file
  - Change ONLY the specified text
  - Do not add comments, do not reformat surrounding code
  - If the find_text is not found exactly, report failure — do not guess

  After applying, report what was changed.
```

### 6. Push/merge strategy: Minimal PR

**Decision:** Minimal PR with auto-merge.

**Justification:**
- Branch protection requires PRs for all changes to `main` — admin bypass escalation from "docs-only" to "code changes" is unjustified and violates `automation_inherits_doctrine`
- A minimal PR adds ~2 minutes (branch + push + PR creation + CI) but preserves the full CI safety net
- This aligns with FR-258's precedent: `chore` finalization PRs use the same `gh pr create` + `gh pr merge --auto --squash` pattern
- Total fast-path time: ~3-5 minutes (vs. 10-120 minutes for full enforce) — the value proposition holds

**CI gate analysis by commit type:**

| Commit Type | commitlint | test | changelog-gate | diary-gate | demo-gate |
|-------------|-----------|------|----------------|------------|-----------|
| `docs:`     | ✅ pass    | ✅ pass | ✅ skip (not feat/fix) | ✅ skip | ✅ skip |
| `chore:`    | ✅ pass    | ✅ pass | ✅ skip | ✅ skip | ✅ skip |
| `style:`    | ✅ pass    | ✅ pass | ✅ skip | ✅ skip | ✅ skip |
| `refactor:` | ✅ pass    | ✅ pass | ✅ skip | ✅ skip | ✅ skip |

### 7. Diary-gate exemption

Micro-fix PRs include `FR-XXX` in the title for traceability, but diary-gate is not triggered because it only gates `feat`/`fix` types. Since micro-fixes are restricted to `docs`/`chore`/`style`/`refactor` commit types, the diary-gate CI check passes without a diary entry.

**Justification:** Micro-fixes are trivial by definition (single file, <10 lines, no behavioral change). They generate no metacognitive insight worth recording. The cognitive overhead of reflection exceeds the value of the insight for changes with zero architectural impact.

### 8. Metrics integration (FR-256 compatible)

The `inline_commit.sh` cleanup trap emits timing JSON with `"pipeline": "inline"` discriminator:

```json
{
  "pipeline": "inline",
  "fr": "FR-259",
  "outcome": "success",
  "started_at": "2026-04-20T10:00:00Z",
  "finished_at": "2026-04-20T10:03:00Z",
  "duration_seconds": 180
}
```

### 9. Fallback on failure

If `inline_commit.sh` exits non-zero, `watch.sh` falls back to the full `enforce_worktree.sh` pipeline. The cleanup trap ensures:
1. Working tree is restored (`git checkout -- . && git clean -fd`)
2. Any created branch is deleted
3. Metrics JSON is written regardless of outcome

## Acceptance Criteria

- [ ] Plan prompt updated with micro-fix classification instruction (7 eligibility criteria including `fix`/`feat` exclusion, `Type: Micro-fix`, `Commit-Type:` field)
- [ ] `feature-requests/TEMPLATE.md` updated to include `Micro-fix` as a valid Type value
- [ ] `watch.sh` checks for `Type: Micro-fix` after Rejected check and before Bug check
- [ ] `watch.sh` falls back to `enforce_worktree.sh` if `inline_commit.sh` exits non-zero
- [ ] `watch.sh` cycle metrics JSON includes `"path": "inline"` discriminator (FR-256 compatible)
- [ ] `scripts/inline_commit.sh` checks working tree cleanliness before proceeding
- [ ] `scripts/inline_commit.sh` rejects `fix:`/`feat:` commit types
- [ ] `scripts/inline_commit.sh` creates branch, applies change via inline graph, runs pre-commit, commits, creates PR with auto-merge
- [ ] `scripts/inline_commit.sh` has a cleanup trap that restores working tree on failure
- [ ] `scripts/inline_commit.sh` cleanup trap emits `"pipeline": "inline"` timing JSON
- [ ] Commit type derived from FR `Commit-Type:` metadata field (not hardcoded)
- [ ] Fast path never uses `--no-verify` — pre-commit hooks run unconditionally
- [ ] Inline graph `analyze` node uses `type: llm` (not `copilot`) so `eligible` field is promoted to top-level state
- [ ] Eligibility guard: conditional edge routes to END when `eligible != True`
- [ ] Analyze prompt outputs structured `ChangeSpec` schema with eligibility check
- [ ] Fast path logs are written to `tmp/inline-*.log`
- [ ] Unit test for eligibility classifier logic (grep pattern matching)
- [ ] Integration test: mock Plan graph emitting `Type: Micro-fix` → verify inline path taken
- [ ] Documentation updated in `CLAUDE.md` (pipeline routing section)
- [ ] Tests added with `@pytest.mark.req` tags

## Constraints

- **No `--no-verify` bypass**: Fast path runs all pre-commit hooks. Non-negotiable per Commandment 10 and the Agents' Prayer.
- **Conservative classifier**: When in doubt, use the full path. False negatives (sending trivial changes to full path) are acceptable; false positives (sending non-trivial changes to fast path) are defects.
- **No behavioral changes via fast path**: Changes that require new tests, modify APIs, or add dependencies must always use the full pipeline.
- **No `fix:` or `feat:` via fast path**: These commit types trigger changelog-gate and diary-gate CI checks. Excluding them eliminates the `finalize_lib.sh` dependency.
- **Working tree must be clean**: The script aborts if uncommitted changes exist. Acceptable because `watch.sh` runs in an automated context with a dedicated checkout.
- **Working tree must be clean on failure**: Cleanup trap restores working tree via `git checkout -- . && git clean -fd` and deletes any created branch.
- **Single file scope**: Fast path is limited to single-file changes. Multi-file changes always use the full pipeline.
- **Analyze node must use `type: llm`**: Ensures `eligible` field is promoted to top-level state for conditional edge evaluation. `type: copilot` stores a `CopilotResult` envelope which nests schema fields.
- **Minimal PR, not admin bypass**: All fast-path changes go through a PR with CI. Branch protection is respected.

## Alternatives Considered

1. **Skip pipeline entirely for regex-matched patterns**: Too fragile — regex cannot reliably distinguish a typo fix from a behavioral change. LLM classification is more reliable.
2. **Batch micro-fixes into a single PR**: Reduces PR overhead but adds batching and partial failure complexity.
3. **Lower CI requirements for micro-fix PRs**: Would require GitHub Actions changes and label-based conditional checks. Adds platform coupling.
4. **Direct commit without validation**: Violates Commandment 10 (pre-commit hooks are the minimum safety gate). Rejected.
5. **Admin bypass push to main**: Precedent exists for docs-only commits but escalating to code changes violates `automation_inherits_doctrine`.
6. **Local-only commit deferred to human push**: Breaks the closed-loop automation goal.
7. **Include `fix:` with inline changelog generation**: Would require implementing `finalize_lib.sh` or duplicating changelog fragment logic. Excluded `fix:` from fast-path eligibility instead.

## Related

- FR-256: Pipeline Timing Metrics (metrics JSON schema — extended with `"path"` field)
- FR-258: Automate Post-Merge Finalization (shared library pattern, PR-based approach precedent)
- FR-243: Watch daemon sequential enforcement (routing logic being extended)
- FR-106: Enforce worktree script (full path — unchanged)
- FR-173: Bugfix worktree script (bug path — unchanged)
- FR-251: Author allowlist and body size cap (security gates — applied to both paths)
- `.chaplain/watch.sh:79-102` — existing routing logic
- `scripts/enforce_worktree.sh:23-32,90-106` — metrics pattern
- Diary: `2026-04-20-chaplain-as-compiler.md` — names "Inlining" as the missing compiler pass
- Diary: `2026-03-07-inquisitor-audit-v.md` — seed for fast-path concept

## Research Brief

### Competitive Landscape

No competing LLM agent framework (LangGraph, CrewAI, AutoGen, Google ADK, OpenAI Agents SDK) addresses this problem because they are *runtime* orchestration tools, not self-hosted CI/CD pipelines with automated triage. The closest analogs exist in **dependency management and code security tooling**:

| Tool | Mechanism | Analogy to FR-259 |
|------|-----------|-------------------|
| **[Renovate `automerge`](https://docs.renovatebot.com/configuration-options/#automerge)** | Classifies dependency updates by severity (`minor`, `patch`, `pin`, `digest`) and auto-merges low-risk PRs without human review. Conservative: major updates always require human intervention. | Direct analog — severity classifier routes trivial updates through a fast path with CI gates but no human review. |
| **[Dependabot auto-triage rules](https://docs.github.com/en/code-security/dependabot/dependabot-auto-triage-rules)** | Classifies security alerts by CVE/CWE/severity/scope and auto-dismisses low-impact issues (e.g., dev-only dependencies). GitHub-curated presets + custom rules. | Classification model — severity-based filtering reduces noise by routing low-impact items away from full review. |
| **[GitHub Copilot Autofix](https://docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/about-autofix-for-codeql-code-scanning)** | LLM-generated code fixes for CodeQL security alerts, presented as PR suggestions. Requires human commit. | LLM-applies-fix pattern — but Autofix is human-in-loop (developer must accept), whereas FR-259 is fully automated with pre-commit + CI as the safety net. |

**Key insight:** Renovate's automerge is the closest production precedent. It proves the pattern: classify by severity → route low-risk through lighter pipeline → require CI to pass → auto-merge. FR-259 extends this pattern to *LLM-generated code changes* rather than dependency version bumps.

**Would documenting suffice?** No. The overhead is in the pipeline execution (worktree creation, LLM enforce, post-assertions), not in developer knowledge. Documentation cannot skip a 10–120 minute LLM enforce cycle.

### Existing Abstractions

| Abstraction | File | Overlap with FR-259 |
|-------------|------|---------------------|
| Pipeline routing | `.chaplain/watch.sh:79-102` | **Direct extension point** — FR-259 inserts a new route between Rejected and Bug checks |
| Full enforce pipeline | `scripts/enforce_worktree.sh:140-210` | **What fast path skips** — worktree setup, LLM enforce graph, post-assertions |
| Judge classification | `.chaplain/graphs/copilot/prompts/judge.yaml:20-24` | **Strategic** classification (primitive/contrib/pattern/reject) exists; **severity** classification (trivial/non-trivial) does not |
| Inquisitor propose mode | `.chaplain/inquisitor.sh:90-115` | Already classifies findings as "Micro-fix (direct fix)" vs "Structural gap (FR stub)" — but routes both to full pipeline |
| Pipeline metrics (FR-256) | `scripts/enforce_worktree.sh:23-32,92-106` | **Ready to extend** — cleanup trap pattern, JSON schema, `tmp/pipeline-metrics/` directory |
| Copilot node type | `yamlgraph/node_factory/copilot_node.py:138-197` | Used for `apply` node; `CopilotResult` envelope prevents top-level state promotion |
| Conditional edge evaluation | `yamlgraph/utils/conditions.py:168-207` | Requires `eligible` at top-level state — drives the `analyze` node using `type: llm` instead of `type: copilot` |
| Finalize post-merge | `scripts/finalize_merge.sh:45-109` | **Excluded by design** — fast path avoids `fix:`/`feat:` commit types that trigger changelog/diary gates |
| FR TEMPLATE | `feature-requests/TEMPLATE.md:4` | Current: `Feature | Bug | Enhancement`; FR-259 adds `Micro-fix` |

**No duplication detected.** The fast path reuses existing infrastructure (routing, metrics, CI gates) and adds a new route + executor script. The inline graph (`.chaplain/graphs/inline/graph.yaml`) is a new, minimal 2-node graph — no overlap with the 4-node enforce graph.

### Diary Precedents

| Entry | Relevance | Key Quote |
|-------|-----------|-----------|
| `2026-04-20-chaplain-as-compiler.md` | **Primary.** Names "Inlining" as the missing compiler pass (#9 of 14). | *"Micro-fixes run through the full pipeline. This is like compiling `x = x + 0` with full optimization."* |
| `2026-04-20-chaplain.md` | **Design review.** Validates FR-259 design, identifies 3 issues: routing order, PR title contradiction, state routing ambiguity. | *"FR-259 proposes a fast-path for micro-fix PRs… Judge validated the design as fundamentally sound: clear ROI (17.5 min/fix), strong demand (36 FRs mention micro-changes)."* |
| `2026-03-07-inquisitor-audit-v.md` | **Seed.** First articulation of the fast-path concept from audit asymmetry. | *"Should the Inquisitor be granted authority to make trivial corrective commits… A read-only auditor that cannot act on micro-fixes creates an asymmetry."* |
| `2026-04-20-reflection-fr-256-pipeline-timing-metrics.md` | **Trap: `infrastructure_self_exempt`.** Pipeline that enforces instrumentation was itself uninstrumented — now fixed by FR-256, enabling FR-259 to measure its own overhead. | *"The pipeline that enforces instrumentation on user graphs was itself uninstrumented."* |
| `2026-04-19-pipeline-process-audit.md` | **Context.** Documents 18-pipeline architecture and process maturity levels. Inlining moves from Level 2 (Gated) toward Level 3 (Self-healing). | Worktree overhead documented: *"isolated git worktree, symlinked .venv, cleanup trap handles bare-repo corruption."* |
| `2026-03-12-reflection-fr-193.md` | **Trap: `automation_inherits_doctrine`.** Scripts follow same rules as humans — no `--no-verify` bypass. | FR-259 explicitly honors this: pre-commit hooks run unconditionally on fast path. |

**Recurring traps addressed by FR-259:**
- `infrastructure_self_exempt` → inline metrics ensure the fast path is instrumented
- `automation_inherits_doctrine` → pre-commit + CI run unconditionally; no `--no-verify`
- `working_system_inertia` → full pipeline "works" but wastes 17.5 min/trivial fix
- `anthropomorphic_naming` → diary reframes Plan/Judge/Enforce as compiler passes, not roles

### Usage Evidence

- **Chaplain graphs:** 3 existing (copilot, enforce, philosopher); FR-259 adds a 4th (inline)
- **Graph files across codebase:** 355 YAML graph files in `graphs/` + `examples/`
- **`enforce_worktree.sh` references:** 60 occurrences across ARCHITECTURE.md, capabilities, FRs, tests, diary
- **`watch.sh` references:** 95 occurrences — heavily integrated into architecture docs and tests
- **Feature requests processed:** 190 FRs in `feature-requests/`; majority show processing markers
- **`type: copilot` nodes:** 51 occurrences across 15 files (inline graph adds 1 more)
- **`type: llm` with inline schemas:** 269 `type: llm` references; inline schema pattern tested in `tests/unit/test_inline_schema.py`
- **`Micro-fix` or `inline_commit` references:** 0 in codebase (13 in draft only) — confirms this is net-new
- Real-world use cases beyond the proposal: Inquisitor audit findings (micro-fixes already identified but routed to full pipeline), version bumps, docstring corrections, import cleanup — all currently pay full enforce overhead

### Classification Signal

- **Abstraction level:** integration — extends existing pipeline routing infrastructure; does not add a new node type, language feature, or framework primitive
- **Recommended approach:** build — all infrastructure exists (routing, metrics, CI gates, conditional edges); the gap is a routing optimization + 80-line executor script + 2-node inline graph; documenting cannot eliminate the 10–120 min LLM enforce overhead
- **Key risk:** LLM classifier false positive routing a non-trivial change through the fast path, bypassing behavioral testing — mitigated by conservative classification (all 7 criteria must hold, `fix:`/`feat:` excluded) and fallback to full pipeline on any failure

## Judgement

**Verdict: APPROVED**

**Classification: Integration enhancement** — extends existing pipeline routing infrastructure with 3+ real use cases (Inquisitor audit micro-fixes, version bumps, docstring corrections, import cleanup). No existing abstraction routes by severity; all proposals currently pay full enforce overhead.

**Evaluation:**

1. **Scope:** Clear and minimal. Single concern — pipeline routing optimization. Components (classifier, router, executor, graph) are cohesive parts of one responsibility.

2. **Contradictions/Ambiguities:** None in the core design. Research brief FR count corrected (190 actual, not 255). The `analyze` node type decision (`llm` vs `copilot` for state promotion) is well-reasoned and correctly motivated by the conditional edge evaluation constraint.

3. **Acceptance criteria:** 19 concrete, testable criteria. Each maps to a specific code artifact or behavior. Measurable.

4. **Feasibility:** All extension points verified against the codebase:
   - `watch.sh` routing insertion point confirmed (lines 79-102)
   - Metrics cleanup trap pattern exists and is ready to extend (`enforce_worktree.sh` lines 23-32, 90-106)
   - Conditional edge evaluation (`conditions.py` lines 168-207) supports `eligible` at top-level state
   - `type: llm` with inline schema correctly promotes fields to top-level state
   - 1.5 day estimate is realistic for the scope

5. **Architecture alignment:** Extends existing patterns without duplication. Respects branch protection (`automation_inherits_doctrine`). Conservative classifier (all 7 criteria, `fix:`/`feat:` excluded) minimizes false positives. Fallback to full pipeline on failure provides a safety net.

6. **Single responsibility:** Yes. No orthogonal concerns detected — no need to split.

7. **Key strengths:**
   - Conservative by default (full path on ambiguity)
   - `fix:`/`feat:` exclusion eliminates changelog/diary gate complexity entirely
   - Fallback mechanism prevents silent failure
   - Instrumented from day one (FR-256 compatible metrics)
   - No `--no-verify` bypass — pre-commit hooks run unconditionally

**Scope frozen. Authority granted to implement.**
