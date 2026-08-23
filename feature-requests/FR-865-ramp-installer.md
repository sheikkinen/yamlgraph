# Feature Request: Ramp Installer — Generic Asset Copier with Tiers

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-23), R-1…R-6 folded
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

One command, under a minute, against a target matching the **supported
contract** (below). It writes only files that do not already exist,
prints exactly what it would do under `--dry-run`, leaves a manifest
naming every asset, action, source commit SHA and content hashes, and
can be re-run safely. It contains no judgement whatsoever — everything
requiring a decision about the target belongs to FR-866.

## Proposed Solution

### Supported target contract (R-3)

Tier 1 supports **Python repositories with `pyproject.toml`, a `tests/`
suite runnable by pytest, and ruff configured**. Any other shape is
refused with a non-zero exit and no writes. "Any path" was an
overclaim: a generic copier cannot know a target's package manager,
test command, or dependency install step.

Fixture scratch repos must cover: passing suite, missing tests,
missing ruff config — each with the documented refusal or skip.

### Curated asset source (R-1, R-2)

Assets live in **`ramp/assets/tier{1,2,3}/...`** in this repo, enumerated
file-by-file in `ramp/manifest.yaml`. **No manifest entry may be a
directory, and no entry may point at this repo's live root files**
unless the FR states why that exact file is domain-free and a source
scan proves it.

This is the revision that matters most: this repo's root
`.pre-commit-config.yaml` is **not** "basics only" — it carries
authoring proof, capability/requirement validation, radon and bandit
against `yamlgraph/`, demo proof, prior-art and FR-board gates. Copying
it byte-for-byte would install a yamlgraph-specific config while this FR
promises domain-free basics. The shipped `.pre-commit-config.yaml` is
therefore a **curated ramp file**, authored for the purpose.

Same for `.github/hooks/`: the manifest names each JSON, script and
check file individually and **excludes** `logs/`, `audit.jsonl`,
`tests/`, `__pycache__/` and any generated state. `pre-command-guard.sh`
contains graph-authoring enforcement for `examples/**/graph.yaml` and
`.chaplain/graphs/*.yaml`; that is not automatically domain-free for a
Tier-1 target and must be either curated out or declared part of the
contract.

### Manifest schema

Each entry: relative normalized `source`, relative normalized
`destination`, `tier`, executable-mode metadata where needed, and an
`overwrite` policy whose values match implemented behaviour. Validation
rejects absolute paths, `..` traversal, directory sources, missing
sources, symlinks (unless explicitly allowed), generated/cache/log
paths, and duplicate destinations.

### Tier assets

**Tier 1 (live)** — curated `.pre-commit-config.yaml` (ruff, file-size,
trailing-whitespace, end-of-file, merge-conflict, private-key,
forbidden phrases, `--no-verify` block); the enumerated Copilot guard
files; a CI workflow per R-3 below; `AGENTS.md` **stub only** — the
installer never writes doctrine content.

**Tier 2 (governed)** — adds FR/judgement/diary templates,
`scripts/judge.sh` + `scripts/review.sh` + their skill directories,
diary and changelog gates.

**Tier 3 (regulated)** — adds the registry shape (`capabilities/`
directory + schema, no entries), `scripts/req_coverage.py`, and the
`--strict` pre-commit gate.

### CI asset (R-3)

Either the workflow runs the **exact documented command path** for the
supported contract, proven by fixture tests — or it ships as a
deliberately **inert setup stub** that prints the operator steps and is
**not described as an active gate**. Note that no
`.github/workflows/tests.yml` exists in this repo today; the CI asset is
authored for the ramp, not copied.

### Overwrite and rollback (R-4)

Manifest action records: `created`, `skipped_exists`, `overwritten`.
A forced overwrite records before/after hashes and **either** a backup
path sufficient to restore **or** the action is refused. Rollback
deletes only `created` files and restores backups where the contract
provides them; deletion alone is not claimed to reverse a forced
overwrite.

### Git-root detection (R-5)

Contract chosen: **filesystem inspection only** — `<target>/.git` plus
path identity. No `git` process is run against the target, mutating or
otherwise. Documented limitation: linked worktrees (where `.git` is a
file) are refused rather than guessed. Tests cover normal repo, non-repo
directory, worktree, nested subdirectory, and self-repo refusal.

