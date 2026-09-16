# Feature Request: FR-1049 opencode judge variant — third backend in the sole-route judge adapter

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 day + two live judge runs (R-4)
**Requested:** 2026-09-16
**First consumer / first event:** an operator whose only agent is opencode
(provider keys in `~/.local/share/opencode/auth.json`, no Copilot seat, no
Claude subscription — the FR-1048 payer profile) runs `JUDGE_BACKEND=opencode
scripts/judge.sh feature-requests/<some-FR>.md` and reads a draft verdict
rendered by opencode. Without this FR, that operator has **no** judge route at
all: the sole-route adapter pins `gpt-5.6-sol` (Copilot seat) and
`claude-opus-5` (Claude subscription), both of which they do not hold.
**Research:** in-body dispositioned alternatives table below with a *Dissent*
column (FR-960 / FR-889 in-body-precedent).
**Evidence:** [evidence/FR-1049-opencode-judge-write-probe.md](evidence/FR-1049-opencode-judge-write-probe.md)
— committed raw capture on the pinned `1.18.31` proving the one load-bearing
fact this FR depends on: opencode headless `write` auto-completes with no
permission flag, so the judge can write its own draft through the existing
FR-1048 backend with a bare `model` pin. (The write-probe was captured on
`inception/mercury-2.5`; the H-1 model is `deepseek/deepseek-v4-pro`. The
`write` auto-approval is a CLI-level permission default, independent of the
LLM model — the probe evidences the mechanism, not a model-specific behavior.)
**Prior art:**
- [FR-960](FR-960-claude-judge-variant.md) [Implemented] — the structural
  template this FR follows 1:1: second-backend node inside the one graph,
  per-backend-per-FR artifact, closed-set wrapper validation before the lock,
  committed witness with a dual-run claim inventory and human payer-boundary
  signature. **This FR is the FR-960 analogue that FR-1048 deferred** (FR-1048
  "Out of Scope": "a separate FR if a consumer swaps onto this backend (the
  FR-960 analogue)"). It differs in one load-bearing way: opencode needs no
  tool/permission flags (see the write-probe §2.3), so the node's `cli_flags`
  is a single `model` pin — not Copilot's `allow_all_tools`, not Claude's
  `--tools`/`--allowedTools`.
- [FR-1048](FR-1048-opencode-cli-backend.md) [Implemented] — the backend this
  FR consumes. Hard precondition (FR-960 R-1 analogue): FR-1048 is Implemented
  on main, its evidence and live witness exist, before any graph/wrapper/test
  work. Its [evidence](evidence/FR-1048-opencode-cli-probe.md) pins the
  `provider/model` grammar, the JSONL state machine, and the version-only
  preflight this FR's node rides on.
- [FR-959](FR-959-claude-cli-backend-primitive.md) [Implemented] — the claude
  backend analogue; its `--tools`/`--allowedTools` approval surface has **no
  opencode counterpart** (write-probe §2.3), which is the FR's central claim.
- [FR-958](FR-958-claude-code-cli-backend-for-copilot-node.md) [SPLIT] —
  parent of FR-960; same lineage, different backend.
- [FR-546](FR-546-opencode-copilot-backend.md) [Judged, never enforced] — the
  opencode server/SDK route, superseded by FR-1048 for the backend name. This
  FR rides the CLI route; the server/SDK route is not revived.
- FR-1022 / FR-1025 — noun matches only (`judge` round sentinel; retire the
  research provenance ledger). Unaffected by this FR. Dismissed.

## Summary

Add a `judge_opencode` node (`backend: opencode`, FR-1048) to
`.github/skills/judge-fr/adapters/graph.yaml`, selected by the same `backend`
state variable through conditional edges, so the graph stays the one route.
`scripts/judge.sh` grows its closed backend set from `copilot|claude` to
`copilot|claude|opencode`; the per-backend-per-FR artifact path already handles
the third backend with no change. The opencode node's `cli_flags` is a single
`model` pin — **no tool or permission flag is mapped by FR-1048 and none is
added here** (R-2): opencode 1.18.31 *does* expose the broad `--auto`
permission flag, but FR-1048 deliberately leaves it unmapped, and the committed
write-probe proves a **workspace-local** `write` auto-completes under the
**probed default configuration** — not a universal permission contract. An
operator configuration that denies `write` fails loudly through the wrapper's
artifact contract (a supported outcome, not a silent fallback). The
admission cost is one routing-condition change: the Copilot edge's catch-all
`backend != "claude"` must become explicit `backend == "copilot"`, because a
third value would otherwise match the catch-all and silently misroute to the
Copilot node (the expression router returns on first match).

