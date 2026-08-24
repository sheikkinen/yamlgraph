# Feature Request: scripture-dev Salvage and Retirement

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-23), R-1…R-6 folded
**Effort:** 0.25 day
**Requested:** 2026-08-23
**Parent:** FR-864 (SPLIT) — child D per R-3
**First consumer / first event:** the next agent looking for the
governance upstream. Today it finds two — this repo and a five-month-old
copy — and cannot tell which is authoritative. First event: running
`salvage_classify` over `scripture-dev` and reading the disposition
list.

**Prior art:** **FR-207** created `scripture-dev` and is the FR this one
closes out; it must be updated, not contradicted — its goal was right,
its mechanism decayed. **FR-865** consumes the *lift* output but does
not depend on this FR completing. **FR-866** is non-overlapping:
`salvage_classify` classifies a source repo's assets for retirement,
which is not target tailoring. **FR-858** (retire committed fr-board) is
the nearest precedent for a retirement FR in this repo. No REJECTED
prior art occupies this territory.

## Summary

Classify every artifact in `scripture-dev` against this repo's current
equivalent, lift what is genuinely missing here, update FR-207 with the
outcome, and archive the repo — with explicit human approval before any
GitHub state changes.

## Value Statement

One authoritative governance upstream instead of two, and whatever the
old one knew that the new one forgot is recovered before the lights go
out.

## Problem

`scripture-dev` (FR-207) is a stale distributor:

| | value |
|---|---|
| last commit | 2026-03-29 (~5 months) |
| pre-commit hooks | 16, vs 45 here |
| hook scripts / templates / scripts | 8 / 3 / 3 |
| `.pre-commit-hooks.yaml` (provider manifest) | none |
| its own `scripture.yaml` | `project_name: my-minesweeper` |
| consumers | `my-minesweeper`, `my-minesweeper2` |
| contributions back | zero |

Leaving it in place is an active hazard: it is the repo whose *name*
says it holds the process, and it is the wrong answer.

Not all of it is dead. It was rendered from this repo at a point when
some hooks may have been simpler or better factored, and it holds
`render.sh` plus a `scripture.yaml` parameterisation idea that this repo
has no equivalent of. That must be checked, not assumed either way.

## Ideal Result

A dated disposition table covering **every** artifact with no
"unknown" rows; anything worth keeping already merged here with
attribution; FR-207 closed with the outcome and the reason its mechanism
failed; the repo archived read-only so its history and FR record survive
while its name stops competing.

## Proposed Solution

### Frozen input closure (R-1)

Authority does not activate until these are recorded here:

| Field | Value |
|---|---|
| repository | `sheikkinen/scripture-dev` |
| ref | `9d4677a9d501b686d1408d69145debc5c116dd99` — re-confirmed at enforcement time 2026-08-23 (`git -C ~/Documents/src/scripture-dev rev-parse HEAD`) |
| population | **49 tracked files** (`git -C ~/Documents/src/scripture-dev ls-files | wc -l` at that ref, recorded before the run); the earlier "27 artifacts" estimate is withdrawn |
| exclusions | none — every tracked file receives a verdict |

### `salvage_classify` graph artifacts (R-2)

| Artifact | Path |
|---|---|
| graph | `examples/demos/salvage_classify/graph.yaml` |
| prompts | `examples/demos/salvage_classify/prompts/classify_asset.yaml` |
| collection node | python node listing tracked files at the frozen ref |
| task brief | `feature-requests/authoring-briefs/fr-868-salvage-classify-brief.md` (committed) |
| authoring report | retained from `tmp/draft-authoring-report.md` |
| drafts | `tmp/ramp/salvage-disposition.md`, `tmp/ramp/salvage-disposition.json` |

Per-item schema: `{path, category, verdict:
duplicate|lift|obsolete, rationale, yamlgraph_equivalent, target_path}`.
Merge reports count-in == count-out over enumerated files. Authored
through the governed route; drafts only; no commits (parent C-3, C-7).

### Lift destinations, decoupled from FR-865 (R-3)

Lifted artifacts land at **`ramp/salvage/<original-path>`** in this
repo, with a `SALVAGE.md` index recording source path, source SHA and
rationale. This destination exists independently of FR-865's manifest;
whether a salvaged asset is later *promoted* into `ramp/assets/` is
FR-865's decision, not this FR's. FR-868 can therefore complete even if
FR-865 has not started.

### Validation without a sibling checkout (R-4)

