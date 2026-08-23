# Feature Request: deviant-daily On-Demand Publish (Dispatchable Pipeline)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-23), revisions folded
**Effort:** 1 day
**Requested:** 2026-08-23
**First consumer / first event:** the operator, at the moment a roster
change lands. On 2026-08-23 `flux-ultra` was retired and
`flux-2-flex` + `google/nano-banana-2` were added to
`sheikkinen/deviant-daily`; the only way to see either model's output
through the real describe→gate→publish path was to wait for the next
07:00 UTC cron and hope the random draw picked one. The first event is
`gh workflow run publish-now.yml -f model=nano-banana-2 -f dry_run=true`,
run within minutes of the roster commit.

**Prior art:** FR-826 (deviant-daily repo) is the **parent** — this FR
extends its R-3 ledger invariant per slot and its R-4 roster; not a
duplicate, it changes the trigger surface, not the pipeline. FR-822
(DeviantArt publish spike) supplies the API contracts consumed here,
notably refresh-token rotation; already enforced, nothing to re-do.
FR-819 (GitHub-native digest repo) is the precedent for the
Actions-native cron+dispatch pattern and shared concurrency; pattern
reused, not modified. FR-781 (macOS file hook) matches on "deviant"
only as a noun coincidence via its vision/describe precedent — no
overlap. FR-827 (gitclaw forkable runner) and FR-828 (gitclaw Oulu
cookbook) are noun coincidences on "daily/publish" in a different
product line — no overlap. No REJECTED prior art covers this territory.

## Summary

`deviant-daily` can be dispatched manually today, but the dispatch is a
no-op after the day's post exists. Split the ledger's overloaded date
key, extract the pipeline into a reusable workflow, and add a
`publish-now` caller with `dry_run`, `model`, `force`, and `date`
inputs — so the pipeline can be started at will without publishing, on
a chosen model, and can publish an additional post on the same day when
the operator explicitly asks for one.

## Value Statement

The operator can exercise the full pipeline on demand — without
publishing (dry run), targeted (chosen model), and repeatable (forced
extra slot) — instead of waiting a day per observation.

## Problem

Three defects, one root cause.

**Root cause.** `date` is simultaneously the idempotency key, the resume
key, the post filename, and a calendar date. The workflow computes it
itself (`--var date="$(date -u +%F)"`, `.github/workflows/daily.yml`),
so nothing outside can influence it.

1. **Dispatch is a no-op.** `draw_step` calls `entry_for_date`; if a
   same-day record is in `TERMINAL` (`published`/`skipped`), it returns
   `done: true` and the graph routes straight to END. This is correct
   idempotency (FR-826 R-3, witnessed as AC-16 in run `32268278258`)
   but it means that after ~07:03 UTC every manual dispatch burns a
   runner and produces nothing. There is no way to say "yes, I know,
   publish another one".

2. **No model targeting.** `choose_model()` is unconditionally random
   over the roster. A newly added model cannot be exercised on demand;
   the operator waits for the random draw to select it. With three
   actives, the expected wait to witness a specific model is three days.

3. **Every start-up costs a real post.** There is no path that runs
   draw → generate → describe → gate without calling DeviantArt. Testing
   a roster change, a `STYLE-CONTRACT.md` edit, or a describe-prompt
   revision means spending a public gallery post on it.

## Ideal Result

The operator changes something in `deviant-daily` — a model, the style
contract, the describe prompt — and immediately sees what the change
produces, through the real pipeline, without publishing anything and
without waiting for tomorrow. When the output is good and an extra post
that day is genuinely wanted, the same button publishes it as a new
slot, with the same committed-before-side-effect guarantees the cron
path has. The scheduled path is byte-identical to what it is today.
## Proposed Solution

### 0. Normalize every dispatch input at the boundary (R-1)

Workflow and CLI variables arrive as **strings**. `"false"` is truthy in
Python, so a stringly boolean would silently invert `force` and
`dry_run` — the failure mode is a live publish when the operator asked
for a dry run. One helper owns the conversion, called by the
graph-facing step functions before any other work:

```python
# tools/inputs.py
def parse_flag(raw: str | bool, default: bool = False) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw == "":
        return default
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    raise ValueError(f"expected true|false, got {raw!r}")

def parse_date(raw: str) -> str:      # "" -> today; else strict ISO
def parse_slot(raw: str | int) -> int  # non-negative int only
def parse_model(raw: str) -> str      # ""|"random" -> random; else in ACTIVE_MODELS
```