## Value Statement

An operator with only provider keys gets a judge route for the first time
(`forced_opposite`, `model_as_trusted_peer`): the same doctrine, rendered
through a third harness with a third payer, into its own draft artifact, cross-
examinable against the Copilot and Claude drafts.

## Problem

1. **No route for the provider-key operator.** The sole-route judge adapter has
   exactly two backend nodes — `judge` (`gpt-5.6-sol`, Copilot seat) and
   `judge_claude` (`claude-opus-5`, Claude subscription). An operator holding
   neither seat nor subscription (the FR-1048 consumer profile) cannot run the
   judge route at all. FR-1048 made opencode a first-class copilot-node
   backend; this FR is its judge-route consumer.
2. **The catch-all edge is a third-value trap.** The Copilot edge's condition is
   `backend != "claude"` (FR-960). `make_expr_router_fn` evaluates conditions in
   order and returns on the **first** match (`yamlgraph/routing.py:91-108`). A
   third value `opencode` satisfies `!= "claude"` and would route to the
   Copilot node, silently billing the Copilot seat — the exact silent-
   default the closed-set validation exists to prevent. The edge must be made
   explicit before any third value is admitted.
3. **The tool-permission question is already answered, and the answer is
   cheaper than the Claude case.** Copilot needed `allow_all_tools` (NC-414:
   denial is silent and exits 0); Claude needed `--tools`/`--allowedTools`
   (FR-960). opencode needs no *mapped* flag: its workspace-local `write`
   auto-completes under the probed default configuration (write-probe §1/§2).
   The broad `--auto` flag exists in the CLI (`--help` §7) but is deliberately
   unmapped by FR-1048 and is not added here (R-2). This FR must not invent a
   permission flag that FR-1048 deliberately never mapped.

## Ideal Result

`scripts/judge.sh <fr>` behaves exactly as today.
`JUDGE_BACKEND=opencode scripts/judge.sh <fr>` renders the same doctrine
through opencode, with the write-probe's workspace-local auto-approved file
tools (under the probed default configuration — R-2), on the provider key, into `tmp/draft-judgement-opencode-<fr-slug>.md`. Running it
alongside the default backend on one FR and inventorying the drafts is the
same documented ritual FR-960 established, now three-way. No permission flag,
no backend change to FR-1048, no `CopilotResult` change — the node is a `model`
pin and a routing edge.

## Proposed Solution

### 1. Adapter graph (graph authoring route only; FR-960 R-2 / C-3 analogue)

The edit MUST go through `scripts/author.sh` with a committed brief
`feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md`
(deliverable D-2, written at enforce). The brief names the artifact boundary
(`.github/skills/judge-fr/adapters/graph.yaml`; the prompt is **unchanged** —
`prompts/judge.yaml` already interpolates `{{ artifact_path }}` and needs no
edit), the existing FR-960 adapter as precedent, the exact edits below, the
lint command, a narrow mocked smoke, and the report contract. Target YAML:

```yaml
state:
  fr_path: str
  backend: str            # "copilot" | "claude" | "opencode"; wrapper always sets it
  artifact_path: str      # wrapper-computed per-backend-per-FR path (FR-960)
  judge_result: dict

nodes:
  select:
    type: passthrough
    output: {}
  judge:                  # unchanged Copilot node, model gpt-5.6-sol
    type: copilot
    backend: cli
    cli_flags:
      model: gpt-5.6-sol
      allow_all_paths: true
      allow_all_tools: true
    prompt: judge
    variables: { fr_path: "{state.fr_path}", artifact_path: "{state.artifact_path}" }
    state_key: judge_result
    timeout: 600
  judge_claude:           # unchanged (FR-960)
    type: copilot
    backend: claude
    cli_flags:
      model: claude-opus-5
      tools: [Read, Glob, Grep, Write]
      allowed_tools: [Read, Glob, Grep, Write]
      max_turns: 40
    prompt: judge
    variables: { fr_path: "{state.fr_path}", artifact_path: "{state.artifact_path}" }
    state_key: judge_result
    timeout: 600
  judge_opencode:         # NEW — the whole feature
    type: copilot
    backend: opencode
    cli_flags:
      model: deepseek/deepseek-v4-pro   # provider/model; compile-time fail-closed (FR-1048 §5); H-1 value (R-1)
    prompt: judge                     # SAME prompt file (NC-412 zero duplication)
    variables: { fr_path: "{state.fr_path}", artifact_path: "{state.artifact_path}" }
    state_key: judge_result
    timeout: 600

edges:
  - { from: START, to: select }
  - { from: select, to: judge,          condition: backend == "copilot" }   # was != "claude" (FR-960); see §1 note
  - { from: select, to: judge_claude,   condition: backend == "claude" }
  - { from: select, to: judge_opencode, condition: backend == "opencode" }
  - { from: judge, to: END }
  - { from: judge_claude, to: END }
  - { from: judge_opencode, to: END }
```

**Routing-condition note (load-bearing).** The Copilot edge condition changes
from `backend != "claude"` to `backend == "copilot"`. This is required, not
cosmetic: the expression router returns on first match, so a catch-all `!=`
would swallow `opencode` into the Copilot node. The three `==` conditions are
mutually exclusive and order-independent. The wrapper's default (`copilot`) and
closed-set validation mean `backend` is always one of the three values when
invoked through the wrapper; a direct graph invocation with `backend` unset
now falls through to no-match → END and produces no artifact (the wrapper's
artifact contract then fails loudly with exit 65), which is honest rather than
silently defaulting. `doctrine.md` and `judgement.template.md` and the prompt
are untouched.

No `allow_all_tools`, no `tools`, no `allowed_tools`, no `auto`, no `agent`,
no permission flag of any kind on the opencode node (write-probe §2.3). The
opencode backend rejects those keys as extras (`OpenCodeCliFlags`, `extra=
"forbid"`) anyway — they are not mapped and must not be invented here.

### 2. Wrapper (`scripts/judge.sh`)

- `case "$BACKEND" in copilot|claude|opencode) ;;` — the third value in the
  closed set; anything else still exits 64 before the lock.
- Usage string: `[JUDGE_BACKEND=copilot|claude|opencode]`.
- Artifact path `tmp/draft-judgement-${BACKEND}-${FR_SLUG}.md` is already
  per-backend-per-FR (FR-960); `opencode` slots in with zero change.
- Nothing else changes: lock, sentinels, executor resolution, artifact
  contract, round sentinel (FR-1022) all untouched.

### 3. README, SKILL, ramp mirror (the FR-960 §3 + the CI trap it hit)

- `adapters/README.md` gains: the third backend and its closed set; that the
  opencode node has **no** tool/permission flag and why (write-probe §2.3),
  stated precisely (R-2) — `--auto` exists in the CLI but is deliberately
  unmapped, a workspace-local `write` succeeded under the probed default
  configuration, and an operator configuration denying `write` fails through
  the artifact contract; that it bills the operator's provider key through
  FR-1048's compile-time model requirement (link FR-1048's payer boundary, do
  not restate it); the routing-condition note.
- `SKILL.md`'s "one judge to rule them all" paragraph ("Since FR-960 the
  adapter graph carries two backend nodes …") becomes three backend nodes.
