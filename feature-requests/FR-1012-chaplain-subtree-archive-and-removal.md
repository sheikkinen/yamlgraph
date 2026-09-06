# Feature Request: Subtree-split `.chaplain/` to a source-only archive and remove the runtime (Phase 2 of FR-1010)

**Priority:** MEDIUM
**Type:** Enhancement (subtraction; destructive — human gates C-4)
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-06). R-1..R-9 folded
below; see [FR-1012-chaplain-subtree-archive-and-removal.judgement.md](FR-1012-chaplain-subtree-archive-and-removal.judgement.md).
No Phase 2 command may run while any field of § Prerequisite gate is blank.
**Effort:** 2 days (census 0.5, removal 1, verification 0.5)
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 2 of 5; prerequisites FR-1014, FR-1011, FR-1015 must be **merged** and recorded in § Prerequisite gate before any Phase 2 operation (FR-1010 C-3, C-5). At filing (2026-09-06) none of the three is merged; FR-1014 is PR #612 (open), FR-1011 and FR-1015 are judged, unenforced.
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
says where it went. Every commit in the PR leaves `req_coverage --strict`,
`validate_capabilities --strict`, and the full non-slow unit suite green.

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
| FR-1014 dir-aware guard | _blank_ | _blank_ | PR #612 |
| FR-1011 relocate live parts | _blank_ | _blank_ | inbox manifest location: _blank_; `.chaplain/inbox/` empty confirmed by: _blank_ |
| FR-1015 supersede FR-975/980 | _blank_ | _blank_ | |

### Archive visibility decision (R-7) — answered before any remote operation

> Archive visibility: `private` or `public`? Operator: _____ Date: _____
> Rationale: _____ Reviewed commit/PR: _____

An unanswered field authorizes no repository creation; it does **not**
default to private.

### Step 0 — Census (committed before any deletion; R-2, R-3, R-7)

Bound to the **unchanged** `examples/demos/corpus_census/graph.yaml`
(FR-892). Consumer-specific pieces live with the existing adapter family:

- `examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml` +
  `chaplain_adapters.py` — **one deterministic discovery rule**, applied
  after the prerequisites merge:
  `git ls-files 'tests/**/*.py' | xargs grep -lE '\.chaplain|inquisitor|watcher2?|philosopher|inbox|triage|distill|chaplain'`
  ∪ `git ls-files 'capabilities/CAP-*.yaml' | xargs grep -lE 'chaplain|watcher|inquisitor|philosopher|inbox|triage|distill'`
  ∪ the explicit legacy set (`scripts/id_registry.py`,
  `scripts/validate_id_registry.py`, `tests/unit/test_id_registry.py`,
  `tests/unit/test_fr754_id_registry_package_boundary.py`,
  `.github/skills/chaplain-ops/**`, `scripts/chaplain-prompts/**`). The
  frozen manifest `docs/census/chaplain-disposition-input.jsonl` records
  per item: source tree SHA, path, kind, bytes, SHA-256, REQs (marker AST),
  `fan_in_by_req`, and for CAPs `modules[]`, `modules_present{}`,
  `current_status`. Per-REQ fan-in and module presence are computed in
  code (invariant 5).