Invalid values raise **before** any ledger write, Replicate call,
Anthropic call, or DA call. `model` validation reuses `RosterError`
rather than inventing a second failure type.

### 1. Split the key: `date` stays a date, `slot` carries the run

Ledger entries gain `slot: int`. Absent means `0` — normalized in
`read_ledger`, at the boundary where the file is parsed, never at call
sites. Non-integer or negative slots are rejected there. The identity
of a run becomes `(date, slot)`, and **no lookup on the publish path
may resolve by date alone** (R-3).

```python
# tools/ledger.py
def read_ledger(path) -> list[dict]:
    ...
    return [_normalize_slot(json.loads(line)) for line in ... ]

def entry_for_slot(entries, date, slot=0) -> dict | None:
    matching = [e for e in entries if e.get("date") == date and e["slot"] == slot]
    return matching[-1] if matching else None

def latest_slot(entries, date) -> int:   # -1 when the date is untouched
    slots = [e["slot"] for e in entries if e.get("date") == date]
    return max(slots) if slots else -1
```

`entry_for_date` is **removed**, not left beside the slot-aware
helper — a date-only lookup surviving next to a slot-aware one is the
defect waiting to be called. `draw_prompt` takes the resolved
`(date, slot)` as resume context instead of deciding by date itself.
Every transition row written by `draw_step`, `gate_step`, and
`publish_step` carries `slot`.

Post path stays `posts/<date>.md` for slot 0 and becomes
`posts/<date>-<slot>.md` above it, so existing posts and existing
ledger rows are untouched and `date` remains parseable as ISO
everywhere. The post markdown records the slot.

### 2. `force` allocates a slot — but resume beats force

```python
def draw_step(date="", force=False, dry_run=False, runner=subprocess.run):
    validate_roster()
    date = date or _today()
    entries = read_ledger(LEDGER)
    slot = latest_slot(entries, date)
    existing = entry_for_slot(entries, date, slot) if slot >= 0 else None

    if existing and existing["status"] not in TERMINAL:
        # An in-flight slot is resumed even under force: stranding it
        # would re-draw a prompt whose 'submitted' row is already committed.
        return {..., "slot": slot, "done": False}
    if existing and not force:
        return {..., "slot": slot, "done": True}      # AC-16 unchanged
    return _draw_new(entries, date, slot + 1 if existing else 0, dry_run, runner)
```

That ordering is the correctness point: `force` may only allocate above
a **terminal** slot. Forcing past a `drawn`-but-not-`published` slot
would abandon a record whose DA submit may already be in flight — the
exact double-publish window FR-826 R-3 exists to close.

### 3. What `dry_run` actually guarantees (R-2)

It is **not free**. It is *no-publication*. Stated exactly:

| Guaranteed absent under `dry_run=true` | Still spent |
|---|---|
| ledger commits (`record_transition`) | Replicate generation tokens |
| post commits, any `git commit`/`push` | Anthropic vision tokens |
| all `da_api` calls (OAuth, submit, publish) | GitHub Actions minutes |
| `gh secret set` (token persistence) | |
| any requirement for DA secrets to be present | |

A no-generate/mock mode that would make dry runs genuinely free is
**out of scope** and needs its own FR (C-7).

Implementation:

- `draw_step`: skips `record_transition`.
- `gate_step`: skips the `skipped` transition commit.
- `publish_step`: returns `{"dry_run": True, "post": post}` **before**
  the missing-secrets check, so a dry run needs no DA secrets at all.
- Workflow uploads the image and the gate's post dict as a run
  artifact, with no token-bearing data in it.

### 4. Workflow structure: one reusable body, two callers

`.github/workflows/_pipeline.yml` (`on: workflow_call`) holds the entire
job — checkout, Python, pip, git identity, `yamlgraph graph run`.
`daily.yml` keeps `schedule` and becomes a caller passing nothing.
`publish-now.yml` exposes the inputs:

