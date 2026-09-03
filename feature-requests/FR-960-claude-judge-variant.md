# Feature Request: FR-960 Claude judge variant — second backend in the sole-route judge adapter

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** **Enforcing 2026-09-03** on branch `feat/fr-960-claude-judge-variant` (judged 2026-09-02 — APPROVED WITH REVISIONS, [judgement](FR-960-claude-judge-variant.judgement.md); R-1..R-6 folded). Gate C-2 satisfied: FR-959 merged to main in PR #563 (`82356118`) with its committed auth probe and live witness; its kill criterion did not fire. Authoring brief (D-2): [authoring-briefs/fr-960-claude-judge-variant-brief.md](authoring-briefs/fr-960-claude-judge-variant-brief.md).
**Effort:** 0.5 day + two live judge runs
**Requested:** 2026-09-02
**First consumer / first event:** the operator runs `JUDGE_BACKEND=claude scripts/judge.sh feature-requests/<some-FR>.md` and reads a draft verdict rendered by Claude Code; the same afternoon the same FR is judged with the default backend and the two drafts are inventoried claim by claim in a committed witness (§4). That inventory is the deliverable; the second judge exists to produce it.
**Research:** in-body dispositioned alternatives table below with a *Dissent* column (FR-958 judgement R-7).
**Prior art:**
- [FR-958](FR-958-claude-code-cli-backend-for-copilot-node.md) [SPLIT] / [judgement](FR-958-claude-code-cli-backend-for-copilot-node.judgement.md) — parent; this FR is D-2 and folds R-2 (judge argv), R-3 (payer boundary as consumed), and R-7 (persistent witness). It inherits the judgement's AC-12..AC-17 and C-2, C-3, C-4, C-7, C-8.
- [FR-959](FR-959-claude-cli-backend-primitive.md) [Judged — APPROVED WITH REVISIONS 2026-09-02] — the backend this FR consumes. **Hard precondition for every deliverable below except this FR's own text** (judgement R-1). Its [evidence](evidence/FR-959-claude-auth-probe.md) pins the `--tools` comma grammar this FR relies on.
- NC-412 / NC-414 / NC-415 (recorded in `.github/skills/judge-fr/adapters/README.md` and `scripts/judge.sh`) — sole-route judge, artifact-not-exit-code contract, OS lock. Preserved: one graph, one wrapper; the second backend is a node inside the graph, not a second route.
- [FR-758](FR-758.judgement.md) / CAP-211 (`capabilities/CAP-211-sole-route-judge-review.yaml`) — owns the sole-route wrapper and adapter contract and `tests/unit/test_fr758_judge_review_wrappers.py`; REQ-YG-642 folds into it (judgement R-4).
- FR-305 (`.chaplain/graphs/watcher-plan/step-judge-v2.yaml`) — lineage of the adapter graph; already runs a Claude *model* through Copilot. Distinguished: this FR changes harness and payer, not weights.
- CAP-44 (judge SPLIT verdict, REQ-YG-143) — judge prompt contract; untouched (the Claude node shares the same prompt file).

## Summary

Add a `judge_claude` node (`backend: claude`, FR-959) to
`.github/skills/judge-fr/adapters/graph.yaml`, selected by a `backend`
state variable through conditional edges so the graph stays the one route.
`scripts/judge.sh` passes `--var backend=${JUDGE_BACKEND:-copilot}` and
writes a **per-backend-per-FR artifact path** so two backends can judge the
same FR, and two FRs can be judged back to back, without deleting each
other's drafts (a same-backend rerun on the same FR deliberately replaces its
own earlier draft). The Claude node restricts available tools to
`Read, Glob, Grep, Write` with `--tools` and auto-approves exactly that set;
no bypass flag. Every live run leaves a committed witness with backend, CLI
version, auth mode, timestamps, artifact hashes, and, for the dual run, a
claim-by-claim inventory of both drafts with `matched` / `contradicted` /
`backend-only` dispositions.

## Value Statement

The chaplain gets a second judge with a different harness, instruction
loader, and payer, so a verdict can be cross-examined instead of trusted
(`forced_opposite`, `model_as_trusted_peer`).

## Problem

1. **One brain.** The adapter pins `gpt-5.6-sol` via Copilot
   (`adapters/graph.yaml:23`). The only variation available is `model:`,
   which changes weights but not harness, tools, or how doctrine is loaded.