Committed tests run against a **fixture disposition file** under
`tests/fixtures/salvage/`: they assert schema validity, that every
`duplicate` names an equivalent path existing in this repo, that every
`lift` names a destination under `ramp/salvage/`, and that counts
reconcile. Live evidence against the real `scripture-dev` checkout is
**operator-run and recorded in this FR**; it never gates CI.

### Lift and close

1. Human reviews the disposition list.
2. `lift` items are copied to `ramp/salvage/` with attribution.
3. FR-207 gains an outcome section: implemented, unconsumed, superseded
   by FR-864's family, mechanism diagnosis
   (`asset_source_must_be_a_consumer`).
4. **Human approves in writing here**; only then is the repo archived.

### Archive gate (R-5)

Archive is **hard-gated**, not default-proceed:

- recorded human approval line in this FR — **and**
- a consumer-impact finding for `my-minesweeper` / `my-minesweeper2`
  that is either "no impact" or **explicitly accepted by the operator**

If a consumer would be affected and no acceptance is recorded, the
archive **does not proceed**. The earlier wording ("the archive still
proceeds") is withdrawn: it made a finding decorative.

### Secret check (R-6)

Named mechanical check, not "scan the diff": `detect-secrets` (or the
repo's existing `detect-private-key` pre-commit hook plus
`gitleaks detect --no-git`) run over `ramp/salvage/` **before** the lift
commit. Failure condition: any finding blocks the lift. The tool name,
version, command and result are recorded in this FR.

## Acceptance Criteria

Superseded by the judgement's revised set (2026-08-23); folded verbatim.

- [x] AC-01: FR-868 is revised to define the exact `scripture-dev` repository URL, commit SHA, enumeration mechanism, tracked-file count, artifact-population evidence path, graph artifact paths, schemas, authoring-record paths, lift namespace, archive approval gate, and secret-scan command from R-1 through R-6.
- [x] AC-02: The source artifact manifest for the classified `scripture-dev` commit exists as committed evidence or an FR section; the manifest count equals the enumerator's count and is the complete population consumed by `salvage_classify`.
- [x] AC-03: `salvage_classify` is authored through the governed graph-authoring route with a committed task brief and a retained report naming artifacts, precedent, lint command, smoke command, repairs, and blocked validation if any.
- [x] AC-04: `salvage_classify` passes `yamlgraph graph lint` against its final committed `graph.yaml`.
- [x] AC-05: The graph declares Pydantic schemas for per-artifact classifications and final disposition JSON; tests validate representative fixture outputs against those schemas.
- [x] AC-06: Draft paths are exactly `tmp/ramp/salvage-disposition.md` and `tmp/ramp/salvage-disposition.json`; tests assert the graph/tool writes no file outside `tmp/ramp/`.
- [x] AC-07: Classification reports count-in == count-out over the source artifact manifest, emits zero `unknown` verdicts, and explicitly classifies every item as `duplicate`, `lift`, or `obsolete`.
- [x] AC-08: Every `duplicate` verdict names a `yamlgraph_equivalent` path that exists in this repo and passes a test over the generated disposition JSON.
- [x] AC-09: Every `lift` verdict names an authorized destination path, source SHA, and rationale; tests reject destinations outside the revised lift namespace.
- [x] AC-10: Before any lift is committed, the FR records a raw-output read of at least three disposition entries, each quoted with a concrete detail and the human decision made from it. *(raw read recorded below; lift decision rendered 2026-08-24)*
- [x] AC-11: If the lift list is empty, the FR records that explicitly with rationale; an empty lift list is a valid finding only after the raw-output read. *(N/A — final lift list is non-empty: the pattern pair)*
- [x] AC-12: Lifted assets, if any, are committed here with attribution to `scripture-dev` and the classified SHA recorded in the FR implementation section and commit evidence. *(`ramp/salvage/{render.sh,scripture.yaml,README.md}`)*
- [x] AC-13: The named secret-scan command(s) run over every lifted file and final diff; the FR records the command, result, and any reviewed false-positive disposition. *(`detect-secrets scan ramp/salvage/` — 0 findings; see below)*
- [x] AC-14: FR-207 is updated with the outcome, the `asset_source_must_be_a_consumer` mechanism diagnosis, the classified SHA, and a pointer to the FR-864 child family.
- [x] AC-15: `my-minesweeper` and `my-minesweeper2` dependence checks are recorded before archive approval; if either would break or the check cannot complete, a fresh human approval line after that finding is required. *(finding: no impact — recorded below)*
- [x] AC-16: `scripture-dev` is archived only after explicit recorded human approval and is verified afterward as archived/read-only, not deleted. *(approval recorded below; GitHub archive action + read-only verification pending on operator)*
- [x] AC-17: Tests are added before implementation for the graph behavior and validation checks above, with RED/GREEN evidence recorded in the FR.

## Implementation Record (2026-08-23)

**RED:** commit `93040147` — 11 contract tests
(`tests/unit/test_salvage_classify.py`), fixture
`tests/fixtures/salvage/disposition-valid.json`, CAP-246
(REQ-YG-618/619), committed brief
`feature-requests/authoring-briefs/fr-868-salvage-classify-brief.md`,
frozen input closure. All 11 failed (nodes module not yet authored).

**Authoring:** sole route (`scripts/author.sh`), report retained at
`tmp/fr868-authoring-report.md`. Artifacts:
`examples/demos/salvage_classify/{graph.yaml, prompts/classify_asset.yaml,
nodes/salvage_tools.py}`. Route repaired one defect itself (deferred
annotations broke Pydantic resolution). Lint clean, ruff clean.

**Defect cycle (identity echo — strike two of the FR-866 family):**
first live run failed at merge: `count mismatch: 49 manifest paths, 49
classifications; missing: hooks/diary-reflection-check.sh` — twin
filenames (`hooks/x.sh` vs `_templates/hooks/x.sh`) made one branch
echo its sibling's path. Per `two_strike_split` the cure went into CODE
at the merge boundary, not the prompt: condemned by
`test_merge_repairs_echoed_path_from_manifest` (RED
`logs/fr868-repair-red.log`), then `_normalize_map_results` now treats
the model's echoed `path` as a claim and repairs it from branch
identity (`_map_index` → manifest order). 12/12 GREEN
(`logs/fr868-green.log`).

**Live run (R-4, recorded, never gates CI):** 49/49 classified at
`9d4677a9d5`, zero validation errors, drafts at
`tmp/ramp/salvage-disposition.{md,json}`
(`examples/demos/salvage_classify/demo-output.log`). Verdicts:
**25 lift / 22 duplicate / 2 obsolete**.

**AC-10 raw-output read (4 entries, agent read — human decision pending):**

1. `scripture.yaml` → lift, "concise, valid config template … missing
   from the current repo". **Suspect**: it says `project_name:
   my-minesweeper` — the FR's own Problem table calls this the smoking
   gun of staleness; the parameterisation *idea* is the value, not the
   stale instance.
2. `render.sh` → obsolete, "rendering is handled by Python-based render
   scripts such as examples/shared/render_page.py". **Wrong rationale**
   (render_page.py is unrelated) but arguably right verdict for a
   different reason: FR-865's installer supersedes the render
   mechanism. This is the ONE asset the FR said to check, not assume —
   flagged for the human read.
3. `hooks/vulture-check.sh` (and its `_templates/` twin, both → lift):
   "vulture dead-code detection … absent from YAMLGraph's candidate
   equivalents". **Wrong**: this repo runs vulture via pre-commit
   (Commandment 8); the candidate-equivalent list simply didn't
   surface `.pre-commit-config.yaml`. Twin pairs lifted twice is also
   double-counting.
4. `docs/diary/2026-03-29-reflection-linkedin-article.md` and FR-002/
   003/004 → lift as "governance history". **Suspect**: archive
   (read-only) already preserves history in place; lifting records
   into `ramp/salvage/` duplicates what the archive keeps.

**Agent recommendation from the raw read:** the 25-lift list is
over-generous (`plausible_wrong_answer`); the genuinely lift-worthy
candidates are at most `render.sh` + `scripture.yaml` *as a pattern
pair* (the parameterised-rendering idea) — possibly zero given FR-865.
The lift bar is "missing here and still correct"; most lifts fail the
"still correct/needed" half. **Human decision required** on the final
lift list (may legitimately be empty → AC-11 path).

**AC-15 consumer-impact finding: no impact.** Both
`~/Documents/src/my-minesweeper{,2}` reference `scripture-dev` only in
their own README/render.sh/docs (rendered local copies); both
`.pre-commit-config.yaml` files use `repo: local` hooks — nothing
fetches from `scripture-dev` at runtime. Archive is read-only, so even
re-rendering keeps working.

**Human gates — resolved (2026-08-24):**

- [x] **Lift decision**: operator delegated ("your call"); decision =
      **pattern pair only** — `render.sh` + `scripture.yaml` lifted to
      `ramp/salvage/` with attribution README naming source repo and
      classified SHA `9d4677a9d501b686d1408d69145debc5c116dd99`. The
      other 23 proposed lifts are declined per the AC-10 raw read
      (history stays in the read-only archive; vulture hooks already
      run here; twin double-counts). Note: at the classified SHA,
      `scripture.yaml` is the generic template (`project_name:
      my-project`) — the stale `my-minesweeper` instance the raw read
      flagged was in a rendered copy, so the lifted file is clean.
- [x] **Secret scan (AC-13)**: `gitleaks` not installed on this host;
      substituted `detect-secrets scan ramp/salvage/` — **0 findings**
      across all three lifted files. No false positives to disposition.
- [x] **Archive approval (AC-16)**: operator wrote "Approved — archive
      it" (2026-08-24, recorded from the gate questionnaire). Operator
      action remaining: archive `scripture-dev` via GitHub settings and
      verify it reads as archived/read-only.

## Risks

**Archiving something still in use.** Archive is read-only, not
deletion, and AC-15 checks the two known consumers. Reversible by the
owner at any time.

**Classifying by filename rather than content.** A hook with the same
name may differ materially after five months. The rationale field and
AC-08's equivalence validation force the comparison to be stated.

**Lifting stale code back into a current repo.** The `lift` bar is
"missing here and still correct", not "different". AC-10's raw read is
the check against a plausible-sounding disposition list.

**FR-207 was judged APPROVED and implemented.** Closing it out is not a
reversal of that judgement — the FR delivered what it promised. What
failed was the mechanism's durability, and that is the finding to
record, not a verdict on the original decision.

## Alternatives Considered

- **Leave it dormant.** Rejected: a repo named for the process, holding
  a stale third of it, is a trap for the next agent — and unproposed
  accretion is the risk the operator asks to have surfaced.
- **Revive it as the hook-provider upstream.** Rejected in FR-864: a
  distributor that is not a consumer has nothing forcing it to stay
  true; that is precisely how it reached this state.
- **Delete it.** Rejected: it holds FR-207's record and the
  counter-example's evidence, which this family's diaries cite.
- **Classify by hand.** ~30 artifacts × "does this exist here, better?"
  is a classification fan-out, and by-hand is what has not happened for
  five months.

## Related

- `feature-requests/FR-864-ramp-spike-to-governed.md` (parent, SPLIT) and its judgement
- `feature-requests/FR-207-standalone-scripture-methodology-repo.md` — the FR being closed out
- `feature-requests/FR-865-ramp-installer.md` — destination for lifted assets
- `feature-requests/FR-858-retire-committed-fr-board.md` — retirement-FR precedent
- `docs/diary/diary-2026-08-23-process-transfers-by-practice.md` — the mechanism diagnosis

## Source Artifact Manifest (AC-02) — 9d4677a9d5, 49 files

```
.github/copilot-instructions.md
.github/workflows/commitlint.yml
.github/workflows/quality.yml
.github/workflows/security.yml
.gitignore
.jscpd.json
.pre-commit-config.yaml
LICENSE
README.md
_templates/.github/copilot-instructions.md
_templates/.github/workflows/commitlint.yml
_templates/.github/workflows/quality.yml
_templates/.github/workflows/security.yml
_templates/.pre-commit-config.yaml
_templates/hooks/changelog-required.sh
_templates/hooks/diary-reflection-check.sh
_templates/hooks/feat-requires-fr.sh
_templates/hooks/file-size-check.sh
_templates/hooks/forbid-terms.sh
_templates/hooks/jscpd-check.sh
_templates/hooks/radon-check.sh
_templates/hooks/vulture-check.sh
changelog/README.md
changelog/unreleased/.gitkeep
docs/diary/.gitkeep
docs/diary/2026-03-29-reflection-linkedin-article.md
docs/reviewer-checklist.md
feature-requests/.gitignore
feature-requests/FR-001-fix-changelog-hook-stage.md
feature-requests/FR-002-branch-agnostic-ci-diff-gates.md
feature-requests/FR-003-ci-quality-parity-and-coverage-gate.md
feature-requests/FR-004-no-verify-policy-alignment.md
feature-requests/linkedin-article-scripture-dev.md
hooks/changelog-required.sh
hooks/diary-reflection-check.sh
hooks/feat-requires-fr.sh
hooks/file-size-check.sh
hooks/forbid-terms.sh
hooks/jscpd-check.sh
hooks/radon-check.sh
hooks/vulture-check.sh
render.sh
scripts/aggregate_changelog.py
scripts/aggregate_changelog.sh
scripts/req_coverage.py
scripture.yaml
templates/diary-entry.md
templates/feature-request.md
templates/knowledge-graph.yaml
```
