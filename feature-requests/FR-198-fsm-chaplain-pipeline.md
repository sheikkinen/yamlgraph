# Feature Request: FR-198 Port Chaplain Pipeline to statemachine-engine

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Blocked (awaiting FR-196 merge)
**Effort:** 1 day
**Requested:** 2026-03-13
**Depends On:** FR-196 (Portable Chaplain) — must be merged first

## Judge Verdict: APPROVED (post-AMEND)

**Date:** 2026-03-13
**Verdict:** APPROVED — Three issues corrected; scope frozen. Authority granted to implement once FR-196 lands on `main`.

### Evaluation

| Criterion | Assessment |
|-----------|-----------|
| Scope clear and minimal? | ✅ Yes — one copy operation + one dependency addition + three lint checks |
| Contradictions or ambiguities? | ✅ None remaining after amendment |
| Acceptance criteria measurable? | ✅ Yes — all verifiable by grep/lint/process-log |
| Implementation approach feasible? | ✅ Yes — cp -r + requirements-dev.txt edit |
| Aligned with architecture? | ✅ Yes — extends portability contract defined in FR-196 |
| Single responsibility? | ✅ Yes — installs the portable Chaplain into one target project |

### Amendments Applied (in-place, 2026-03-13)

1. **Smoke-test step made concrete**: drop a file, start `watch.sh`, assert filename appears in log within 10 s, kill. No conditional `--dry-run`.
2. **AC added for smoke-test**: detection-within-10-seconds criterion now has a corresponding checkbox.
3. **Vacuous AC removed**: "No yamlgraph tests broken" dropped — this FR makes no changes to yamlgraph source; the criterion could never surface a real defect.

---

## Summary

Once FR-196 relocates the Chaplain subsystem into a self-contained `.chaplain/` directory in yamlgraph, copy that directory wholesale into the `statemachine-engine` project, add `yamlgraph` as a dev dependency, verify all three graphs pass `yamlgraph graph lint`, and update `.gitignore` to exclude Chaplain log and inbox/drafts artifacts.

## Value Statement

statemachine-engine developers get the same Plan → Judge → Enforce automation loop that yamlgraph developers use, with zero bespoke infrastructure: one copy operation and one dependency addition.

## Problem

The Chaplain pipeline (watch.sh, Plan/Judge/Enforce graphs, philosopher.sh, inquisitor.sh) lives only in yamlgraph. The `statemachine-engine` project (`fsm/`) has no automated feature-request workflow, no diary reflection gate, and no doctrine-enforcement daemon. Manually maintaining a parallel implementation would create drift; the correct fix is to make the portable version (FR-196) the canonical source and install it everywhere that needs it.

Because FR-196 has not yet merged, this task cannot start. FR-198 is blocked until FR-196's squash-merge lands on `main`.

## Proposed Solution

After FR-196 merges and `.chaplain/` in yamlgraph is fully self-contained:

### Step 1: Copy the directory

```bash
cp -r .chaplain/ /path/to/statemachine-engine/.chaplain/
```

Copies graphs, lib, shell scripts, id-registry.yaml, inbox/, and drafts/ wholesale.

### Step 2: Add dev dependency

Append `yamlgraph` (pinned to the version that shipped FR-196) to
`statemachine-engine/requirements-dev.txt`:

```
yamlgraph>=<fr196-version>
```

### Step 3: Verify graphs lint

Run `yamlgraph graph lint` on each of the three Chaplain graphs from within the
`statemachine-engine` working directory:

```bash
yamlgraph graph lint .chaplain/graphs/copilot/graph.yaml
yamlgraph graph lint .chaplain/graphs/enforce/graph.yaml
yamlgraph graph lint .chaplain/graphs/philosopher/graph.yaml
```

All three must exit 0.

### Step 4: Update `.gitignore`

Add the following patterns to `statemachine-engine/.gitignore`:

```
# Chaplain runtime artefacts
.chaplain/logs/
.chaplain/inquisitor.log
.chaplain/inbox/
.chaplain/drafts/
```

### Step 5: Smoke-test

1. Drop a one-line `.md` file into `.chaplain/inbox/`.
2. Start `watch.sh` in the background, redirecting output to a log file.
3. `grep` the log file for the filename within 10 seconds.
4. Kill the process.

The log message must contain the filename. Manual interrupt after confirmed detection is sufficient.

## Acceptance Criteria

- [ ] `.chaplain/` directory exists at the root of `statemachine-engine` with identical structure to the yamlgraph version post-FR-196 merge.
- [ ] `yamlgraph graph lint .chaplain/graphs/copilot/graph.yaml` exits 0.
- [ ] `yamlgraph graph lint .chaplain/graphs/enforce/graph.yaml` exits 0.
- [ ] `yamlgraph graph lint .chaplain/graphs/philosopher/graph.yaml` exits 0.
- [ ] `yamlgraph` appears in `statemachine-engine/requirements-dev.txt` pinned to a version ≥ the FR-196 release.
- [ ] `statemachine-engine/.gitignore` excludes `.chaplain/logs/`, `.chaplain/inquisitor.log`, `.chaplain/inbox/`, and `.chaplain/drafts/`.
- [ ] `git status` in `statemachine-engine` shows no untracked Chaplain runtime files after a `watch.sh` run.
- [ ] `watch.sh` detects a test `.md` file dropped in `.chaplain/inbox/` and logs the filename within 10 seconds of the file appearing (verified via `grep` of the process log before interrupt).

## Alternatives Considered

- **Maintain a parallel bespoke implementation**: rejected — two implementations diverge immediately; FR-196 exists precisely to prevent this.
- **Git subtree / submodule for `.chaplain/`**: adds VCS complexity for a directory that is already a simple file copy; the cost outweighs the benefit at current scale.
- **Wait for a formal plugin mechanism**: no such mechanism is planned; YAGNI.

## Related

- FR-196: Portable Chaplain (dependency — must land first)
- FR-186: fsm pre-commit quality gates (sibling proposal for statemachine-engine)
- `.chaplain/watch.sh`, `.chaplain/philosopher.sh`, `.chaplain/inquisitor.sh`
- `statemachine-engine/pyproject.toml`, `statemachine-engine/requirements-dev.txt`