2. **Shared artifact path.** `scripts/judge.sh` does `rm -f tmp/draft-judgement.md`
   at start and every run writes the same file. Raw record, 2026-09-02:
   FR-958's run verified its artifact at 18:57:49 local (`tmp/judge-fr958.log`);
   a sibling session's run started at 18:57:52 (`tmp/.judge.lock/holder`,
   `tmp/judge-fr955-957.log`) and deleted it. The verdict survived only in
   the Copilot session transcript. The FR-959 and FR-960 judgements of
   2026-09-02 each had to `cp` the draft in the same shell command as the
   wrapper to be safe. This FR's own AC-14 (two backends, same FR) would
   collide the same way by design.
3. **Over-broad judge permissions.** The current node needs
   `allow_all_tools: true` because Copilot CLI otherwise exits 0 while
   denying the file write (NC-414). Claude's print mode has separate
   availability and approval controls, so the judge can have exactly the
   four tools its contract needs.

## Ideal Result

`scripts/judge.sh <fr>` behaves exactly as today. `JUDGE_BACKEND=claude
scripts/judge.sh <fr>` renders the same doctrine through Claude Code, with
four tools, on the subscription, into its own artifact file. Running both on
one FR and inventorying the drafts is a documented ritual with a committed
record. Whether the drafts converge or diverge, the inventory says so
explicitly: convergence is valid evidence (recorded with a sentinel), and a
`contradicted` or `backend-only` row is the most useful line in either draft.

## Proposed Solution

### 1. Adapter graph (graph authoring route only; judgement R-2, C-3)

The edit MUST go through `scripts/author.sh` with the committed brief
`feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md`
(deliverable D-2; written and committed only after FR-959 is Implemented,
per R-1). The brief names the artifact boundary
(`.github/skills/judge-fr/adapters/graph.yaml`,
`.github/skills/judge-fr/adapters/prompts/judge.yaml`), the existing judge
adapter as precedent, the exact expected edits below, the lint command, a
narrow mocked smoke, and the report contract. The YAML below is the brief's
target, not a hand edit:

```yaml
state:
  fr_path: str
  backend: str            # "copilot" | "claude"; wrapper always sets it
  artifact_path: str      # wrapper-computed per-backend-per-FR path (see §2)
  judge_result: dict

nodes:
  select:
    type: passthrough
  judge:                  # unchanged Copilot node, model gpt-5.6-sol
    type: copilot
    backend: cli
    cli_flags: { model: gpt-5.6-sol, allow_all_paths: true, allow_all_tools: true }
    prompt: judge
    variables: { fr_path: "{state.fr_path}", artifact_path: "{state.artifact_path}" }
    state_key: judge_result
    timeout: 600
  judge_claude:
    type: copilot
    backend: claude
    cli_flags:
      model: opus                          # alias; exact id pinned in the witness
      tools: [Read, Glob, Grep, Write]     # availability (FR-959 `--tools`, comma grammar per its evidence §4)
      allowed_tools: [Read, Glob, Grep, Write]   # approval for the same set
      max_turns: 40
    prompt: judge                          # SAME prompt file (NC-412 zero duplication)
    variables: { fr_path: "{state.fr_path}", artifact_path: "{state.artifact_path}" }
    state_key: judge_result
    timeout: 600

edges:
  - { from: START, to: select }
  - { from: select, to: judge,        condition: backend != "claude" }
  - { from: select, to: judge_claude, condition: backend == "claude" }
  - { from: judge, to: END }
  - { from: judge_claude, to: END }
```

The prompt `adapters/prompts/judge.yaml` replaces the literal
`tmp/draft-judgement.md` with `{{ artifact_path }}`. No doctrine text
changes (the prompt is a pointer; doctrine lives in `doctrine.md`).

No `allow_all_tools` on the Claude node (FR-958 R-2, C-3). No `Bash`, no
MCP, no `Edit` (the judge creates one new file; it does not modify).

### 2. Wrapper (`scripts/judge.sh`; judgement R-3)

- `BACKEND="${JUDGE_BACKEND:-copilot}"`; refuse anything but `copilot|claude`
  (exit 64) **before the lock is taken**, so a typo cannot select the default
  silently.