```yaml
name: publish-now
on:
  workflow_dispatch:
    inputs:
      dry_run: {type: boolean, default: true}
      model:   {type: choice, default: random,
                options: [random, z-image, flux-2-flex, nano-banana-2, grok]}
      force:   {type: boolean, default: false}
      date:    {type: string,  default: ""}
concurrency:
  group: daily-publish          # MUST match daily.yml — see R-critical below
  cancel-in-progress: false
jobs:
  run:
    uses: ./.github/workflows/_pipeline.yml
    secrets: inherit
    with: {dry_run: ..., model: ..., force: ..., date: ...}
```

`dry_run` defaults to `true`: an accidental dispatch must not publish.

### 5. Graph plumbing

`graph.yaml` gains `model: str`, `dry_run: str`, `force: str` state
fields, passed into the relevant node args. Unset vars resolve to `""`
(yamlgraph `_resolve_variables` falls back to empty string on
`KeyError`), and §0's parsers map `""` to the scheduled default — so
the cron path stays byte-identical. `choose_model(rng=None, name="")`
validates an explicit name against `ACTIVE_MODELS` and raises
`RosterError` on a typo — never a silent fallback to random.

The `graph.yaml` change is **graph authoring** (R-4): it goes through
the governed authoring route, with the authoring report retained as
enforcement evidence, graph lint passing, and smoke runs covering both
the unchanged scheduled path and the dry-run dispatch path. Manual
edits to `graph.yaml` are not authorized.

## Acceptance Criteria

Superseded by the judgement's revised set (2026-08-23); folded verbatim.

- [ ] AC-01: This FR is revised to include strict boundary normalization
      for `dry_run`, `force`, `model`, `date`, and `slot`, honest
      dry-run cost semantics, slot identity across all ledger
      transitions, graph-authoring evidence for target graph changes,
      and the human approval gate for forced live publishing.
- [ ] AC-02: `publish-now.yml` exposes `workflow_dispatch` inputs
      `dry_run` (boolean, default `true`), `model` (choice: `random`
      plus the current `ACTIVE_MODELS` names only), `force` (boolean,
      default `false`), and `date` (string, default `""`).
- [ ] AC-03: `daily.yml` and `publish-now.yml` both call the reusable
      `_pipeline.yml` body and declare the same
      `concurrency.group: daily-publish` with `cancel-in-progress: false`;
      a test parses both workflow files and fails on drift.
- [ ] AC-04: The reusable workflow body preserves the scheduled path:
      daily cron passes no model, force, dry-run, or date override
      beyond today's UTC date, and the unforced slot-0 terminal rerun
      still exits idempotently without DA calls.
- [ ] AC-05: Boundary tests prove empty boolean inputs use scheduled
      defaults, `"false"` is false, `"true"` is true, invalid boolean
      strings fail before side effects, empty/`random` model selects
      randomly, a valid explicit model returns exactly that config, and
      an unknown explicit model raises `RosterError`.
- [ ] AC-06: `dry_run=true` performs zero `record_transition` calls,
      zero `da_api` calls, zero `gh secret set` calls, zero git commits,
      and exits green with all DA secrets absent; fail-fast injected
      runner/session tests prove this.
- [ ] AC-07: A dry-run dispatch that gate-passes uploads a workflow
      artifact containing the generated image and the gate-passing post
      dict, with no credentials or token-bearing data in the artifact.
- [ ] AC-08: `read_ledger()` normalizes every slot-less committed row in
      `state/published.jsonl` to `slot: 0` at read time and rejects
      non-integer or negative slot values.
- [ ] AC-09: Every newly written ledger transition (`drawn`,
      `submitted`, `published`, `skipped`) includes `slot`, and no
      run-selection helper on the publish path resumes or terminates by
      date alone.
- [ ] AC-10: Force semantics are mechanically tested: terminal slot 0
      plus `force=false` returns `done: true`; terminal slot 0 plus
      `force=true` allocates slot 1; terminal slot 1 plus `force=true`
      allocates slot 2; in-flight latest slot plus `force=true` resumes
      that slot and allocates nothing.
- [ ] AC-11: Post paths are slot-aware: slot 0 writes
      `posts/<date>.md`, slot N writes `posts/<date>-<N>.md`, and the
      committed post markdown records the slot.
- [ ] AC-12: Corpus no-repeat remains global across slots: a forced
      extra post cannot reuse any `source_file` already present in the
      ledger for any date or slot.
- [ ] AC-13: With `model`, `dry_run`, and `force` unset, `draw_step` and
      `generate_step` behavior is regression-pinned to the current
      scheduled path: random model selection, date-derived slot 0,
      same-day terminal no-op, and `posts/<date>.md`.