- `chaplain-extract.tool.yaml` — payload = file text + the item's facts
  row. Preflight ceilings frozen in the run config: ≤ 120 items,
  ≤ 1.5 MB total, ≤ 48 KB per item, ≤ 130 model calls, ≤ 20 min wall
  clock; provider/data-classification decision recorded (repository is
  the operator's own code; `claude-haiku-4-5` as in `req_witness_audit`).
- Rubric (`adapters/chaplain_rubric.md`) with **two typed row schemas**:
  - test row: `path, kind=test, verdict: keep|delete, reason, reqs[], fan_in_by_req{}, cites[], manual_review: bool`
  - CAP row: `path, cap_id, kind=cap, current_status, verdict: keep|retire, reason, reqs[], modules[], modules_present{}, surviving_witnesses_by_req{}, cites[], manual_review: bool`
  Rules stated in the rubric: a test is `delete` only if its subject is
  the runtime **and** every REQ it marks has `fan_in > 0` or belongs to a
  CAP marked `retire` in the same run; a CAP is `retire` only when every
  requirement and every present module is runtime-owned or explicitly
  dispositioned; any mixed CAP is `keep` + `manual_review: true`, and
  **enforcement stops** until this FR records the human resolution for
  each such row.
- Canaries (invariant 8), withheld from the rubric, matched by verdict
  family: `tests/unit/test_fr305_watcher_pipeline_v2.py` → `delete`;
  `tests/unit/test_fr_triage.py` (post-FR-1011 path) → `keep`.
- Post-reconciliation (`chaplain_adapters.py`, deterministic): every
  manifest ID has exactly one result of the right kind (invariants 2, 4,
  7); every `cites[]` entry resolves to a line in the item; counts,
  unresolved-`manual_review` count, and cost computed in code; writes
  `docs/census/chaplain-test-disposition.jsonl` + `.md` + `.run.json`
  (provider, model, run id, input SHA). Raw primary outputs preserved
  under `docs/census/chaplain-test-disposition.raw/` and **read by a named
  human** before the reduction is trusted (`read_raw_output_first`).

If the shared graph cannot carry one required invariant, **stop** and file
the generic gap as its own FR; do not copy the graph.

### Step 1 — Archive (human gate C-4; R-6, R-7)

Preflights, fail-closed: `git tag -l chaplain-archive` empty locally and
`git ls-remote --tags origin refs/tags/chaplain-archive` empty;
`gh repo view sheikkinen/yamlgraph-chaplain` fails (name unused). Any
existing name stops enforcement for human reconciliation.

```bash
PRE=$(git rev-parse origin/main)                       # after FR-1015 merge; recorded
git tag chaplain-archive "$PRE" && git push origin chaplain-archive
git ls-files -z .chaplain | xargs -0 shasum -a 256 > tmp/chaplain-manifest.txt   # frozen path+hash set
SPLIT=$(git subtree split -P .chaplain "$PRE")         # recorded
gh repo create sheikkinen/yamlgraph-chaplain --<visibility from decision> --description "Historical source of the YAMLGraph Chaplain FSM runtime (2026-03 -> 2026-09). Not a runnable distribution."
git push git@github.com:sheikkinen/yamlgraph-chaplain.git "$SPLIT":refs/heads/main
# in a clone: PREPEND banner + links to the existing root README.md (the split's own README) — the only post-split change
ARCHIVE_HEAD=<sha after README commit>                 # recorded
gh repo archive sheikkinen/yamlgraph-chaplain --yes
```

The split's root `README.md` (formerly `.chaplain/README.md`) is
**modified**, not added: first line "Historical source snapshot — not a
runnable distribution.", then links to the `chaplain-archive` tag and
`docs/archive/chaplain.md`. Three immutable identities are recorded in
`.run.json` and `docs/archive/chaplain.md`: `PRE`, `SPLIT`, `ARCHIVE_HEAD`.

### Step 2 — Removal (one PR; R-5 history contract; human gate C-4)

Traceability frozen **before** RED under FR-1015's allocation contract
(`max(ids on main + all open PR heads) + headroom`): new
`capabilities/CAP-<N>-chaplain-runtime-retired.yaml` with one
`REQ-YG-<M>` — "the Chaplain runtime is absent from `main`; its source is
reachable only via the `chaplain-archive` tag and the archived repository;
the census `delete`/`retire` sets equal the enacted sets". `N`/`M` are
allocated at enforcement start and written here. **Not** CAP-165: its
REQ-YG-466 is about FR-277 watcher2 baseline checkpointing.

History contract (four commit classes, in order):

1. **Census/evidence commit** — manifests, adapters, rubric, jsonl, raw,
   run record, this FR's Raw-read/human-read record. Passes all gates.
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
   `docs/archive/chaplain.md` + `python scripts/aggregate_capabilities.py`
   + changelog fragment + `docs/diary/` Distill entry (R-9). Makes the
   focused witness, `req_coverage --strict`, `validate_capabilities --strict`,
   `lint-imports`, and the full non-slow suite pass.
4. Every later commit and final HEAD passes all checks.

`docs/archive/chaplain.md`: one paragraph (what it was, when it ran, why
archived), tag, repo URL, verified visibility + archive status, the three
SHAs, and a replacement table with a row for **every** FR-1010 live-parts
category (dispatcher → operator + `scripts/author.sh`/`judge.sh`/`review.sh`;
inbox → `proposals/`; fr_triage/world_distill/philosopher → `graphs/`;
finalize_lib → `scripts/lib/`; id-registry → enumeration at filing +
FR-701 (FR-1015); inquisitor → none, retired).

### Step 3 — Post-merge witness

On the main checkout: `scripts/worktree.sh sync` succeeds (if git cannot
unlink the 555 `.chaplain` dir, `chmod u+w .chaplain` first — recorded);
`python scripts/vscode/now.py | grep -q '\.chaplain'; test $? -eq 1`.

## Acceptance Criteria (from judgement, verbatim; R-8)

- [ ] AC-01: FR-1014, FR-1011, and FR-1015 merge SHAs and human-review references are recorded; FR-1011's 13-item inbox manifest is linked and `.chaplain/inbox/` is confirmed empty; no Phase 2 command ran before all fields were complete.
- [ ] AC-02: `## Raw Input Read` contains at least five source-cited samples covering certain-delete, certain-keep, shared-REQ, runtime-only CAP, and mixed/live CAP boundaries, each with computed fan-in and a concrete surprising detail.
- [ ] AC-03: The Chaplain census binds only consumer-specific manifests/adapters/rubric to unchanged `examples/demos/corpus_census/graph.yaml`; no `examples/demos/chaplain_disposition_census/` or second graph/prompt tree exists.
- [ ] AC-04: The frozen input manifest records source SHA, path, kind, bytes, SHA-256, REQs, and fan-in for every discovered item; hard item/byte/per-item/call/timeout ceilings and the provider/data-classification decision are recorded before the first model call.
- [ ] AC-05: The run record proves all eight corpus-map-reduce invariants, both withheld canary families, zero missing/duplicate/unknown/wrong-kind rows, valid citations, and zero unresolved `manual_review` rows; raw primary outputs were read by the recorded human before reduction was trusted.
- [ ] AC-06: `docs/census/chaplain-test-disposition.jsonl` and its summary are committed before RED or deletion; the deleted test set equals test `delete` rows, and transitioned CAPs equal CAP `retire` rows.
- [ ] AC-07: The exact new CAP/REQ and `tests/unit/test_fr1012_chaplain_removed.py` are frozen in the FR; the recorded RED commit fails the focused assertions with `SKIP=pytest`, and the immediately following atomic GREEN commit makes the focused test, `python scripts/req_coverage.py --strict`, `python scripts/validate_capabilities.py --strict`, `lint-imports`, and `pytest tests/unit -q -m "not slow" -n auto` pass.
- [ ] AC-08: Every commit except the designated RED passes the checks applicable to its state; final HEAD passes all AC-07 checks. The RED/GREEN SHAs and outputs are recorded.
- [ ] AC-09: `git ls-files .chaplain .github/skills/chaplain-ops scripts/chaplain-prompts scripts/id_registry.py scripts/validate_id_registry.py` prints nothing, the `validate-id-registry` hook is absent, and no census-authorized deletion exceeds the reviewed `delete` set.
- [ ] AC-10: The operator records `private` or `public`, date, rationale, and reviewed commit/PR before remote operations; preflights prove the tag and repository names unused; the creation command uses the decision and final `gh repo view` output proves visibility, archived status, and default branch.
- [ ] AC-11: `git ls-remote --tags origin refs/tags/chaplain-archive` resolves exactly to the recorded pre-removal commit; `docs/archive/chaplain.md` records that commit, the subtree-split commit, and final archive HEAD.
- [ ] AC-12: A fresh archive clone has exactly the frozen `.chaplain/` path set and file count; every source hash matches except `README.md`, whose sole documented transformation prepends the historical-source banner and links. Its first line contains "not a runnable distribution."
- [ ] AC-13: `docs/archive/chaplain.md` contains the tag, URL, verified visibility/archive status, immutable SHAs, and a replacement-table row for every FR-1010 live-parts category.
- [ ] AC-14: `python scripts/aggregate_capabilities.py && git diff --exit-code -- ARCHITECTURE.md` succeeds; an explicit no-match assertion proves `python scripts/vscode/now.py` emits no `.chaplain`; CAP-38, CAP-45, and `scripts/finalize_merge.sh` remain live and unchanged in behavior.
- [ ] AC-15: Human review of the exact census, manual resolutions, remote visibility, tag/repository operations, hook removal, mass-deletion diff, RED/GREEN record, and final validation is recorded before tag push, repository creation/archive, or merge.
- [ ] AC-16: Discovery of any new live artifact, existing remote/tag collision, unresolved census row, prerequisite drift, or FR-1010 live-parts change stops enforcement and returns FR-1010/FR-1012 to judgement.
- [ ] AC-17: `changelog/unreleased/fr-1012-chaplain-runtime-removed.md` and a `docs/diary/` Distill entry with `**Seed:**` are committed; the FR implementation record contains all run, archive, review, validation, and deviation evidence.
- [ ] AC-18: After merge, `scripts/worktree.sh sync` succeeds on main and an explicit no-match assertion proves `python scripts/vscode/now.py` emits no `.chaplain`; both outcomes are recorded.

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
| Census run id / provider / model | _pending_ |
| Input tree SHA / manifest SHA-256 | _pending_ |
| Raw-read reviewer + date | _pending_ |
| Canary results (family match) | _pending_ |
| `manual_review` rows + human resolutions | _pending_ |
| New CAP-N / REQ-YG-M | _pending_ |
| RED SHA + assertion output | _pending_ |
| GREEN SHA + gate outputs | _pending_ |
| `PRE` / `SPLIT` / `ARCHIVE_HEAD` | _pending_ |
| Visibility decision (operator, date, rationale, PR) | _pending_ |
| Human-review reference (AC-15) | _pending_ |
| Post-merge `sync` + `now.py` outcome | _pending_ |
| Deviations | _pending_ |

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