- `ARTIFACT="$WORKDIR/tmp/draft-judgement-${BACKEND}-${FR_SLUG}.md"` where
  `FR_SLUG` is the FR basename without extension. The startup `rm -f` and
  the end-of-run artifact check both use this path. The name is
  **per-backend-per-FR**, not per-run: a rerun of the same backend on the
  same FR removes and replaces only its own earlier draft; the other
  backend's draft and other FRs' drafts survive. The README names the
  pattern and the overwrite.
- Pass `--var backend=$BACKEND --var artifact_path=$ARTIFACT`.
- Lock unchanged (one judge at a time is still right; the artifact change
  protects the *previous* run's output, which the lock never did).
- Print the artifact path and the backend on success.

### 3. README and doctrine pointers

`adapters/README.md` gains: backend selection and validation; the
per-backend-per-FR artifact pattern, the overwrite rule, and why (the
2026-09-02 clobber); that the Claude node has four tools and no bypass; that
it bills the operator's Claude subscription (with FR-959's residual payer
list linked, not repeated). `SKILL.md`'s "one judge to rule them all"
paragraph gains one sentence: the graph has two backend nodes, still one
route. `doctrine.md` and `judgement.template.md` are untouched.

### 4. Witness record (R-7, judgement R-6) — `feature-requests/evidence/FR-960-claude-judge-witness.md`

Committed, one section per live run:

| Field | Content |
|---|---|
| Authoring proof | `scripts/author.sh` command and brief path, digest of the local `tmp/draft-authoring-report.md` (which is **not** committed, per `.github/skills/graph-authoring/SKILL.md:35`), quoted required sections, lint and smoke commands with results, graph commit SHA, limitations |
| Run | target FR path and commit SHA, backend, `claude --version` / `copilot --version`, auth mode as reported by FR-959's preflight, `JUDGE_BACKEND`, start/end timestamps, artifact path and sha256, verdict header line |
| Dual-run inventory | for each draft: the verdict line, every substantive claim in *What is sound*, each R-* revision, each C-* condition — under stable witness-local IDs (`CP-n` for the Copilot draft, `CL-n` for the Claude draft). Each item carries a disposition `matched` (cite the counterpart ID), `contradicted` (cite both and the file:line evidence each relies on), or `backend-only`. When no item is `contradicted` or `backend-only`, the section ends with the literal sentinel `no backend-only or contradicted items` — convergence recorded, not an empty table passed off as a result |
| Signatures | two separate dated lines by a human other than the enforcer: (1) "Enforcement-infrastructure diff and route invariants accepted by <name>, <date>"; (2) "Residual Claude subscription payer boundary (FR-959 §5) accepted for judge execution by <name>, <date>" |
| Limitations | anything not exercised |

### 5. Tests (judgement R-5) — `tests/unit/test_fr960_claude_judge_variant.py`, marked `process`, every test `@pytest.mark.req("REQ-YG-642")`

- Wrapper, stubbed `YAMLGRAPH_BIN` (pattern of `test_fr758_judge_review_wrappers.py`):
  exact argv for unset, `copilot`, `claude`, and `cluade` `JUDGE_BACKEND`;
  `cluade` exits 64 with no `tmp/.judge.lock` created; artifact path is
  `tmp/draft-judgement-<backend>-<fr-slug>.md`; a pre-created
  `tmp/draft-judgement-copilot-other.md` and
  `tmp/draft-judgement-copilot-<same-slug>.md` both survive a `claude` run;
  a second `copilot` run on the same FR replaces
  `tmp/draft-judgement-copilot-<same-slug>.md`; verdict-line verification
  unchanged; no real judge launch.
- Graph routing: compile the adapter with mocked `subprocess.run`;
  `backend=copilot` visits only `judge`, `backend=claude` visits only
  `judge_claude`; both receive the same `judge` prompt and the requested
  `artifact_path`; the Claude node's captured argv contains `--tools`,
  `Read,Glob,Grep,Write` and `--allowedTools`, `Read,Glob,Grep,Write` and
  `--max-turns`, `40`, and contains no `--dangerously-skip-permissions`,
  `Bash`, `Edit`, or `mcp__` name.

### 6. Traceability (judgement R-4)