- [ ] AC-14: Governed graph-authoring evidence exists for material
      `graph.yaml` or `prompts/*.yaml` changes in
      `sheikkinen/deviant-daily`, including graph lint and smoke
      validation for the scheduled path and dry-run dispatch path.
- [ ] AC-15: `README.md` in `sheikkinen/deviant-daily` documents both
      workflows and the exact semantics of `dry_run`, `model=random`,
      explicit model names, `force`, date override, slot numbering,
      artifacts, and required secrets.
- [ ] AC-16: Tests are added before implementation for the defects
      above, and the FR records the RED/GREEN evidence or equivalent
      failing-test witness.
- [ ] AC-17: Witness — a real `publish-now` dispatch with
      `dry_run=true` and `model=nano-banana-2` completes green; the FR
      records the run id and artifact contents (PNG plus gate-passing
      post dict), with no DA secret requirement and no DA publish URL.
- [ ] AC-18: Witness — **only after explicit operator approval is
      recorded** (R-5), a real `publish-now` dispatch with `force=true`
      and `dry_run=false` on a date that already has a terminal slot
      publishes a second DA URL and records `slot: 1` or higher in the
      ledger and post markdown.

## Operator approval gate (R-5)

A forced non-dry run creates a **second public DeviantArt post** on a
date that already has one. That is a product and spend decision, not a
judgement decision. Unit and integration tests may cover forced slot
allocation freely; the public second-URL witness (AC-18) must not be
attempted until the operator's approval is recorded here.

**Approval:** _not yet granted._

## Risks

**R-critical: shared concurrency group.** If `publish-now` gets its own
group, a manual run and the cron can overlap. Both call
`refresh_token`; DeviantArt rotates the refresh token on every refresh,
so the second run authenticates with a token the first already
invalidated, and `persist_refresh_secret` races on the repo secret.
This is not a performance concern — it can brick the credential. AC-9
exists to make it mechanically checked rather than reviewed by eye.

**Ledger schema change.** Mitigated by normalizing `slot` in
`read_ledger` (AC-5). No migration of the committed file.

**Corpus no-repeat is unaffected.** `used_source_ids` is global, not
per-day, so a forced extra post cannot repeat a published prompt.

## Alternatives Considered

- **Add inputs to `daily.yml` directly.** Rejected: it mutates the
  workflow whose cron/no-op semantics were witnessed as AC-14/AC-16
  under FR-826, and mixes scheduled and manual audit trails in one run
  list.
- **Duplicate the job body into a second workflow.** Rejected: the
  secrets list, pip line, and git identity would drift silently.
  `workflow_call` keeps one body.
- **Let the operator pass an arbitrary `date` string
  (`2026-08-23-manual`) as the extra-post key.** Rejected: it works
  only because nothing parses `date`, and it poisons the field for any
  future consumer that does. `slot` says what is actually meant.
- **Do nothing; wait for the next cron.** Rejected by the first
  consumer: it is the status quo that made two new models unobservable
  on the day they landed.

## Related

- `feature-requests/FR-826-deviantart-daily-repo.md` — parent FR; R-3
  froze the committed-before-side-effect ledger invariant this FR
  extends per slot, and R-4 froze the roster whose rotation is the
  triggering event.
- `feature-requests/FR-822-deviantart-publish-spike.md` — DA API
  contracts, including refresh-token rotation (the R-critical risk).
- `feature-requests/FR-819-github-native-digest-poc-repo.md` — prior
  art for the Actions-native repo pattern and for freezing
  cron-plus-dispatch concurrency/no-op behavior.
- `sheikkinen/deviant-daily` @ `568df8b` — roster rotation that
  produced the first consumer.
- Implementation lands in the sibling repo `sheikkinen/deviant-daily`,
  not in yamlgraph core. Its `graph.yaml` is modified by this FR;
  **the judge ruled this is graph authoring** (R-4) — the governed
  route applies to the sibling-repo artifact, and manual graph/prompt
  edits are not authorized. The sibling-repo boundary is hard: it is
  never vendored, submoduled, or committed into yamlgraph (C-8).

## Judgement (2026-08-23)

**Verdict:** APPROVED WITH REVISIONS — see
[FR-862-deviant-daily-on-demand-publish.judgement.md](FR-862-deviant-daily-on-demand-publish.judgement.md)
for findings, frozen scope, and the eight enforcement conditions.

