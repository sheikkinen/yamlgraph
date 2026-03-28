# Feature Request: Demo Proof Gate — Require Demo Output Log Artifact

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 1–2 days (backfilling ~35 demo directories requires LLM API calls)
**Judged:** 2026-03-28
**Requested:** 2026-03-28

## Summary

Add a CI gate and pre-commit hook that require a `demo-output.log` artifact when demos are created or modified, proving the demo was actually run. Update the enforcer Phase 2 prompt to capture demo output to this log file.

## Value Statement

Maintainers gain confidence that every demo in `examples/demos/` has been executed at least once before merge, closing the gap between Commandment 2's mandate ("demonstrate with example") and actual enforcement.

## Problem

Demo creation is emphasized as mandatory by Scripture (Commandment 2) and planned by FR-096 (Demo Plan in FR template), yet **no gate verifies demos were actually run**:

1. **Enforcer Phase 2** asks Copilot to create demos "if applicable" but never verifies execution output — demo creation is advisory, not enforced.
2. **No CI gate** exists for demo proof. Compare: `diary-gate` blocks PRs without diary reflections, `changelog-gate` blocks PRs without changelog fragments — but demos have no equivalent.
3. **No pre-commit hook** checks for demo proof when demo files change.
4. **Result**: Demos ship with syntax errors, broken imports, or hallucinated YAML because no proof of execution is committed. The enforcer skips demo execution ~99% of the time.

The diary-gate (FR-158) and changelog-gate (FR-149/FR-179) prove this pattern works: require an artifact, gate on its presence, and compliance becomes automatic.

## Proposed Solution

### 1. Artifact convention

Every demo directory that contains runnable graph(s) must include a `demo-output.log` capturing the output of a successful run:

```
examples/demos/<name>/demo-output.log
```

The log is produced by running the demo and redirecting output:

```bash
yamlgraph graph run examples/demos/hello/graph.yaml \
  --var name="World" --var style="casual" --full \
  2>&1 | tee examples/demos/hello/demo-output.log
```

The log file is committed alongside the demo, serving as proof-of-execution.

### 2. CI gate: `demo-gate`

Add a `demo-gate` job to `.github/workflows/commitlint.yml` following the diary-gate pattern:

```yaml
demo-gate:
  name: Demo proof required for changed demos
  runs-on: ubuntu-latest
  if: >-
    startsWith(github.event.pull_request.title, 'feat') ||
    startsWith(github.event.pull_request.title, 'fix')
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Verify demo output logs exist
      env:
        BASE_SHA: ${{ github.event.pull_request.base.sha }}
        HEAD_SHA: ${{ github.event.pull_request.head.sha }}
      run: |
        # Find demo directories with changed files (excluding the log itself)
        CHANGED_DEMOS=$(git diff --name-only "$BASE_SHA" "$HEAD_SHA" \
          | grep -E '^examples/demos/[^/]+/' \
          | grep -vE 'demo-output\.log$' \
          | sed 's|examples/demos/\([^/]*\)/.*|\1|' \
          | sort -u)

        if [ -z "$CHANGED_DEMOS" ]; then
          echo "⏭️ No demo files changed — demo gate skipped"
          exit 0
        fi

        MISSING=0
        for DEMO in $CHANGED_DEMOS; do
          LOG="examples/demos/${DEMO}/demo-output.log"
          if git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -qF "$LOG"; then
            echo "✅ Demo proof found: $LOG"
          else
            echo "::error::Demo '$DEMO' changed but no demo-output.log in diff"
            MISSING=$((MISSING + 1))
          fi
        done

        if [ "$MISSING" -gt 0 ]; then
          echo ""
          echo "Run each changed demo and commit the output log:"
          echo "  yamlgraph graph run examples/demos/<name>/graph.yaml --full 2>&1 | tee examples/demos/<name>/demo-output.log"
          exit 1
        fi
```

Add `demo-gate` to the branch protection required status checks on `main`.

### 3. Pre-commit hook: `demo-proof-check`

Add a local hook to `.pre-commit-config.yaml`:

```yaml
- id: demo-proof-check
  name: demo-proof-check
  entry: scripts/check_demo_proof.sh
  language: script
  pass_filenames: false
  stages: [pre-commit]
```

The script checks staged files: if any `examples/demos/<name>/` files are staged (excluding the log), require `examples/demos/<name>/demo-output.log` to also be staged.

### 4. Enforcer Phase 2 update

Update `.chaplain/graphs/enforce/prompts/enforce-test-demo.yaml` to capture demo output:

```yaml
  3. **EXAMPLE** - If a demo is needed:
     - Create a minimal working example in `examples/demos/<feature>/`
     - Include: graph.yaml, prompts/ folder, README.md
     - Test the example runs: `yamlgraph graph lint <example>/graph.yaml`
     - **Run the demo and capture proof:**
       ```
       yamlgraph graph run examples/demos/<feature>/graph.yaml \
         --full 2>&1 | tee examples/demos/<feature>/demo-output.log
       ```
     - Stage the demo-output.log alongside the demo files
```

## Acceptance Criteria

- [ ] `scripts/check_demo_proof.sh` exists and detects missing demo logs for staged demo changes
- [ ] Pre-commit hook `demo-proof-check` added to `.pre-commit-config.yaml`
- [ ] CI job `demo-gate` added to `.github/workflows/commitlint.yml`
- [ ] `demo-gate` added to branch protection required status checks
- [ ] Enforcer Phase 2 prompt updated to capture demo output to `demo-output.log`
- [ ] Existing demos in `examples/demos/` backfilled with `demo-output.log` (via `demo.sh` or manual run)
- [ ] `demo-output.log` entries added to relevant `.gitignore` exclusions if needed (should NOT be ignored)
- [ ] Tests: unit test for `check_demo_proof.sh` logic (REQ-YG-XXX)
- [ ] Documentation: `CLAUDE.md` branch protection table updated with `demo-gate`

## Demo Plan

**Location**: Enhancement to existing enforcement infrastructure (no standalone demo needed — the gate itself is the artifact)
**Showcase**: Create or modify a demo without `demo-output.log` → commit blocked by pre-commit and CI
**Before/After**: Demo ships without proof of execution → Demo ships with committed execution log
**Marketing Angle**: Every demo proven to run before merge — no more broken examples

## Alternatives Considered

**Run demos in CI instead of requiring committed logs** — Run `demo.sh` in the CI pipeline to verify demos work. Rejected because: (a) demos require LLM API keys not available in CI; (b) demo output is non-deterministic, making CI flaky; (c) a committed log is a permanent artifact that documents expected behavior.

**Require logs only for new demos, not modifications** — Gate only on new `graph.yaml` files, not changes to existing demos. Rejected because modifications can break demos just as easily — proof should accompany any change.

**Store logs in `outputs/` instead of co-located** — Put logs in `outputs/demos/<name>.log` to keep demo directories clean. Rejected because co-location makes the proof discoverable alongside the demo, and `outputs/` is gitignored in many workflows.

## Related

- FR-096: Require Demo Plan in FR template (planning side — this FR adds enforcement)
- FR-158: Diary Existence CI Gate (architectural precedent for artifact gates)
- FR-149/FR-179: Changelog gate (precedent for CI-enforced fragments)
- `.chaplain/graphs/enforce/prompts/enforce-test-demo.yaml`: Enforcer Phase 2
- `.github/workflows/commitlint.yml`: CI gate definitions
- `examples/demos/demo.sh`: Existing demo runner (can be extended to generate logs)
- Commandment 2: "Demonstrate with example. Code that has not been run must not be demoed."