- **REQ-YG-642** (id provisional, re-derived at enforce) folded into
  `capabilities/CAP-211-sole-route-judge-review.yaml` with `fr: FR-758, FR-960`
  and modules: `.github/skills/judge-fr/adapters/graph.yaml`,
  `.github/skills/judge-fr/adapters/prompts/judge.yaml`, `scripts/judge.sh`,
  `tests/unit/test_fr758_judge_review_wrappers.py`,
  `tests/unit/test_fr960_claude_judge_variant.py`.
- `ARCHITECTURE.md` regenerated; `python scripts/req_coverage.py --strict`.
- Changelog fragment `changelog/unreleased/fr-960-claude-judge-variant.md`
  (`type: feat`, `scope: judge`, `req: REQ-YG-642`).
- Diary entry under `docs/diary/` with a **Seed**.

### Requirements (ADR-001; provisional id)

- **REQ-YG-642** — Judge adapter supports backend selection (`copilot`
  default, `claude`) inside one graph via state-conditioned edges; the
  Claude judge node restricts tool availability and approval to
  `Read, Glob, Grep, Write` with no bypass; `scripts/judge.sh` derives a
  per-backend-per-FR artifact path from backend and FR, refuses unknown
  backends before taking the lock, and a same-backend rerun replaces only its
  own artifact; each live run is recorded in a committed witness including a
  dual-backend claim inventory with `matched` / `contradicted` /
  `backend-only` dispositions and two separate human signatures.

## Acceptance Criteria (revised by the judgement; C-n = gate)

- [ ] AC-01 (C-2): FR-959 is Implemented on main, its committed auth probe
  and live witness exist, and its kill criterion has not fired, before any
  D-2..D-9 work begins.
- [ ] AC-02 (C-3): `feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md`
  is committed, cited here, and names the artifact boundary, precedent,
  expected edits, lint, narrow smoke, and report contract.
- [ ] AC-03 (C-3): `scripts/author.sh feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md`
  produces a non-empty local `tmp/draft-authoring-report.md` with the
  required headings; the witness records its digest, quoted required
  sections, lint and smoke commands/results, graph commit SHA, and
  limitations, and nowhere claims the report is committed.
- [ ] AC-04: `yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml`
  → 0 errors; a REQ-YG-642 test proves `copilot` selects only `judge`,
  `claude` selects only `judge_claude`, and both receive the same `judge`
  prompt and requested `artifact_path`.
- [ ] AC-05 (C-4): the Copilot node retains `backend: cli`,
  `model: gpt-5.6-sol`, `allow_all_paths: true`, `allow_all_tools: true`;
  only its `artifact_path` variable and routing edge differ from the
  committed pre-FR-960 graph.
- [ ] AC-06 (C-5): the Claude node's captured argv contains `--tools`,
  `Read,Glob,Grep,Write`; `--allowedTools`, `Read,Glob,Grep,Write`;
  `--max-turns`, `40`; and no `--dangerously-skip-permissions`, `Bash`,
  `Edit`, or `mcp__` name.
- [ ] AC-07: stubbed wrapper tests prove unset and `copilot` select the
  Copilot branch, `claude` the Claude branch, any other value exits 64
  before lock creation, and the exact `--var backend=…` and
  `--var artifact_path=…` arguments are passed.
- [ ] AC-08: wrapper tests prove the path is
  `tmp/draft-judgement-<backend>-<fr-slug>.md`; a run removes/replaces only
  that path; other-backend and other-FR artifacts survive; a same-backend
  same-FR rerun replaces its earlier artifact.
- [ ] AC-09: the prompt contains `{{ artifact_path }}` and no literal
  `tmp/draft-judgement.md`; `doctrine.md` and `judgement.template.md`
  unchanged (diff empty).
- [ ] AC-10: README and SKILL text per §3, linking FR-959's residual payer
  list rather than restating it.
- [ ] AC-11: CAP-211 carries REQ-YG-642 and FR-960 provenance;
  `ARCHITECTURE.md` regenerated; every new test tagged
  `@pytest.mark.req("REQ-YG-642")`; changelog fragment carries
  `req: REQ-YG-642`; `python scripts/req_coverage.py --strict` passes.

Live (each recorded in the witness; C-6: pytest and CI never launch a judge):

- [ ] AC-12 (C-8): `JUDGE_BACKEND=claude scripts/judge.sh <FR>` on a host
  with a subscription login and no `ANTHROPIC_API_KEY` writes
  `tmp/draft-judgement-claude-<slug>.md` with a `**Verdict:**` line; the
  witness records target FR path and commit SHA, backend, CLI version, auth
  mode from the FR-959 preflight, timestamps, artifact path/hash, verdict.