Revisions folded into this FR:

| # | Required revision | Where folded |
|---|---|---|
| R-1 | Normalize all dispatch inputs at the boundary — `"false"` is truthy in Python | Proposed Solution §0; AC-05 |
| R-2 | Dry run is *no-publication*, not *free* — it still spends Replicate + LLM tokens | Summary, Value Statement, §3 cost table; AC-06/07 |
| R-3 | Slot identity complete: remove `entry_for_date`, every transition row carries `slot` | §1; AC-08/09/10/11/12 |
| R-4 | Sibling-repo `graph.yaml` change IS graph authoring — governed route applies | §5, Related; AC-14 |
| R-5 | Forced live publish needs recorded operator approval first | Operator approval gate; AC-18 |

**Authority:** activates now that R-1…R-5 are folded (C-1 satisfied).
Enforcement modifies only `sheikkinen/deviant-daily`. Do not re-invoke
the judge while enforcing (C-2).

## Implementation status (2026-08-23)

**Enforced** in `sheikkinen/deviant-daily`, commits `87a03bb` (RED),
`a41de65` (feat), `721bbc8`, `b8fb3fd` (fixes). Suite 124 tests green,
`ruff` clean.

| AC | Status | Evidence |
|---|---|---|
| AC-01 | ✅ | R-1…R-5 folded above |
| AC-02 | ✅ | `.github/workflows/publish-now.yml`; `test_publish_now_input_shape` |
| AC-03 | ✅ | `test_both_callers_share_one_concurrency_group`, `test_both_callers_use_the_reusable_body` |
| AC-04 | ⏳ | `test_daily_passes_no_overrides` green; live cron witness pending 07:00 UTC |
| AC-05 | ✅ | `tools/inputs.py`; `tests/test_inputs.py` (17 cases) |
| AC-06 | ✅ | `Boom` fail-fast runner/session; run 32623376014 committed nothing |
| AC-07 | ✅ | run 32623376014 — "2 files uploaded" (PNG + `dry-run-post.json`) |
| AC-08 | ✅ | `test_read_ledger_normalizes_the_live_committed_ledger` (real file) |
| AC-09 | ✅ | every `record_transition` carries `slot`; `entry_for_date` deleted |
| AC-10 | ✅ | `tests/test_dispatch.py` — all four force cases |
| AC-11 | ✅ | `post_path()`; `- slot:` line in post markdown |
| AC-12 | ✅ | `test_draw_prompt_new_slot_never_reuses_published_source` |
| AC-13 | ✅ | `test_scheduled_path_regression_pin` |
| AC-14 | ✅ | `scripts/author.sh` run; `docs/authoring-{brief,report}-fr862.md` in target repo; lint passed |
| AC-15 | ✅ | `README.md` — Workflows/Inputs/Slots sections |
| AC-16 | ✅ | RED `87a03bb` → GREEN `a41de65`, separate commits |
| AC-17 | ✅ | run 32623139791 (`nano-banana-2`, no DA secrets used, no publish URL) |
| AC-18 | ⛔ | blocked on operator approval (R-5) — not attempted |

### Deviations and findings

1. **Caller permission ceiling.** The first dispatch died at
   `startup_failure` with no job logs. A called workflow cannot
   escalate beyond its caller's permissions, and moving the job body
   out of `daily.yml` moved `permissions: contents: write` with it.
   Both callers now declare the ceiling, pinned by
   `test_callers_declare_the_write_ceiling` (`721bbc8`).
2. **AC-07 was under-specified by me, not by the judge.** The first
   green dry run uploaded only the PNG — the post dict existed only in
   the run log. `publish_step` now writes
   `outputs/dry-run-post.json` on dry runs (`b8fb3fd`).
3. **Third dispatch gate-skipped at `confidence: medium`** and
   therefore produced no post dict — correct behaviour, and an
   incidental witness that a dry-run skip commits nothing.
4. **Authoring wrapper reports a contract violation for sibling-repo
   targets.** `author.sh` checks that a listed artifact exists under
   its own workdir; the artifact was `deviant-daily/graph.yaml`.
   Verified by artifact per the adapter README ("never by exit code"):
   diff correct, `yamlgraph graph lint` passed. Worth a follow-up FR if
   sibling-repo authoring recurs.