- **Ramp mirror (FR-960's CI failure):** `ramp/assets/tier2/github/skills/judge-fr/SKILL.md`
  is byte-mirrored via `ramp/manifest.yaml` `mirror_exact` — the §3 SKILL.md
  edit must be re-copied there or CI's `test_mirror_exact_entries_match_live_bytes`
  fails. `ramp/assets/tier2/scripts/judge.sh` is a *curated* copy (not
  byte-tested) and stays pre-FR-1049; refreshing it is the ramp owner's
  adjacent work, not folded here.

### 4. Witness record — `feature-requests/evidence/FR-1049-opencode-judge-witness.md`

Committed, one section per live run, mirroring FR-960 §4:

| Field | Content |
|---|---|
| Authoring proof | `scripts/author.sh` command and brief path, digest of the local `tmp/draft-authoring-report.md` (not committed), quoted required sections, lint/smoke results, graph commit SHA, limitations |
| Run | target FR path and commit SHA, backend `opencode`, `opencode --version` (the FR-1048 version-only preflight), resolved model as the `--model` argv (the only payer signal — FR-1048 §8), `JUDGE_BACKEND`, start/end timestamps, artifact path and sha256, verdict header line, and the effective permission/config limitation (R-2) |
| Dual-run inventory | `CP-n` (Copilot draft) vs `OC-n` (opencode draft) IDs with `matched` / `contradicted` / `backend-only` dispositions, or the literal convergence sentinel `no backend-only or contradicted items` |
| Signature | two separate dated lines by humans other than the enforcer (R-3): (1) "Enforcement-infrastructure diff and route invariants accepted by <name>, <date>"; (2) "Residual opencode provider-key payer boundary (FR-1048 §5) accepted for judge execution by <name>, <date>" — the second signed by the spend owner |
| Limitations | anything not exercised |

### 5. Tests — `tests/unit/test_fr1049_opencode_judge_variant.py`, marked `process`, every test `@pytest.mark.req("REQ-YG-682")`

- Wrapper, stubbed `YAMLGRAPH_BIN` (pattern of `test_fr758_judge_review_wrappers.py`
  / `test_fr960_claude_judge_variant.py`): exact argv for unset, `copilot`,
  `claude`, and `opencode`; `opencode` passes `--var backend=opencode`; a
  typo (e.g. `opncode`) exits 64 with no lock and no launch; artifact path is
  `tmp/draft-judgement-opencode-<fr-slug>.md`; a pre-existing other-backend and
  other-FR draft survive an opencode run; a second opencode run replaces only
  its own draft; verdict-line verification unchanged; no real judge launch.
- Graph routing, mocked `subprocess.run`: `backend=opencode` visits only
  `judge_opencode`; `copilot` only `judge`; `claude` only `judge_claude`;
  the opencode node's captured argv is `opencode run <prompt> --format json
  --model deepseek/deepseek-v4-pro` with **no** `--tools`, `--allowedTools`,
  `--auto`, `--agent`, or permission flag; and the pre-existing FR-960 routing
  assertions still hold.

### 6. Traceability

- **REQ-YG-682** (provisional, re-derived at enforce) folded into
  `capabilities/CAP-211-sole-route-judge-review.yaml` with `fr: FR-758, FR-960,
  FR-1022, FR-1049` and the new test + graph modules.
- `ARCHITECTURE.md` regenerated; `python scripts/req_coverage.py --strict`.
- Changelog fragment `changelog/unreleased/fr-1049-opencode-judge-variant.md`
  (`type: feat`, `scope: judge`, `req: REQ-YG-682`).
- Diary entry under `docs/diary/` with a **Seed**.

### Requirements (ADR-001; provisional id)

- **REQ-YG-682** — Judge adapter supports a third backend (`opencode`, FR-1048)
  inside the one graph via mutually exclusive state-conditioned edges (`==
  "copilot"` / `== "claude"` / `== "opencode"`); the opencode node's
  `cli_flags` is a single compile-time-fail-closed `provider/model` pin and
  carries **no** tool or permission flag; `scripts/judge.sh` admits `opencode`
  in the closed set, still exits 64 on any other value before the lock, and
  derives the per-backend-per-FR artifact path unchanged; each live run is
  recorded in a committed witness with a dual-backend claim inventory and the
  provider-key payer-boundary human signature.

## Acceptance Criteria

Offline:

- [ ] AC-01 (C-2): FR-1048 is Implemented on main, its evidence and live
  witness exist, and its kill criterion has not fired, before any graph /
  wrapper / test / doc work begins.
- [ ] AC-01b (R-1, H-1): a named human spend owner has selected the exact
  `provider/model` (recorded as H-1 with chooser + date in the FR); the graph
  target, argv test, REQ-YG-682, docs, and witness all use that one value, and
  no implementation default or unpinned option remains. Enforcement never
  substitutes a model.
- [ ] AC-02 (C-3): `feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md`
  is committed, cited here, and names the artifact boundary, precedent,
  expected edits, lint, narrow smoke, and report contract.
- [ ] AC-03 (C-3): `scripts/author.sh <brief>` produces a non-empty local
  `tmp/draft-authoring-report.md` with the required headings; the witness
  records its digest, quoted required sections, lint/smoke results, graph
  commit SHA, and limitations; nowhere claims the report is committed.
- [ ] AC-04: `yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml`
  → 0 errors; a REQ-YG-682 routing test proves `copilot`→only `judge`,
  `claude`→only `judge_claude`, `opencode`→only `judge_opencode`, all three
  receive the same `judge` prompt and the requested `artifact_path`.
- [ ] AC-05: the Copilot and Claude nodes and the `judge` prompt are byte-
  unchanged except the Copilot edge condition `!= "claude"` → `== "copilot"`.
- [ ] AC-06: the opencode node's captured argv is
  `["opencode", "run", <one prompt element>, "--format", "json", "--model", "deepseek/deepseek-v4-pro"]`
  with no `--tools`, `--allowedTools`, `--auto`, `--agent`, permission flag,
  resume flag, or shell.
- [ ] AC-07: stubbed wrapper tests prove unset and `copilot` select the Copilot
  branch, `claude` the Claude branch, `opencode` the opencode branch, any other
  value exits 64 before lock creation, and the exact `--var backend=…` /
  `--var artifact_path=…` arguments are passed.
- [ ] AC-08: wrapper tests prove the path is `tmp/draft-judgement-opencode-<fr-slug>.md`;
  a run replaces only that path; other-backend and other-FR artifacts survive;
  a same-backend same-FR rerun replaces its own artifact.
- [ ] AC-09: `adapters/README.md`, `SKILL.md`, and the ramp `SKILL.md` mirror
  reflect the third backend per §3; `doctrine.md` and `judgement.template.md`
  and `prompts/judge.yaml` are unchanged (diff empty).
- [ ] AC-10: CAP-211 carries REQ-YG-682 and FR-1049 provenance;
  `ARCHITECTURE.md` regenerated; every new test tagged
  `@pytest.mark.req("REQ-YG-682")`; changelog fragment carries `req: REQ-YG-682`;
  `python scripts/req_coverage.py --strict` passes.

Live (each recorded in the witness; pytest and CI never launch a judge;
R-4 — AC-11 and AC-12 together are **two** live judge runs on the **same
comparison witness host**, which must hold **both** the H-1 opencode provider
key **and** a working Copilot entitlement; the named provider-key-only consumer
needs only the opencode route once it is operational):

- [ ] AC-11 (C-8): `JUDGE_BACKEND=opencode scripts/judge.sh <FR>` on the
  comparison witness host (opencode 1.18.31 + the H-1 provider key) writes
  `tmp/draft-judgement-opencode-<slug>.md` with a `**Verdict:**` line; the
  witness records target FR path/commit, backend, `opencode --version`, the
  resolved `--model` argv, timestamps, artifact path/hash, verdict, and the
  effective permission/config limitation (R-2).
- [ ] AC-12: the default backend run on the same FR, same host, with a working
  Copilot entitlement, writes `tmp/draft-judgement-copilot-<slug>.md`; both
  files exist afterwards with distinct hashes or an explicitly recorded
  equality.
- [ ] AC-13: the witness inventories both drafts per §4; every item has a
  source location, evidence citation, and disposition; convergence uses the
  literal sentinel, never an empty table.
- [ ] AC-14 (C-7/C-8): **two** separate dated approvals by humans other than the
  enforcer (§4, R-3) — the enforcement-infrastructure diff/route invariants,
  and the provider-key payer boundary (signed by the spend owner) — are given
  before the opencode route is operational or this FR is marked Implemented.
- [ ] AC-15: the diary entry exists with a Seed; all REQ-YG-682 tests and the
  existing judge-wrapper/model-pin tests pass without launching a real judge.

## Alternatives Considered (with dissent preserved)

| Alternative | Probe (2026-09-16) | Disposition | Dissent |
|---|---|---|---|
| Add a `judge_opencode` node (this FR) | write-probe §1/§2: headless `write` auto-completes; FR-1048 maps only `model`/`resume` | CHOSEN — a `model` pin + one routing edge, no backend change | opencode's default-permission auto-approve is a *default*, not a *contract*: an operator's `opencode.json` could deny `write`, silently breaking the draft write exactly as NC-414 warned for Copilot. The node should carry an explicit permission, not trust the ambient default. |
| Extend `OpenCodeCliFlags` with a permission flag (`auto` → `--auto`) | `--help` §7 shows `--auto` "auto-approve permissions… (dangerous!)" | REJECTED for v1 — `--auto` is a broad bypass ("dangerous"), not a scoped `--allowedTools`; a scoped permission flag does not exist in the pinned CLI; and the write-probe proves the default suffices | A broad bypass is still the *explicit* contract Copilot/Claude nodes carry; trusting the ambient default is trusting vendor behaviour with no diff in the repo. If a judge write fails in the wild, the cure is a scoped flag FR, not a bypass. |
| Route opencode via the existing `judge` node by changing `model:` only | FR-960 rejected this for Claude ("same harness, same seat") | REJECTED — `backend: cli` bills the Copilot seat, which the consumer does not hold | Cheapest possible third opinion; but it does not solve the problem (the operator has no Copilot seat) and would silently bill a seat on misroute. |
| Fold opencode into `scripts/review.sh` too | `review.sh` shares the pattern | DEFERRED — FR-960 also deferred review/author migration; separate FR after the first witness | Symmetry would be cheap now; but each route needs its own witness + payer signature, and bundling them is scope creep (judgement SPLIT discipline). |
| Do nothing; the operator uses the Claude or Copilot route | the operator holds neither | REJECTED — leaves a named consumer (FR-1048 §first-consumer) with no judge route | The judge is advisory and the human can always judge by hand; a third automated brain is `growth_as_default` unless a real FR needs cross-examination. This FR's consumer test answers it: the operator has no route at all. |

Is this a graph? The judge selection is already inside a graph (three nodes, one
prompt, one wrapper). The three-way comparison is not yet a graph, on purpose
(FR-960's last-row deferral still stands).

## Kill criterion

If AC-11 cannot be witnessed on this host because opencode headless does **not**
write the draft artifact with a verdict line (e.g. the operator's opencode
configuration denies `write`, or the stream fails the FR-1048 state machine),
REJECT this FR with the log attached. No `--auto`, no permission-flag
invention, no Copilot/Claude fallback, and no weakened model-explicit claim
rescues the witness.

## Constraints

- opencode backend flags stay `model`/`resume` only (FR-1048); no
  `OpenCodeCliFlags` change, no `CopilotResult` change, no `copilot_runtime_*`
  change.
- The `judge` prompt and `doctrine.md` are untouched; the only graph edit is
  the new node, the three explicit edges, and the Copilot edge condition.
- The opencode node's `model` must match `^[^/\s]+/[^/\s]+$` (FR-1048 §5) —
  a bare model name like `gpt-5.6-sol` is invalid for this backend. The pin is
  the H-1 value `deepseek/deepseek-v4-pro`, selected and dated by the human
  spend owner (R-1); enforcement never substitutes a model.
- Copilot, Claude, and the review route are unchanged; `backend: sampling` and
  streaming are untouched.
- New module under 400 lines (a test file); graph edits via `scripts/author.sh`
  only.
- Not authorized: FR-546's server/SDK route; a permission/`auto` flag; a
  `CopilotResult` field change; migrating `review.sh`/`author.sh`/`research.sh`;
  changing the default backend; CI/pytest execution of a real judge; any
  expansion of the advisory output boundary.

## Out of Scope

- FR-546's server/SDK route (superseded, not revived).
- Migrating `scripts/review.sh` / `scripts/author.sh` / `scripts/research.sh`
  to opencode — separate FRs after the first committed witness.
- A scoped opencode permission flag (a new `OpenCodeCliFlags` key) — only if a
  judge write fails in the wild (the first dissent row).
- Changing the default judge backend or the `gpt-5.6-sol` / `claude-opus-5`
  pins.
- A fourth judge backend (Codex, Gemini CLI) — still no consumer.

## Related

- `.github/skills/judge-fr/adapters/graph.yaml`, `adapters/prompts/judge.yaml`,
  `adapters/README.md`, `SKILL.md`, `scripts/judge.sh`,
  `capabilities/CAP-211-sole-route-judge-review.yaml`,
  `ramp/assets/tier2/github/skills/judge-fr/SKILL.md`
- [evidence/FR-1049-opencode-judge-write-probe.md](evidence/FR-1049-opencode-judge-write-probe.md)
- [evidence/FR-1048-opencode-cli-probe.md](evidence/FR-1048-opencode-cli-probe.md),
  [evidence/FR-1048-opencode-backend-witness.md](evidence/FR-1048-opencode-backend-witness.md)
- `feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md`
  (D-2, pending)

## Judgement

Round 1 (2026-09-16, sole route `scripts/judge.sh`, Copilot CLI `gpt-5.6-sol`):
**APPROVED WITH REVISIONS** — R-1 (fold the human model/spend decision H-1),
R-2 (precise permission boundary: `--auto` exists but is unmapped; workspace-
local `write` succeeded under the probed default configuration), R-3 (two
separate human signatures: enforcement-infrastructure + provider-key payer),
R-4 (effort is two live runs; comparison witness host needs both the opencode
provider key and a Copilot entitlement). R-2/R-3/R-4 folded; at round 1, R-1
was **not** folded — H-1 is a human spend decision and remained pending until
the spend owner answered it (folded 2026-09-16, below).

Round 2 (2026-09-16, same route): **APPROVED WITH REVISIONS** — single
remaining revision R-1 (round 2): the human spend owner must record a named,
dated acceptance of `deepseek/deepseek-v4-pro` (or one replacement exact
`provider/model`), and the FR must not claim R-1 is folded until that decision
exists.

### Human decisions (R-1 — FOLDED 2026-09-16)

- **H-1 (spend/provider): which `provider/model` does the opencode judge pin?**
  - **Decision: `deepseek/deepseek-v4-pro`.**
  - **Chooser / date:** Sami Heikkinen (spend owner), 2026-09-16.
  - Evidence: `opencode models` (FR-1048 probe §8) lists
    `deepseek/deepseek-v4-pro`; the provider-key payer is the operator's
    `~/.local/share/opencode/auth.json`. The author proposed the value; the
    spend owner selected it; enforcement never substitutes a model (R-1).

## Implementation Status

- 2026-09-16: Proposed. Raw write-probe captured (headless workspace-local
  `write` auto-completes under the probed default configuration) and promoted
  to `evidence/FR-1049-opencode-judge-write-probe.md`. No code written.
- 2026-09-16: Judged APPROVED WITH REVISIONS (round 1). Revisions folded:
  R-2 (precise permission boundary — `--auto` exists but is unmapped;
  workspace-local `write` succeeded under the probed default configuration;
  denying config fails through the artifact contract); R-3 (two separate human
  signatures — enforcement-infrastructure and provider-key payer); R-4 (effort
  is two live runs; comparison witness host needs both the opencode provider
  key and a Copilot entitlement). R-1 (H-1 model/spend decision) was a human
  decision and remained pending at round 1 (folded 2026-09-16, below).
- 2026-09-16: Judged APPROVED WITH REVISIONS (round 2). Single remaining
  revision R-1 (round 2): the human spend owner must record a named, dated
  acceptance of `deepseek/deepseek-v4-pro` (or one replacement exact
  `provider/model`), and the FR must not claim R-1 is folded until that
  decision exists.
- 2026-09-16: R-1 folded — the human spend owner (Sami Heikkinen) selected
  `deepseek/deepseek-v4-pro` on 2026-09-16; the value is used consistently in
  §1 (graph target), §5 (argv), §6, Constraints, AC-06/AC-07/AC-11, and H-1.
  Awaiting re-judgement.