- [ ] AC-13 (C-10): with `ANTHROPIC_API_KEY=sk-invalid-on-purpose` exported,
  AC-12's subscription-authenticated result is unchanged; if it changes,
  FR-959's kill criterion fires and this FR receives no operational authority.
- [ ] AC-14: the default backend run on the same FR, same host, writes
  `tmp/draft-judgement-copilot-<slug>.md`; both files exist afterwards with
  distinct hashes or an explicitly recorded equality.
- [ ] AC-15: the witness inventories both drafts per §4; every item has a
  source location, evidence citation, and disposition; convergence uses the
  literal sentinel, never an empty table.
- [ ] AC-16 (C-7, C-8): two separate dated signatures by a human other than
  the enforcer — infrastructure diff/route invariants, and the residual
  Claude subscription payer boundary — exist before the Claude route is
  operational or this FR is marked Implemented.
- [ ] AC-17: the diary entry exists with a Seed; all REQ-YG-642 tests and the
  existing judge-wrapper/model-pin tests pass without launching a real judge.

## Alternatives Considered (with dissent preserved)

| Alternative | Probe (2026-09-02) | Disposition | Dissent |
|---|---|---|---|
| Second adapter graph `graph-claude.yaml`, wrapper picks the file | `adapters/README.md`: "one judge to rule them all — the graph above is the sole route" | REJECTED — two files read as two routes | Two small graphs are easier to lint and diff than one graph with a passthrough and two conditional edges; the "route" is arguably the wrapper, not the file. The doctrine's wording decides it, not the engineering. |
| Only change `model:` on the existing Copilot node | `step-judge-v2.yaml:24` already runs `claude-sonnet-4.6` through Copilot | REJECTED — same harness, same permission model, same seat | Cheapest possible second opinion, zero new auth surface. Sufficient if the concern is weights alone. It is not. |
| Keep the shared artifact path; rely on the lock | `scripts/judge.sh:25-38`: lock serializes runs; `rm -f` at line 41 | REJECTED — the lock protects the run, not the previous output; witnessed loss 2026-09-02 | A per-backend-per-FR name means operators must know which file to open; the README fix is one line, and the wrapper prints the path. Real but small cost. |
| Per-run artifact via run id instead of backend+slug | run id exists in the graph run log (`yamlgraph.route` event) | REJECTED — not known to the wrapper before the run; backend+slug is deterministic and human-readable | A UUID never collides even for two runs of the same backend on the same FR; backend+slug overwrites its own earlier draft on a rerun. Accepted and now named honestly (judgement R-3). |
| Give the Claude judge `allow_all_tools` like the Copilot node | NC-414 record: Copilot needed it because denial was silent | REJECTED — Claude has a real availability control; using it is the point (R-2) | Symmetry between the two nodes would make the dual-run comparison cleaner (same tool surface). The asymmetry is deliberate: the comparison is *of judges*, not of tool sets, and a judge with Bash is a judge that can run the judge. |
| Do the dual-run comparison as a graph (`map` over backends, `llm` diff node) | `yamlgraph graph list` — no judge-comparison graph exists; `is_this_a_graph` | DEFERRED — the hand-written inventory for the first N witnesses is the raw read the comparison graph would later be built from (`read_raw_output_first`) | It is exactly the "for each item, ask the model" shape the Scripture says to graph first. Correct; after three witnesses, file it. |

Is this a graph? The judge selection is already inside a graph. The
comparison is not yet a graph, on purpose (last row).

## Out of Scope

- Anything in FR-959 (runtime, lint, payer preflight, auth, settings).
- A third judge backend (Codex, Gemini CLI). The edge shape admits it; no
  consumer (`would_you_use_this`).
- Migrating `scripts/review.sh` / `scripts/author.sh` adapters; separate
  FRs after the first committed witness.
- Changing the default judge backend or the `gpt-5.6-sol` pin.
- Usage-limit wait/reroute (FR-958 §Follow-on).
- Automated disagreement scoring (last dissent row).
- Per-backend-per-FR naming for the other sole-route wrappers
  (`scripts/review.sh`, `scripts/author.sh`, `scripts/research.sh` share the
  fixed-name `rm -f` pattern, census 2026-09-02); convention FR after this
  one's naming survives its first dual run.
