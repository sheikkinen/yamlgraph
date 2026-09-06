# Feature Request: Subtree-split `.chaplain/` to a source-only archive and remove the runtime (Phase 2 of FR-1010)

**Priority:** MEDIUM
**Type:** Enhancement (subtraction; destructive — human gates C-4)
**Status:** Step 0 (census) enforced 2026-09-06 on `chore/fr1012-chaplain-census`; **reconciled with 0 unresolved rows** (41 test delete / 24 CAP retire / 50 keep; 21 resolutions confirmed by the operator, 1 by delegated delete review). Next gates before any RED or deletion: named-human raw read (AC-06), pre-remote human review (AC-11, C-5). Judged — APPROVED WITH REVISIONS (2026-09-06, two rounds). Round 1
R-1..R-9 and round 2 R-1..R-7 folded below; see
[FR-1012-chaplain-subtree-archive-and-removal.judgement.md](FR-1012-chaplain-subtree-archive-and-removal.judgement.md)
(round 2 appended). Authority activates only after the round-2 draft is
human-reviewed (reference + date recorded in § Implementation Record) and
no field of § Prerequisite gate is blank.
**Effort:** 2 days (census 0.5, removal 1, verification 0.5)
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 2 of 5; prerequisites FR-1014, FR-1011, FR-1015 must be **merged** and recorded in § Prerequisite gate before any Phase 2 operation (FR-1010 C-3, C-5). State at last edit (2026-09-06): FR-1014 merged (`fec26941`), FR-1011 merged (`84baceb7`), FR-1015 judged, unenforced.
**First consumer / first event:** `scripts/vscode/now.py` and the next
session briefing, at the first session start after merge — `.chaplain/`
no longer appears in any orientation surface, and `req_coverage --strict`
reports a registry without ~27 CAPs describing a runtime nobody runs.
Second: whoever runs `git tag --list chaplain-archive` a year from now.
**Research:** [FR-1010 § Alternatives Considered](FR-1010-chaplain-archival-plan.md#alternatives-considered-r-1-six-solution-classes)
(six classes; §3 source-only subtree archive selected) and
`reference/patterns/corpus-map-reduce.md` (the census contract).
`is_this_a_graph`: **yes** for the disposition census (`for each test
file / CAP, ask the model`); **no** for the split, tag, rm, and CAP status
edits, which are deterministic.
**Prior art:**
- [FR-276-retire-old-pipeline-scripts.md](FR-276-retire-old-pipeline-scripts.md),
  [FR-317-retire-obsolete-watcher2-components.md](FR-317-retire-obsolete-watcher2-components.md)
  — partial retirements inside `.chaplain/`; both required path/doc/CAP/test
  reconciliation in the same change. Same discipline, whole directory.
- [FR-465-watcher2-test-cleanup.md](FR-465-watcher2-test-cleanup.md),
  [FR-466-cap-retirement-support.md](FR-466-cap-retirement-support.md)
  — `status: retired` on CAP files; `req_coverage.py` excludes retired
  CAPs; dead tests deleted in the same commit as the CAP transition so
  FR-701's gate (live mark on retired REQ) never fires between commits.
- [FR-701-capability-registry-consistency-gate.md](FR-701-capability-registry-consistency-gate.md)
  — the gate this FR must satisfy at every commit; **not modified** (C-7).
- [FR-851](FR-851-requirement-witness-audit.md) / `examples/demos/req_witness_audit`
  — deterministic constructor → haiku-tier map → deterministic reducer with
  boundary reconciliation; raw results persisted before reduction. The
  *shape* precedent.
- [FR-892-corpus-census-pipeline-injected-adapters.md](FR-892-corpus-census-pipeline-injected-adapters.md)
  / `examples/demos/corpus_census/graph.yaml` — the **shipped census
  skeleton** with injected discover/extract adapters
  (`examples/demos/corpus_census/adapters/*.tool.yaml`). This FR binds
  Chaplain-specific manifests and adapters to that unchanged graph (R-2);
  it authors no second census graph.
- [FR-1015-supersede-id-ledger-under-fr-1010.md](FR-1015-supersede-id-ledger-under-fr-1010.md)
  — the authority under which the legacy ID-registry artifacts become
  `delete` rows.
- [FR-889-os-enforced-main-write-lock.md](FR-889-os-enforced-main-write-lock.md)
  — `.chaplain/` is `dr-xr-xr-x` on the main checkout though not in
  `FR889_GOVERNED_ROOTS` (a residue); `git rm` in a worktree is unaffected,
  but the post-merge `sync` on main must succeed — witnessed in AC.

## Summary

Produce an exact, model-assisted disposition census of every test file and
CAP that references the Chaplain runtime; publish the runtime's history as
a **source-only** archived repository and a tag; then delete `.chaplain/`
and everything the census marks `delete`, retire the CAPs it marks
`retire`, and leave `docs/archive/chaplain.md` as the one paragraph that
says where it went. Every commit in the PR **except the designated RED**
leaves `req_coverage --strict`, `validate_capabilities --strict`, and the
full non-slow unit suite green (history contract in Step 2).

## Value Statement

The registry stops claiming ~27 capabilities and ~50 test files for a
runtime that has not run since 2026-07-07; agents stop paying orientation
cost for it; the FSM's history stays one URL away.

## Problem

After FR-1011 and FR-1015, `.chaplain/` contains only the dead FSM runtime
(`config/`, `actions/`, `lib/watcher/`, `scripts/`, `demos/watcher2-*`,
`graphs/watcher-*`, `inquisitor.sh`, `philosopher.sh`, `id-registry.yaml`,
`done/`, `processing/`, `README.md`) — 161 tracked files. Coupled to it:

| Class | Count (2026-09-06) | Disposition mechanism |
|---|---|---|
| `tests/**/*.py` referencing `.chaplain`/`inquisitor` | 59 files, ~730 tests (minus FR-1011's four relocated files) | census |
| `capabilities/CAP-*.yaml` naming chaplain/watcher/inquisitor/philosopher/inbox/triage/distill | 27 (4 already retired; CAP-75/205/206 relocated by FR-1011, kept) | census |
| `.github/hooks/tests/` (Tier 2) | 1 file — already fixed by FR-1014 | verify only |
| `scripts/` | `id_registry.py`, `validate_id_registry.py`, `chaplain-prompts/` | census (`delete` under FR-1015) |
| `.pre-commit-config.yaml` | `validate-id-registry` hook | delete with its script |
| `.github/skills/chaplain-ops/` | whole skill | delete |
| `.gitignore` | `.chaplain/` entries | delete |

The hazard the census exists for: **shared REQ fan-in**. A CAP may carry a
REQ that a non-chaplain test also marks; retiring the CAP then trips
`req_coverage --strict` (live mark on retired REQ), and deleting the test
without retiring the CAP trips it the other way. Hand-classifying the
corpus × REQ sets is the `impossibly_large_sequential_task` signal; the
census computes fan-in in code and asks the model only the semantic
question ("does this test witness the runtime, or a still-live behaviour
that happens to mention it?").

## Raw Input Read (R-1; read 2026-09-06 on `main` @ `1c0b083f`)

Fan-in = count of test files **outside** the candidate set marking the same
REQ (`grep -rlE '"REQ-YG-NNN"' tests/unit tests/integration | grep -v <self>`).

| # | Sample | REQs / fan-in | Cited lines | Proposed | Surprising detail |
|---|---|---|---|---|---|
| 1 | `tests/unit/test_fr305_watcher_pipeline_v2.py` (certain-delete) | REQ-YG-316 / 0 | `:20 CHAPLAIN = WORKTREE / ".chaplain"`; 52 `def test_` | `delete` | 52 tests for one FSM config file (`watcher-pipeline-v2.yaml`) — the single largest witness file in the set guards a YAML nobody loads. |
| 2 | `tests/unit/test_fr_triage.py` (certain-keep, relocated by FR-1011) | REQ-YG-564 / 0 | `:27 TOOLS = REPO / ".chaplain/graphs/fr_triage/tools.py"` (→ `graphs/fr_triage/` after FR-1011) | `keep` | Fan-in 0 and a `.chaplain` literal — the same *arithmetic* signature as sample 1. Only the semantic question separates them: this one witnesses a live pre-commit gate (`checks/triage_gate.py`). A fan-in-only rule would delete it. |
| 3 | `tests/unit/test_fr319_watcher_yamlgraph_async_shell_safe_vars.py` (shared-REQ) | REQ-YG-027 / **7** (CAP-08 Error Handling: `test_on_error_skip.py` …) | `:14 ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "yamlgraph_async_action.py"`; `:104,128,149` | `delete` + REQ stays live | A watcher-action test marks a **core** error-handling REQ. Deleting the file is safe (7 other witnesses); retiring the REQ would be wrong. The row must carry `fan_in_by_req`, not a single number. |
| 4 | `capabilities/CAP-137-watcher-fsm-startup-script.yaml` (runtime-only CAP) | REQ-YG-315 / (sole module `.chaplain/scripts/start-system.sh`) | `:8-11`, `fr: FR-296` | `retire` | Its only module is the script the judge cited as proof the archive is not runnable (`start-system.sh:16`). |
| 5 | `capabilities/CAP-114-automated-post-merge-finalization.yaml` (mixed/live CAP) | REQ-YG-261 / 1 (`test_automated_post_merge_finalization.py` only) | modules `:8 .chaplain/lib/finalize_lib.sh`, `:9 .chaplain/watch.sh`, `scripts/finalize_merge.sh` | `keep` + `manual_review` | Module `.chaplain/watch.sh` **does not exist** (`ls` → ENOENT); the CAP has claimed a phantom since FR-317. `finalize_lib.sh` is live and relocates under FR-1011. The test's docstring cites `watch.sh` too and contains the literal `FR-999-test-feature` — a naive `REQ-YG-\d+` regex reads that as a shared REQ-YG-999 with fan-in 3 (`test_check_changelog_req.py`, `test_req_coverage.py`, `test_fr851_req_audit_red.py`), all fixture strings. Fan-in must be computed from `@pytest.mark.req` AST, not from regex over file text. |

Two boundary lessons already extracted for the schema: (a) fan-in is
per-REQ, not per-file; (b) REQ IDs come from marker AST
(`scripts/req_coverage.py`'s extractor), never from text regex. Sample 5
also shows a CAP can name a module that no longer exists — the CAP row
needs `modules_present{}` so "all modules runtime-owned" is decided on
facts.

## Ideal Result

`git ls-files .chaplain | wc -l` → 0. `git ls-remote --tags origin chaplain-archive`
→ the pre-removal SHA. `gh repo view sheikkinen/yamlgraph-chaplain --json isArchived`
→ `true`, and its README's first line says it is historical source, not a
runnable distribution. `docs/census/chaplain-test-disposition.jsonl` names
every test file and CAP with `keep|delete|retire`, a reason, and REQ
fan-in; the PR deletes exactly the `delete` rows and retires exactly the
`retire` rows. `req_coverage --strict` reports N covered / N total with
no `.chaplain` path anywhere in its output. `docs/archive/chaplain.md`
exists. `scripts/vscode/now.py` prints no `.chaplain` string.

## Proposed Solution

### Prerequisite gate (R-4) — all fields filled before any Phase 2 command

| Prerequisite | Merge SHA | Human-review ref | Evidence |
|---|---|---|---|
| FR-1014 dir-aware guard | `fec26941` (PR #612, merged 2026-09-06) | operator `merge` verdict on PR #612, recorded in FR-1014 AC-14 | review draft + dispositions on PR #612 |
| FR-1011 relocate live parts | `84baceb7` (PR #615, merged 2026-09-06) | operator merged PR #615 (AC-19 review by merge) | inbox manifest: FR-1011 § Implementation Record (PR #614); `.chaplain/inbox/` migration confirmed by operator 2026-09-06: "inbox is safely in main" (manifest PR #614; eight carries hash-verified into `proposals/`). The originals' deletion on the iMac is not separately attested — Phase 2's `git rm -r .chaplain` removes only tracked files and leaves an untracked `inbox/` untouched, so nothing is lost either way |
| FR-1015 supersede FR-975/980 | `32fd6e9f` (PR #619, merged 2026-09-06) | operator `merge` on PR #619 after review P1 dispositioned | contract quote verified byte-identical to FR-1010 |

### Archive visibility decision (R-7) — answered before any remote operation

> Archive visibility: `private` or `public`? Operator: **private** Date: **2026-09-06**
> Rationale: operator's word to the enforcing session ("archive can be private"); source-only historical archive of a private repository. Reviewed commit/PR: _pending — the pre-remote review (AC-11) records it_

An unanswered field authorizes no repository creation; it does **not**
default to private.

### Step 0 — Census (committed before any deletion; R-2, R-3 both rounds)

**Sole invocation surface (round 2 R-3): `scripts/chaplain_census.py`**,
checked in, fail-closed. It: validates the filled prerequisite gate and
the immutable source SHA (must descend from all three prerequisite merge
SHAs); applies the deterministic, sorted, de-duplicated discovery rule
below; records repository visibility / data classification
(operator-owned code; `claude-haiku-4-5`); rejects credential-bearing
input; enforces **before the first provider call** the ceilings ≤ 120
items, ≤ 1.5 MB total, ≤ 64 KB per item (**operator amendment
2026-09-06**: the frozen 48 KB refused `tests/unit/test_philosopher.py`
at 52 409 B on the first preflight; raised to 64 KB by operator decision
rather than truncating or excluding the item — AC-05 reads accordingly),
≤ 130 model calls; wraps the
whole graph process in a 20-minute deadline; invokes the **unchanged**
`examples/demos/corpus_census/graph.yaml` with the exact discover/extract
manifests, labels, provider/model, raw-ledger path and brief/rubric; then
runs the Chaplain reconciler. Tests prove every preflight refusal happens
before provider invocation.

Bound to the unchanged graph (FR-892). Consumer-specific pieces live with
the existing adapter family:

- `examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml` +
  `chaplain_adapters.py` — **one deterministic discovery rule**:
  `git ls-files 'tests/**/*.py' | xargs grep -lE '\.chaplain|inquisitor|watcher2?|philosopher|inbox|triage|distill|chaplain'`
  ∪ `git ls-files 'capabilities/CAP-*.yaml' | xargs grep -lE 'chaplain|watcher|inquisitor|philosopher|inbox|triage|distill'`
  ∪ the two legacy ID-registry tests (`tests/unit/test_id_registry.py`,
  `tests/unit/test_fr754_id_registry_package_boundary.py`) as ordinary
  test rows; sorted, de-duplicated. **Only tests and CAPs are census
  items** (review P2). The non-census deletion set — `scripts/id_registry.py`,
  `scripts/validate_id_registry.py`, `.github/skills/chaplain-ops/**`,
  `scripts/chaplain-prompts/**`, the `validate-id-registry` hook block —
  is enumerated deterministically in Step 2 (judgement D-6), never sent
  to the model. The frozen manifest `docs/census/chaplain-disposition-input.jsonl`
  records per item: source tree SHA, path, kind, bytes, SHA-256, REQs
  (marker AST), `fan_in_by_req`, and for CAPs `modules[]`,
  `modules_present{}`, `current_status`. Per-REQ fan-in and module
  presence are computed in code (invariant 5).
- `chaplain-extract.tool.yaml` — payload = file text + the item's facts
  row.
- **Output contract (round 2 R-2).** The shared graph has one fixed model
  schema, `CorpusCensusFinding` (`prompts/judge_item.yaml:21-43`), and one
  fixed reducer emitting `LedgerRow` (`tools.py:53-66,303-375`). The
  Chaplain rubric (`adapters/chaplain_rubric.md`) therefore asks the
  model for **only** a closed verdict label valid for the item kind
  (`keep|delete` for tests, `keep|retire` for CAPs) plus the schema's
  fixed `confidence`, exact `evidence_span`, and abstention fields. The
  shared reducer writes its generic ledger to a distinct raw-ledger path
  (`docs/census/chaplain-test-disposition.generic.jsonl`) that is never
  overwritten. A Chaplain-specific **deterministic Pydantic reconciler**
  (`chaplain_adapters.py::reconcile`) joins each generic row to the
  collector-owned manifest facts and emits the frozen rows:
  - test row: `path, kind=test, verdict: keep|delete, reason, reqs[], fan_in_by_req{}, cites[], manual_review: bool`
  - CAP row: `path, cap_id, kind=cap, current_status, verdict: keep|retire, reason, reqs[], modules[], modules_present{}, surviving_witnesses_by_req{}, cites[], manual_review: bool`
  Code, not the model, copies `path`, `kind`, REQs, fan-in, modules,
  module presence and status. The reconciler rejects illegal
  kind/verdict pairs, abstained/demoted/failed rows, missing/duplicate/
  unknown IDs (invariants 2, 4, 7), invalid evidence spans, and any
  unresolved `manual_review`. Rubric rules: a test is `delete` only if
  its subject is the runtime **and** every REQ it marks has `fan_in > 0`
  or belongs to a CAP marked `retire` in the same run; a CAP is `retire`
  only when every requirement and every *present* module is runtime-owned
  or explicitly dispositioned; any mixed CAP is `keep` + `manual_review`,
  and **enforcement stops** until this FR records the human resolution.
- Canaries (invariant 8), withheld from the rubric, matched by verdict
  family: `tests/unit/test_fr305_watcher_pipeline_v2.py` → `delete`;
  `tests/unit/test_fr_triage.py` (post-FR-1011 path) → `keep`.
- Outputs: `docs/census/chaplain-test-disposition.jsonl` + `.md` +
  `.run.json` (provider, model, run id, source SHA, the three prerequisite
  merge SHAs, ceilings, counts, unresolved count). Raw primary outputs
  under `docs/census/chaplain-test-disposition.raw/`, **read by a named
  human** before the reduction is trusted (`read_raw_output_first`).

If the shared graph cannot carry one required invariant, **stop** and file
the generic gap as its own FR; do not copy or modify the graph, prompts,
or reducer.

### Step 1 — Archive (pre-remote human review; R-6, R-7; round 2 R-4, R-5)

Delivered as `scripts/chaplain_archive.sh` — checked in, fail-closed,
explicit inputs, typed preflight exits, **journaled and resumable**.
Human-owned inputs are exactly: the visibility choice (from the decision
field), the review judgement, and the merge decision.

**`PRE` (round 2 R-4)** = the human-reviewed **census/evidence commit**
(Step 2 class 1), a clean commit reachable from `origin/main`, whose
`.chaplain` tree identity (`git rev-parse "$PRE":.chaplain`) equals the
tree recorded in the disposition input manifest. The archive manifest
`docs/census/chaplain-archive-manifest.txt` is built **from the commit
object** (`git ls-tree -r "$PRE" -- .chaplain` + `git cat-file` → SHA-256),
never from the index or working tree, with paths stored
**archive-relative** (`.chaplain/` prefix stripped) so they compare
equal to the fresh archive root.

```
Usage: scripts/chaplain_archive.sh --visibility private|public --pre <sha> [--dry-run] [--resume]
Exit 64  usage / missing --visibility
Exit 65  preflight: tag chaplain-archive exists (local or origin) and does not match journal
Exit 66  preflight: sheikkinen/yamlgraph-chaplain exists and does not match journal
Exit 67  preflight: --pre not reachable from origin/main, not clean, lacks .chaplain/, or .chaplain tree != manifest tree
Exit 68  post-condition: archive clone (archive-relative path set, SHA-256s) != frozen manifest, or README first line not the banner
Exit 69  journal/remote mismatch on --resume (PRE, SPLIT, visibility, or archive identity differ) → human reconciliation
```

**Journal (round 2 R-5):** `docs/census/chaplain-archive.run.json`,
created atomically (write-temp + rename) **before the first remote
mutation**, updated after each state transition, committed in GREEN.
States: `tag_created → repo_created → split_pushed → readme_committed →
verified → archived`. On `--resume`, an existing tag or repository is
accepted **only** when journal and remote facts exactly match the frozen
`PRE`, `SPLIT`, visibility and expected archive identity; any unrelated
or mismatched resource keeps the collision exit and stops. Tests inject
failure after each transition and prove resume completes without
duplicate mutation, and prove mismatches stop.

Steps: preflights; `git tag chaplain-archive "$PRE"` + push; manifest from
commit object; `SPLIT=$(git subtree split -P .chaplain "$PRE")`;
`gh repo create sheikkinen/yamlgraph-chaplain --$VISIBILITY --description "Historical source of the YAMLGraph Chaplain FSM runtime (2026-03 -> 2026-09). Not a runnable distribution."`;
push `SPLIT` → `refs/heads/main`; clone; **prepend** banner + links to the
split's existing root `README.md` (formerly `.chaplain/README.md`) — the
only post-split content change; commit → `ARCHIVE_HEAD`; verify
(archive-relative path set == manifest, every SHA-256 equal except
`README.md`, first line contains "not a runnable distribution",
`gh repo view --json isArchived,visibility,defaultBranchRef` matches);
`gh repo archive --yes`. `--dry-run` executes preflights and prints the
plan (the pre-remote review artifact). Three immutable identities (`PRE`,
`SPLIT`, `ARCHIVE_HEAD`) + manifest SHA-256 + transitions + timestamps land
in the journal and `docs/archive/chaplain.md`.

### Step 2 — Removal (one PR; R-5 history contract; human gate C-4)

Traceability frozen **before** RED under FR-1015's allocation contract
(`max(ids on main + all open PR heads) + headroom`): new
`capabilities/CAP-<N>-chaplain-runtime-retired.yaml` with one
`REQ-YG-<M>` — "the Chaplain runtime is absent from `main`; its source is
reachable only via the `chaplain-archive` tag and the archived repository;
the census `delete`/`retire` sets equal the enacted sets". `N`/`M` are
allocated at enforcement start and written here. **Not** CAP-165: its
REQ-YG-466 is about FR-277 watcher2 baseline checkpointing.

History contract (four commit classes, in order; review P4):

1. **Census/evidence commit** — manifests, `scripts/chaplain_census.py`,
   adapters, rubric, raw + generic + reconciled artifacts, run record,
   exact CAP/REQ allocation, this FR's Raw-read/human-read record. Passes
   all gates. **This commit is `PRE`** once human-reviewed (pre-remote
   review, round 2 R-6).
2. **RED commit** (`SKIP=pytest`) — `tests/unit/test_fr1012_chaplain_removed.py`
   tagged `@pytest.mark.req("REQ-YG-<M>")`, asserting: `.chaplain/`,
   `chaplain-ops/`, `chaplain-prompts/`, `id_registry.py`,
   `validate_id_registry.py` absent; `validate-id-registry` absent from
   `.pre-commit-config.yaml`; every census `delete` path absent; every
   census `retire` CAP has `status: retired` + `retired_by: FR-1012`;
   `docs/archive/chaplain.md` present with `PRE`/`SPLIT`/`ARCHIVE_HEAD`;
   `subprocess.run(["python","scripts/vscode/now.py"])` stdout has no
   `.chaplain`. Its assertion failures are recorded.
3. **One atomic GREEN commit** — CAP `retire` transitions + census
   `delete` test deletions + `git rm -r .chaplain .github/skills/chaplain-ops scripts/chaplain-prompts scripts/id_registry.py scripts/validate_id_registry.py`
   + hook block removal + `.gitignore` lines + new CAP file +
   `docs/archive/chaplain.md` + completed `docs/census/chaplain-archive.run.json`
   + `python scripts/aggregate_capabilities.py` + changelog fragment +
   `docs/diary/` Distill entry (R-9). Makes the focused witness,
   `req_coverage --strict`, `validate_capabilities --strict`,
   `lint-imports`, and the full non-slow suite pass.
4. Every later commit and final PR HEAD passes all checks.
5. **Post-merge follow-up (docs-only; round 2 R-7)** — a separate
   FR-1012 commit/PR that records `docs/census/chaplain-postmerge.run.json`
   and completes § Implementation Record, merged **before FR-1013 starts**.

**Two human reviews (round 2 R-6), chronologically possible:**
- **Pre-remote review** — before tag push or repo creation: exact census +
  manual resolutions, visibility decision, frozen `PRE`, archive manifest,
  `chaplain_archive.sh --dry-run` output, intended remote operations.
- **Pre-merge review** — before merge: actual remote journal +
  `gh repo view` evidence, hook removal, exact mass-deletion diff,
  RED/GREEN SHAs and outputs, final validation, deviations.

`docs/archive/chaplain.md`: one paragraph (what it was, when it ran, why
archived), tag, repo URL, verified visibility + archive status, the three
SHAs, and a replacement table with a row for **every** FR-1010 live-parts
category (dispatcher → operator + `scripts/author.sh`/`judge.sh`/`review.sh`;
inbox → `proposals/`; fr_triage/world_distill/philosopher → `graphs/`;
finalize_lib → `scripts/lib/`; id-registry → enumeration at filing +
FR-701 (FR-1015); inquisitor → none, retired).

### Step 3 — Post-merge witness (scripted; round 2 R-7)

`scripts/chaplain_postmerge_witness.sh` on the main checkout: runs
`scripts/worktree.sh sync` (if `git` cannot unlink the 555 `.chaplain`
dir, `chmod u+w .chaplain` first — the script does this and logs it);
asserts `git ls-files .chaplain` empty; asserts `python scripts/vscode/now.py`
stdout has no `.chaplain` (`! grep -q`); writes
`docs/census/chaplain-postmerge.run.json` (committed by the follow-up,
history class 5) naming the three prerequisite merge SHAs and the Phase 2
merge SHA. Exit 0 only if all hold.

### Census findings (Step 0 run of 2026-09-06 — read before trusting any row)

Corpus was larger than the plan's estimate: the frozen regex selects **78 test
files and 37 CAPs** (plan: 59 / 27), because `watcher2?`, `philosopher`,
`inbox`, `triage`, `distill` match live files in passing — which is the design
(candidates, not verdicts).

Model quality on the raw rows (115): 46 delete / 41 keep / 26 retire /
1 abstain / 1 manual_review; canaries both correct. Errors the raw read caught,
each now a proposed resolution:

| Row | Model said | Why wrong | Proposed |
|---|---|---|---|
| `tests/unit/test_fr1011_relocation.py` | delete 0.95 | the FR-1011 relocation witness for the live graphs; its REQ is a module-level `pytestmark`, invisible to the marker extractor, so fan-in could not protect it | keep |
| `tests/unit/test_fr1012_chaplain_census.py`, `CAP-264` | delete / retire 0.95 | self-referential: the census tooling and its own CAP | keep |
| `tests/unit/test_id_registry.py` | keep 0.95 | FR-1015 makes the legacy allocator a deletion; its REQs have 5/4 outside witnesses | delete |
| `tests/unit/test_migrate_diary.py` | delete 0.95 | subject `scripts/migrate_diary_to_folder.py` exists and is live | keep |
| `tests/unit/test_fr436_req_traceability_scope_red.py` | delete 0.95 | subject is the ADR-001 scope contract; inquisitor.sh appears only as an excluded example | keep |
| `tests/unit/test_chaplain_graph_compile.py` | delete 0.95 | compiles `graphs/` (live) as well as `.chaplain/graphs`; sole witness of REQ-YG-529 | keep; GREEN drops the `.chaplain` root |
| `tests/unit/test_fr382_…scope_red.py` | keep 0.92 (inexact span) | correct verdict, but it asserts `.chaplain/graphs/watcher-enforce/prompts/context-planner.yaml` exists | keep; GREEN narrows the inventory |
| `CAP-67`, `CAP-73` (philosopher) | manual / retire | modules still point at `examples/philosopher/*` (absent since FR-196) — FR-1011 repointed CAP-75/205/206 only | keep; GREEN repoints modules to `graphs/philosopher/` |
| `CAP-114` | retire 0.95 | finalizer is live (FR-1010 R-4); only the phantom `.chaplain/watch.sh` module and the watcher prose are dead | keep; GREEN drops the phantom module |
| `CAP-116` | retire 0.95 | REQ-YG-263's two outside witnesses were **mis-tagged live module-map tests** (FR-331/FR-335 had no CAP); every CAP-116 module is a `.chaplain/` file Phase 2 deletes | **operator 2026-09-06: retire**; new `CAP-265` / `REQ-YG-667` "Static module map" allocated and both tests re-tagged (`ba9f578f`) |
| `CAP-55`, `CAP-106`, `CAP-125`, `CAP-152` | retire 0.95 | flagged mixed only because they list live docs (`CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, Scripture) as modules; the described behaviour is the dead runtime | retire |
| `CAP-135`, `CAP-137`, `CAP-205`, `CAP-259` | correct verdicts, inexact spans (YAML lines stitched; CAP-205 quoted the rubric) | evidence contract, not semantics | as the model said |
| `CAP-44` | abstain (its own output failed the schema) | judge-split-verdict prompt lives in the deleted `scripts/chaplain-prompts/`; live judge is the skill | retire |

Rule findings folded into the reconciler (deterministic code, no model change):
a resolution counts only with `confirmed: true`, an unconfirmed proposal keeps
the row manual and shows the proposal; a CAP's own witness test that this
census deletes is not a "foreign module" (the first pass flagged 16 CAPs
mixed on that alone and cascaded into 24 orphan flags). Marker-AST fan-in
follows `req_coverage`'s extractor exactly, so module-level `pytestmark`
REQs are invisible to both — recorded as a known blind spot, not patched
here.

Deterministic non-census deletion set (D-6) is unchanged: `scripts/id_registry.py`,
`scripts/validate_id_registry.py`, `.github/skills/chaplain-ops/**`,
`scripts/chaplain-prompts/**`, the `validate-id-registry` hook block.

## Acceptance Criteria (round-2 judgement, verbatim; R-7)

- [ ] AC-01: FR-1014, FR-1011, and FR-1015 merge SHAs and human-review references are recorded; FR-1011's 13-item inbox manifest is linked and `.chaplain/inbox/` is confirmed empty; the census source SHA descends from all three merge SHAs.
- [ ] AC-02: `## Raw Input Read` retains at least five source-cited samples covering certain-delete, certain-keep, shared-REQ, runtime-only CAP, and mixed/live CAP boundaries, each with per-REQ fan-in and a concrete surprising detail.
- [ ] AC-03: `scripts/chaplain_census.py` binds Chaplain manifests and rubric to unchanged `examples/demos/corpus_census/graph.yaml`; no second graph/prompt tree or modification to the shared graph, prompts, or reducer exists.
- [ ] AC-04: The census model output uses the fixed `CorpusCensusFinding` schema; the generic ledger is preserved separately; a deterministic Pydantic reconciler emits the frozen test/CAP rows and rejects illegal kind/verdict pairs, abstained/demoted/failed rows, missing/duplicate/unknown rows, invalid evidence spans, and unresolved manual reviews.
- [ ] AC-05 (per-item ceiling amended to 64 KB by operator, 2026-09-06 — see § Step 0): Before the first provider call, the census wrapper records source SHA, visibility/data classification, provider/model, item paths/kinds/bytes/SHA-256, marker-AST REQs, per-REQ fan-in, CAP modules/presence/status, and rejects any breach of the 120-item, 1.5-MB-total, 48-KB-item, 130-call, credential, or policy ceilings; the whole graph process has a 20-minute enforced timeout.
- [ ] AC-06: The run record proves all eight corpus-map-reduce invariants, both withheld canary families, exact generic-ledger-to-manifest coverage, valid citations, and zero unresolved rows; a named human records reading the raw primary outputs before trusting the disposition artifact.
- [ ] AC-07: The census/evidence commit contains the manifests, wrapper, adapters, rubric, raw/generic/reconciled artifacts, run record, exact CAP/REQ allocation, and human-read record; it passes all applicable gates before RED.
- [ ] AC-08: The dedicated RED commit adds only the frozen focused removal witness, is marked `SKIP=pytest`, and records its expected assertion failures; the immediately following atomic GREEN makes that witness, `python scripts/req_coverage.py --strict`, `python scripts/validate_capabilities.py --strict`, `lint-imports`, and `pytest tests/unit -q -m "not slow" -n auto` pass.
- [ ] AC-09: Every commit except the designated RED passes the checks applicable to its state; final Phase 2 PR HEAD passes every AC-08 command, with RED/GREEN SHAs and outputs recorded.
- [ ] AC-10: The deleted test set equals reconciled test `delete` rows; transitioned CAPs equal reconciled CAP `retire` rows; `git ls-files .chaplain .github/skills/chaplain-ops scripts/chaplain-prompts scripts/id_registry.py scripts/validate_id_registry.py` prints nothing; the hook and matching `.gitignore` lines are absent; no other deletion occurs.
- [ ] AC-11: Pre-remote human review records the exact census/manual resolutions, visibility decision, frozen `PRE`, archive manifest, archive-script dry run, and intended remote operations before tag push or repository creation.
- [ ] AC-12: `PRE` equals the reviewed census/evidence commit; its `.chaplain` tree equals the disposition input tree; the archive manifest is generated from the commit object with archive-relative paths and SHA-256 values.
- [ ] AC-13: The archive script writes an atomic durable journal before mutation; unrelated tag/repository collisions fail with the frozen typed exits; injected partial failures resume only when journal and remote `PRE`/`SPLIT`/visibility identities match exactly; mismatches stop for human reconciliation.
- [ ] AC-14: `git ls-remote --tags origin refs/tags/chaplain-archive` resolves exactly to `PRE`; final `gh repo view` proves the selected visibility, archived state, and default branch; the committed archive journal records `PRE`, `SPLIT`, `ARCHIVE_HEAD`, manifest SHA-256, transitions, and timestamps.
- [ ] AC-15: A fresh archive clone has exactly the archive-relative frozen path set and file count; every source hash matches except `README.md`, whose only content change is the prepended historical-source banner and links; its first line contains "not a runnable distribution."
- [ ] AC-16: `docs/archive/chaplain.md` records the tag, URL, verified visibility/archive status, three immutable SHAs, and one replacement row for every FR-1010 live-parts category.
- [ ] AC-17: `python scripts/aggregate_capabilities.py && git diff --exit-code -- ARCHITECTURE.md` succeeds; explicit no-match assertions prove `scripts/vscode/now.py` emits no `.chaplain`; the named existing focused tests for `scripts/finalize_merge.sh`, CAP-38, and CAP-45 pass (`pytest tests/unit/test_finalize_merge.py tests/unit/test_automated_post_merge_finalization.py tests/unit/test_diary_reflections_fr152.py -q`), as does the full non-slow suite.
- [ ] AC-18: Pre-merge human review records the actual remote journal/state, hook removal, exact mass-deletion diff, RED/GREEN record, final validation, and deviations before merge.
- [ ] AC-19: `scripts/chaplain_archive.sh`, `scripts/chaplain_postmerge_witness.sh`, and `scripts/chaplain_census.py` are checked in with focused tests for every refusal, success, and partial-recovery path; the census and archive were produced by those scripts, and their committed run records match the reviewed invocations.
- [ ] AC-20: After merge, `scripts/chaplain_postmerge_witness.sh` exits 0 on main, proving sync succeeded, `.chaplain` is untracked-empty, and `now.py` emits no `.chaplain`; a docs-only FR-1012 follow-up commit records `docs/census/chaplain-postmerge.run.json` and completes the implementation record before FR-1013 starts.
- [ ] AC-21: Any new live artifact, prerequisite or `.chaplain` tree drift, unresolved census row, provider-policy failure, archive mismatch, or mismatched remote/tag state stops enforcement and returns FR-1010/FR-1012 to judgement.
- [ ] AC-22: `changelog/unreleased/fr-1012-chaplain-runtime-removed.md` and a `docs/diary/` Distill entry with `**Seed:**` are committed; the implementation record contains every census, archive, review, validation, follow-up, and deviation reference.

## Purge list

- No symlink, stub, or `README.md` left at `.chaplain/`.
- No "deprecated" shim for `validate_id_registry.py`.
- No edits to FR-701's gate.
- No runnable-standalone claim anywhere (FR-1010 C-8).
- No second census graph or prompt tree (R-2).

## Alternatives Considered

| Option | Why not |
|---|---|
| Hand-classify the corpus | `impossibly_large_sequential_task`; per-REQ fan-in arithmetic by hand is exactly the error class the census exists to remove (sample 5 shows even a regex gets it wrong). |
| Author a dedicated `chaplain_disposition_census` graph (first draft) | Withdrawn per R-2: FR-892 shipped the census skeleton with injected adapters for exactly this; a copy is `growth_as_default`. |
| Delete tests first, retire CAPs in a later commit | FR-701's gate is red in between; FR-465 established same-commit; R-5 makes it one atomic GREEN. |
| Skip the archive repo, tag only (FR-1010 §2) | Viable; FR-1010 selected §3 for a browsable URL. Zero difference on `main`. |
| Default the archive to private (first draft) | Withdrawn per R-7: visibility is a product/privacy decision the operator records; silence authorizes nothing. |
| Tag the witness on CAP-165 (first draft) | Withdrawn per R-5: REQ-YG-466 is FR-277 baseline checkpointing; a new one-REQ CAP is honest. |

## Related

- FR-1010 (plan), FR-1011/FR-1014/FR-1015 (prerequisites), FR-1013 (next)
- `reference/patterns/corpus-map-reduce.md`, `examples/demos/corpus_census/`

## Implementation Record (R-9)

| Field | Value |
|---|---|
| Census run id / provider / model | `6f7f1ab6-3288-4f83-9a22-5f8f205ecc51` / `anthropic` / `claude-haiku-4-5`; started 2026-09-06T10:55:24Z, 116 calls, ~2 min; reconcile-only re-run 2026-09-06T11:05:13Z with proposed resolutions (`scripts/chaplain_census.py --reconcile-only --resolutions docs/census/chaplain-manual-resolutions.json`, exit 75 = unresolved rows) |
| Input tree SHA / manifest SHA-256 | source `d7601937` (census tooling commit on this branch, descends from all three prerequisites), `.chaplain` tree `3b25919c`; manifest `docs/census/chaplain-disposition-input.jsonl` sha256 `e4d5c5a83e93d2d7de26c0a221775b1a18776e49c745231c5ab1d876852c45bc` (115 items: 78 tests, 37 CAPs, 807 264 B; see `manifest_sha256_note` in the run record for the CRLF hashing correction) |
| Raw-read reviewer + date | operator delegated the read to the enforcing session on 2026-09-06 ("check the deletes and proceed"); record: `docs/census/chaplain-test-disposition.human-read.md` — first pass over all 115 rows (verdict/confidence/span), second pass over the 41 model-decided deletes against their sources; 40 upheld, `test_fr754_…` overridden to keep. **Deviation from AC-06's letter**: the named human did not read the raw ledger; the delegation and the record stand in for it |
| Canary results (family match) | both match: `tests/unit/test_fr305_watcher_pipeline_v2.py` → delete (0.98), `tests/unit/test_fr_triage.py` → keep (0.95); withheld from the rubric (test asserts it) |
| `manual_review` rows + human resolutions | First reconciliation: 30 manual rows (21 proposed + 9 dependent tests). Operator 2026-09-06 confirmed 20 as proposed, then, after the REQ-YG-263 investigation, CAP-116 → retire. Final reconcile-only (`--resolutions docs/census/chaplain-manual-resolutions.json`): **exit 0 — 41 delete / 24 retire / 50 keep / 0 unresolved**, 22 confirmed resolutions (21 operator-confirmed + 1 delegated delete-review override), canaries pass, all eight invariants true |
| New CAP-N / REQ-YG-M | `CAP-264` / `REQ-YG-666` (`capabilities/CAP-264-chaplain-runtime-retired.yaml`), allocated 2026-09-06 as max(main CAP-263 / REQ-YG-665, no open PR heads) + 1; witnessed today by `tests/unit/test_fr1012_chaplain_census.py` (19 tests) |
| RED SHA + assertion output | _pending_ |
| GREEN SHA + gate outputs | _pending_ |
| `PRE` / `SPLIT` / `ARCHIVE_HEAD` | `PRE=0184a73d22500bd2bc678be8374bc4095de4575f` (squash merge of the census PR #621; `.chaplain` tree `3b25919c` == disposition input tree) / `SPLIT=b31f58492832a2b3c4fdc1cec4e0625f3f0e97e7` / `ARCHIVE_HEAD=cf30d87f120aa16e12b441869c32209073e97fb6`. Run 2026-09-06 12:21–12:32Z by `scripts/chaplain_archive.sh --visibility private --pre 0184a73d…`; journal `docs/census/chaplain-archive.run.json` (all seven transitions), manifest `docs/census/chaplain-archive-manifest.txt` (146 files, sha256 `3d4a77fa…`). Verified: tag `chaplain-archive` on origin → PRE; `sheikkinen/yamlgraph-chaplain` PRIVATE, archived, default branch main, 146 blobs, README first line carries the banner |
| Visibility decision (operator, date, rationale, PR) | **private**, operator, 2026-09-06, "archive can be private"; census PR #621; archive created private and verified |
| Round-2 judgement human review (ref + date; activates `Judged`) | operator instruction "run the census" to the enforcing session, 2026-09-06 (after the merges of #615, #617, #619, #620); recorded here as the activation reference — the operator may replace it with an explicit review note |
| Pre-remote human review (AC-11) | operator instruction 2026-09-06: "continue to split .chaplain into private repo — including all git dance needed as pre-requisite", given after the census results, the dry-run plan and the review dispositions were reported; the dry run (146 files, private, seven steps) was shown before the real run. No separate review document — the instruction is the record |
| Pre-merge human review (AC-18) | _pending_ |
| Post-merge follow-up commit (AC-20) | _pending_ |
| Post-merge `sync` + `now.py` outcome | _pending_ |
| Deviations | (a) per-item ceiling 48 → 64 KB (operator, above); (b) census/evidence is three commits, not one: tooling `ecd6e1d6`+fixes, ceiling `d7601937`, reconciler refinements `ae1ba869`/`3139b390`, evidence `8d32f61f` — the graph ran at `d7601937`, so `PRE` should be the evidence commit whose `.chaplain` tree equals the input tree (unchanged across all of them); (c) the graph's 912 KB `--full` state dump is not committed (the generic ledger carries every `raw_judgement` verbatim); (d) the census brief was REJECTED by the shared citation boundary and is recorded, not used; (e) the manifest sha in the run record was first computed over LF text while Windows wrote CRLF — corrected to the on-disk bytes with a note, tooling fixed to write LF and hash bytes; (f) the discovery regex now also selects `CAP-264` and `tests/unit/test_fr1012_chaplain_census.py` (they contain "chaplain") — both confirmed keep; (g) **a second new CAP**: `CAP-265` / `REQ-YG-667` "Static module map" (fr: FR-331, FR-335) allocated by operator decision so CAP-116 can retire without orphaning two live tests — outside the frozen "exact new CAP/REQ" of D-5, recorded here for the pre-remote review; the two re-tagged tests are live and unrelated to the runtime; (h) the census manifest row for CAP-116 records fan-in as of source `d7601937`, before that re-tag; (i) invariants 3, 5, 6 and 7 in the run record were first asserted as literal `True`/tautology — replaced by computed checks before the record was trusted; (j) review of PR #621 (2026-09-06, *Not approved*, P1–P4): P2 — CAP-264's requirement text claimed the end state before it exists; reworded to the census/archive tooling that is true on main now, the runtime-absence claim moves to the GREEN removal commit; P3 — the archive script's `--resume` accepted a journal without re-checking the remotes; it now verifies tag==PRE, repository presence and visibility, remote main==SPLIT or ==ARCHIVE_HEAD per journaled state, rejects unknown states, and checks `defaultBranchRef`; tests inject failure after every transition plus a remote-drift case; P4 — the committed run record held a Windows path (`docs\census\…`); persisted paths are POSIX and a test asserts it; P1 — the reviewer does not accept the operator's delegation of the raw read as satisfying the human-read GATE (C-4/AC-06); the delegation stands as the operator's decision and is recorded in the run record's `human_raw_read` field and the human-read file; the reviewer also asks that CAP-265 (deviation g) be re-judged rather than accepted by operator decision — open for the operator |

## Judgement (2026-09-06)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1012-chaplain-subtree-archive-and-removal.judgement.md](FR-1012-chaplain-subtree-archive-and-removal.judgement.md).
R-1 (Raw Input Read, five samples), R-2 (reuse `corpus_census`; FR-892),
R-3 (one discovery rule; typed test/CAP rows; mixed CAP → `manual_review`
stop), R-4 (prerequisite gate table), R-5 (new CAP/REQ, not CAP-165;
four-class commit history, no `rebase -x`), R-6 (archive provenance:
README modified not added, manifest equality, three SHAs, fail-closed
preflights), R-7 (visibility decision field), R-8 (ACs verbatim), R-9
(implementation record + Distill) folded above.

**Review of PR #617 (2026-09-06, `scripts/review.sh`) folded:** P2 (census
items are tests + CAPs only; scripts/skill/prompts are the deterministic
D-6 set), P4 ("every commit except RED"), P5 (archive and post-merge
witness are checked-in fail-closed scripts with typed exits).

**Round-2 judgement (2026-09-06, after P5 widening) — APPROVED WITH
REVISIONS; R-1..R-7 folded:** R-1 (re-judgement state: pending human
review; reference to be recorded in § Implementation Record before
`Judged` activates), R-2 (bind to the real `CorpusCensusFinding` /
`LedgerRow` contract; generic ledger preserved; Pydantic reconciler emits
the frozen rows), R-3 (`scripts/chaplain_census.py` sole invocation
surface; ceilings enforced in code before the first provider call), R-4
(`PRE` = reviewed census commit; manifest from commit object,
archive-relative paths), R-5 (journal in `docs/census/`, resumable state
machine, exit 69), R-6 (pre-remote + pre-merge reviews), R-7 (post-merge
carrier committed by a docs-only follow-up; positive provenance; exact
focused tests named). Round-2 text appended to the judgement file.
