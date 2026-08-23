# Feature Request: Ramp Installer — Generic Asset Copier with Tiers

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-23
**Parent:** FR-864 (SPLIT) — child A per R-1
**First consumer / first event:** the operator, at the next ramp. The
first event is `scripts/ramp.sh /tmp/scratch-repo --tier 1 --dry-run`
in this repo's own test suite; the first real target is FR-867's.

**Prior art:** **FR-207** (`scripture-dev`) is the superseded mechanism
and the reason this FR exists: a template repo with `render.sh`
placeholder substitution, frozen 2026-03-29 at 16 hooks while this repo
reached 45, its own config left reading `project_name: my-minesweeper`,
zero contributions back. This FR keeps its *goal* and inverts its
*mechanism* — ship from the repo that runs the assets daily. **FR-748**
(`fr_atlas`) is non-overlapping here: it is a corpus-map graph, and this
FR contains no LLM step (its territory is FR-866's). **FR-826/862/863**
are target-repo history and non-overlapping with a generic installer.
No REJECTED prior art occupies this territory.

## Summary

`scripts/ramp.sh <target-repo-path> --tier {1|2|3}` — a mechanical,
idempotent, reversible installer that copies this repo's domain-free
governance assets into a target repo and records a manifest. No LLM, no
target-specific content, no repo it does not own.

## Value Statement

A repo that has gone live acquires its gates in minutes rather than
never, from a source that cannot go stale because it runs the same
assets on every commit.

## Problem

Assets that could be copied cold are not, because copying them by hand
is a 30-file chore nobody performs at the moment it is needed — the
moment a repo goes live, when the operator wants to be doing something
else. `deviant-daily` ran four days unattended with an empty
`.git/hooks/` and no CI running its 14 test files.

The previous attempt failed on distribution, not on intent: a template
repo is a photograph of a practice, and it decayed from the render
forward.

## Ideal Result

One command, under a minute, against any path. It writes only files
that do not already exist, prints exactly what it would do under
`--dry-run`, leaves a manifest naming every asset and the source commit
SHA, and can be re-run safely. It contains no judgement whatsoever —
everything requiring a decision about the target belongs to FR-866.

## Proposed Solution

### Asset manifest (source of truth: `ramp/manifest.yaml` in this repo)

Each entry: source path, destination path, tier, and `overwrite: never`.

**Tier 1 (live)**
- `.pre-commit-config.yaml` — basics only: ruff, file-size,
  trailing-whitespace, end-of-file, merge-conflict, private-key,
  forbidden phrases, `--no-verify` block
- `.github/hooks/` — the Copilot guard set (`pre-command-guard.sh`,
  `post-edit-checks`, config JSON). Domain-free: it fired twice on
  2026-08-23 from a foreign cwd.
- `.github/workflows/tests.yml` — runs the target's suite + ruff
- `AGENTS.md` — **stub only**, naming the three rules and pointing at
  FR-866 for tailoring. The installer must never write doctrine content.

**Tier 2 (governed)** — adds FR/judgement/diary templates,
`scripts/judge.sh` + `scripts/review.sh` + their skill directories,
diary and changelog gates.

**Tier 3 (regulated)** — adds the registry shape (`capabilities/`
directory + schema, no entries), `scripts/req_coverage.py`, and the
`--strict` pre-commit gate.

### Behaviour

- `--dry-run` prints the full plan, writes nothing, exits 0
- default: writes only missing files; existing files are reported as
  `skipped (exists)`
- `--force` overwrites, and only with an explicit flag
- always writes `<target>/docs/ramp-manifest.md`: asset list, source
  paths, **this repo's commit SHA** (`artifact_carries_code_identity`)
- never runs `git` in the target, never installs hooks by executing
  `pre-commit install` — it prints the command for the operator
- refuses to run if `<target>` is not a git repo root, or is this repo

## Acceptance Criteria

Exhaustive for this surface alone (parent judgement R-5); no criterion
depends on FR-866/867/868.

- [ ] AC-01: `--tier {1,2,3} --dry-run` each print a plan listing every
      manifest asset for that tier and write zero files; exit 0.
- [ ] AC-02: after `--tier 1` on a scratch repo, all Tier-1 asset paths
      exist and match their sources byte-for-byte (except `AGENTS.md`,
      asserted to be the stub).
- [ ] AC-03: Tier 2 installs everything in Tier 1 plus its own; Tier 3
      plus Tier 2's — asserted as set containment, not a hardcoded list.
- [ ] AC-04: a second identical run changes no file mtime and reports
      every asset as `skipped (exists)`; exit 0.
- [ ] AC-05: a pre-existing `AGENTS.md` with sentinel content survives a
      run without `--force`, and is replaced with it.
- [ ] AC-06: `docs/ramp-manifest.md` contains every installed
      destination path and this repo's commit SHA; a test parses it.
- [ ] AC-07: running against a non-repo path, or against this repo,
      exits non-zero with a message and writes nothing.
- [ ] AC-08: the installer contains no LLM call, no network call, and no
      `git` invocation in the target — asserted by a source scan.
- [ ] AC-09: `ramp/manifest.yaml` is schema-validated in CI; every
      declared source path exists in this repo.
- [ ] AC-10: rollback is documented and tested: the manifest is
      sufficient to delete exactly what was installed.
- [ ] AC-11: tests added before implementation (RED/GREEN commits).

## Risks

**The manifest drifts from reality.** An asset renamed here silently
breaks the installer. AC-09 makes it a CI failure.

**Tier 1 is still too heavy.** If a target rejects it, the tier
boundaries are wrong, not the installer. Recorded as a follow-up
question rather than pre-solved.

**`AGENTS.md` stub tempts content.** The single hardest boundary to
hold: writing doctrine here would resurrect the template mechanism that
FR-207 proved decays. AC-02 asserts the stub.

## Alternatives Considered

- **`pre-commit` remote hook repo with `rev:` pinning.** The correct
  long-term distribution refinement for the pre-commit subset only; it
  cannot carry `.github/hooks/`, skills, templates or CI. Deferred.
- **Cookiecutter / template repo.** Rejected — FR-207 is the experiment
  and its result is on record.
- **Install via a graph.** Rejected: copying files is mechanical, and a
  graph here would be `framework_costume`.

## Related

- `feature-requests/FR-864-ramp-spike-to-governed.md` (parent, SPLIT) and its judgement
- `feature-requests/FR-207-standalone-scripture-methodology-repo.md` — superseded mechanism
- `docs/diary/diary-2026-08-23-process-transfers-by-practice.md` — why the source must consume what it ships