- CI or pytest execution of a real judge (C-6); any expansion of the advisory
  output boundary (C-9).

## Related

- `.github/skills/judge-fr/adapters/graph.yaml`, `adapters/prompts/judge.yaml`,
  `adapters/README.md`, `SKILL.md`, `scripts/judge.sh`,
  `capabilities/CAP-211-sole-route-judge-review.yaml`
- `feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md` (D-2, pending)
- `tmp/judge-fr958.log`, `tmp/judge-fr955-957.log` (the clobber's raw record;
  local, quoted in the witness when written)
- FR-959 evidence files

## Judgement (2026-09-02)

**Verdict:** APPROVED WITH REVISIONS — [FR-960-claude-judge-variant.judgement.md](FR-960-claude-judge-variant.judgement.md)
(sole route `scripts/judge.sh`, Copilot CLI gpt-5.6-sol, session
`c03cb3ef-473f-40dd-b190-4586602bd06d`; not the author's session).

**Folded 2026-09-02:** R-1 (FR-959 Implemented is a hard precondition for
every deliverable but this text), R-2 (committed brief cited as D-2), R-3
("per-backend-per-FR" everywhere; rerun-overwrite test), R-4 (REQ-YG-642
into CAP-211, ARCHITECTURE, changelog, diary), R-5 (named test file, routing
and argv assertions), R-6 (claim inventory protocol with sentinel; two
separate signatures; Ideal Result accepts convergence). Acceptance criteria
replaced by the judgement's revised set.

**Gate at fold time:** C-2 — FR-959 not yet Implemented. No FR-960 brief,
graph, wrapper, test, doc, or witness work has begun.

## Implementation Status

- 2026-09-03: C-2 satisfied (FR-959 merged, PR #563 `82356118`). Branch
  `feat/fr-960-claude-judge-variant`.
- RED committed: `tests/unit/test_fr960_claude_judge_variant.py` (process,
  REQ-YG-642; 8 stubbed wrapper tests + 4 mocked routing tests);
  `test_fr931_sole_route_model_pin.py` re-scoped (pin invariant on the
  Copilot-CLI node per route; every copilot node must carry a model);
  brief `authoring-briefs/fr-960-claude-judge-variant-brief.md` (D-2).
- Graph and prompt authored **only** through `scripts/author.sh` with that
  brief (preflight: premises and commands resolved; the agent's one repair
  was `output: {}` on the passthrough `select` node, required by lint E601).
  Local report `tmp/draft-authoring-report.md` (not committed) sha256
  `ed42ab0f96797f205f9212eec4cdfa0a4937ef2c6fa38ed9afefe2f33d0feee0`;
  quoted in the witness.
- GREEN committed: `scripts/judge.sh` (backend validation before lock,
  per-backend-per-FR artifact, `--var backend/artifact_path`), README and
  SKILL text, CAP-211 (REQ-YG-642; REQ-YG-632 re-scoped), `ARCHITECTURE.md`
  regenerated, changelog fragment, FR-758 judge stubs updated to the new
  artifact name.
- Verification: routing + pin tests 7 passed; `yamlgraph graph lint` 0
  issues and `graph validate` ok (3 nodes, 5 edges);
  `req_coverage.py --strict` and `validate_capabilities.py --strict` pass.
  The 26 bash-wrapper tests (FR-758 + FR-960) cannot spawn `bash` from
  pytest on this host (FR-953 class) and are witnessed by CI; the FR-960
  wrapper behaviours were additionally exercised by hand under Git Bash
  with the same stub (unset → copilot; `claude`; `cluade` → 64 with no lock
  and no launch; other-backend/other-FR/legacy drafts survive; same-backend
  rerun replaces its own draft; missing verdict → 65).
- **Deviation recorded:** REQ-YG-632 (FR-931) said "exactly one copilot
  node" per route; FR-960 necessarily adds a second. The invariant is
  re-scoped to "exactly one Copilot-CLI node, pinned; every copilot node
  pinned" in CAP-211 and its test — the judgement's C-4 (preserve the default
  Copilot backend/model) is what the pin protects, and it still holds.
- **Live witness (D-8): in progress** — default-backend run on the
  committed target FR-961 first; the Claude run waits for the C-8 spend
  decision for judge execution (separate from FR-959's Option A).