### Human-review gate (R-6)

The curated asset tree and manifest are **enforcement infrastructure**
being shipped into other repositories, and judge doctrine treats
enforcement-infrastructure changes as adversarial input. They must be
human-reviewed before first non-scratch use, with the reviewed source
commit SHA recorded in `docs/ramp-manifest.md`. This FR authorizes
adding a curated asset set and tests — **not** changing this repo's live
hooks, CI, judge/review doctrine, graph-authoring doctrine, or
detector behaviour.

### Behaviour

- `--dry-run` prints every action (`create` / `skip exists` /
  `overwrite`), writes nothing, exits 0
- default: writes only missing files
- `--force`: per the R-4 contract
- always writes `<target>/docs/ramp-manifest.md`: destinations, sources,
  actions, this repo's commit SHA, and content hashes
  (`artifact_carries_code_identity`)
- never installs hooks by executing `pre-commit install` — it prints the
  command for the operator
- refuses: non-repo path, this repo, unsupported target shape, any
  destination escaping the target root

## Acceptance Criteria

Superseded by the judgement's revised set (2026-08-23); folded verbatim.

- [ ] AC-01: FR-865 is revised to define the supported target contract, curated asset source tree, exact manifest schema, overwrite/rollback model, git-root detection contract, and human-review gate from R-1 through R-6.
- [ ] AC-02: `ramp/manifest.yaml` schema validation runs in CI/test, and every entry has relative normalized `source`, relative normalized `destination`, `tier`, executable-mode metadata where needed, and an overwrite policy whose values match the implemented behavior.
- [ ] AC-03: Manifest validation rejects absolute paths, `..` traversal, directory sources, missing source files, symlink sources unless explicitly allowed, generated/cache/log paths, and duplicate destinations.
- [ ] AC-04: Tier expansion is mechanical and monotonic: Tier 2 installs Tier 1 plus Tier 2, Tier 3 installs Tier 1 plus Tier 2 plus Tier 3; tests assert set containment from the manifest rather than hardcoded lists.
- [ ] AC-05: `--tier {1,2,3} --dry-run` each prints every action it would take from the manifest, including `create`, `skip exists`, or `overwrite` status as applicable, writes zero files, and exits 0.
- [ ] AC-06: A Tier-1 install into a scratch supported repo creates all Tier-1 destinations from curated ramp sources; installed files match those curated sources byte-for-byte except documented templated/stub fields such as the `AGENTS.md` stub.
- [ ] AC-07: A second identical run changes no file content or mtime and reports every already-present destination as skipped; exit 0.
- [ ] AC-08: A pre-existing `AGENTS.md` with sentinel content survives without `--force`; the with-`--force` behavior is tested according to the revised backup/restore/refusal contract.
- [ ] AC-09: `docs/ramp-manifest.md` records every destination, source path, action taken, source commit SHA, and source/installed hashes; a test parses it and verifies it is sufficient for the documented rollback behavior.
- [ ] AC-10: Rollback is documented and tested against a scratch repo: it deletes only files created by the installer and either restores forced-overwrite backups or refuses forced overwrite when restoration is not supported.
- [ ] AC-11: The installer refuses a non-repo path, this repository, an unsupported target shape, and any target path that would escape the repo root; each refusal exits non-zero and writes nothing.
- [ ] AC-12: Source scans assert the installer and curated assets contain no LLM call, no network call, no target-repo mutating `git` command, no secret material, no hook logs, no pycache, and no unresolved yamlgraph-only assumptions outside the explicitly reviewed contract.
- [ ] AC-13: If a CI workflow is installed, fixture tests prove the exact supported target suite command and ruff command run as documented; otherwise the workflow is an explicit setup stub and is not described as an active gate.
- [ ] AC-14: The manifest and curated enforcement assets are human-reviewed before first non-scratch use; the FR records the reviewed source commit SHA and any approved deviations.
- [ ] AC-15: Tests are added before implementation for the installer behavior above, with RED/GREEN evidence recorded in the FR.

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
