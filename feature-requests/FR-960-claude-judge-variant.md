# Feature Request: FR-960 Claude judge variant — second backend in the sole-route judge adapter

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed (child of FR-958 SPLIT, D-2) — **blocked on FR-959 Implemented**
**Effort:** 0.5 day + two live judge runs
**Requested:** 2026-09-02
**First consumer / first event:** the operator runs `JUDGE_BACKEND=claude scripts/judge.sh feature-requests/<some-FR>.md` and reads a draft verdict rendered by Claude Code; the same afternoon the same FR is judged with the default backend and the two drafts' disagreements are listed in a committed witness. That list is the deliverable; the second judge exists to produce it.
**Research:** in-body dispositioned alternatives table below with a *Dissent* column (FR-958 judgement R-7).
**Prior art:**
- [FR-958](FR-958-claude-code-cli-backend-for-copilot-node.md) [SPLIT] / [judgement](FR-958-claude-code-cli-backend-for-copilot-node.judgement.md) — parent; this FR is D-2 and folds R-2 (judge argv), R-3 (payer boundary as consumed), and R-7 (persistent witness). It inherits the judgement's AC-12..AC-17 and C-2, C-3, C-4, C-7, C-8.
- [FR-959](FR-959-claude-cli-backend-primitive.md) [Proposed] — the backend this FR consumes. Hard dependency: no live witness here until FR-959 is Implemented (C-2).
- NC-412 / NC-414 / NC-415 (recorded in `.github/skills/judge-fr/adapters/README.md` and `scripts/judge.sh`) — sole-route judge, artifact-not-exit-code contract, OS lock. Preserved: one graph, one wrapper; the second backend is a node inside the graph, not a second route.
- FR-305 (`.chaplain/graphs/watcher-plan/step-judge-v2.yaml`) — lineage of the adapter graph; already runs a Claude *model* through Copilot. Distinguished: this FR changes harness and payer, not weights.
- CAP-44 (judge SPLIT verdict, REQ-YG-143) — judge prompt contract; untouched (the Claude node shares the same prompt file).

## Summary

Add a `judge_claude` node (`backend: claude`, FR-959) to
`.github/skills/judge-fr/adapters/graph.yaml`, selected by a `backend`
state variable through conditional edges so the graph stays the one route.
`scripts/judge.sh` passes `--var backend=${JUDGE_BACKEND:-copilot}` and
writes a **per-run artifact path** so two judges can run on the same FR
without deleting each other's drafts. The Claude node restricts available
tools to `Read, Glob, Grep, Write` with `--tools` and auto-approves exactly
that set; no bypass flag. Every live run leaves a committed witness with
backend, CLI version, auth mode, timestamps, artifact hashes, and, for the
dual run, a complete disagreement table.

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
   the Copilot session transcript. This FR's own AC-16 (two backends, same
   FR) would collide the same way by design.
3. **Over-broad judge permissions.** The current node needs
   `allow_all_tools: true` because Copilot CLI otherwise exits 0 while
   denying the file write (NC-414). Claude's print mode has separate
   availability and approval controls, so the judge can have exactly the
   four tools its contract needs.

## Ideal Result

`scripts/judge.sh <fr>` behaves exactly as today. `JUDGE_BACKEND=claude
scripts/judge.sh <fr>` renders the same doctrine through Claude Code, with
four tools, on the subscription, into its own artifact file. Running both
on one FR and diffing the drafts is a documented ritual with a committed
record; the drafts disagree on something, and that something is the most
useful line in either.

## Proposed Solution

### 1. Adapter graph (graph authoring route only)

Target shape; the edit MUST go through `scripts/author.sh` with a task brief
(`.github/skills/graph-authoring/doctrine.md`). The YAML below is the brief's
target, not a hand edit:

```yaml
state:
  fr_path: str
  backend: str            # "copilot" | "claude"; wrapper always sets it
  artifact_path: str      # wrapper-computed per-run path (see §2)
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
      tools: [Read, Glob, Grep, Write]     # availability (FR-959 `--tools`)
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

No `allow_all_tools` on the Claude node (judgement R-2, C-3). No `Bash`, no
MCP, no `Edit` (the judge creates one new file; it does not modify).

### 2. Wrapper (`scripts/judge.sh`)

- `BACKEND="${JUDGE_BACKEND:-copilot}"`; refuse anything but `copilot|claude`
  (exit 64) so a typo cannot select the default silently.
- `ARTIFACT="$WORKDIR/tmp/draft-judgement-${BACKEND}-${FR_SLUG}.md"` where
  `FR_SLUG` is the FR basename without extension. The startup `rm -f` and
  the end-of-run artifact check both use this path. The README's operator
  instructions name the pattern.
- Pass `--var backend=$BACKEND --var artifact_path=$ARTIFACT`.
- Lock unchanged (one judge at a time is still right; the artifact change
  protects the *previous* run's output, which the lock never did).
- Print the artifact path and the backend on success.

### 3. README and doctrine pointers

`adapters/README.md` gains: backend selection; the per-run artifact
pattern and why (the 2026-09-02 clobber); that the Claude node has four
tools and no bypass; that it bills the operator's Claude subscription (with
FR-959's residual payer list linked, not repeated). `SKILL.md`'s "one judge
to rule them all" paragraph gains one sentence: the graph has two backend
nodes, still one route.

### 4. Witness record (R-7) — `feature-requests/evidence/FR-960-claude-judge-witness.md`

Committed, one section per live run:

| Field | Content |
|---|---|
| Authoring proof | `scripts/author.sh` command, digest of the local `tmp/draft-authoring-report.md` (which is **not** committed, per `.github/skills/graph-authoring/SKILL.md:35`), quoted required sections, lint and smoke commands with results, graph commit SHA |
| Run | backend, `claude --version` / `copilot --version`, auth mode as reported by FR-959's preflight, `JUDGE_BACKEND`, start/end timestamps, artifact path and sha256, verdict header line |
| Dual run | the two verdict lines; a table of every finding present in one draft and absent from the other, with the judge's file:line evidence for each; zero rows is recorded as a finding ("second judge added nothing on this FR") |
| Limitations | anything not exercised |

### Requirements (ADR-001; provisional id)

- **REQ-YG-642** — Judge adapter supports backend selection (`copilot`
  default, `claude`) inside one graph via state-conditioned edges; the
  Claude judge node restricts tool availability and approval to
  `Read, Glob, Grep, Write` with no bypass; `scripts/judge.sh` derives a
  per-run artifact path from backend and FR and refuses unknown backends;
  each live run is recorded in a committed witness including a
  dual-backend disagreement table.

## Acceptance Criteria

Gates inherited from the FR-958 judgement are marked (C-n).

- [ ] AC-01 (C-2): FR-959 is Implemented on main before any live criterion
  below is attempted; offline criteria may proceed on a branch.
- [ ] AC-02: `yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml`
  → 0 errors; the graph has exactly two `type: copilot` nodes, both with
  `prompt: judge`; the `judge` node's config is byte-identical to today's
  except for the added `artifact_path` variable.
- [ ] AC-03 (C-3): the Claude node's argv, asserted by a test that compiles
  the graph and captures the mocked `subprocess.run`, contains
  `--tools`, `Read,Glob,Grep,Write` and `--allowedTools`, `Read,Glob,Grep,Write`,
  and does **not** contain `--dangerously-skip-permissions`, `Bash`, or any
  `mcp__` name. If FR-959's captured `claude --help` shows `--tools` cannot
  carry the list, the assertion is instead on bare-name `--disallowedTools`
  for every default tool outside the four; the witness records which form.
- [ ] AC-04: shell tests for `scripts/judge.sh`: unset `JUDGE_BACKEND` →
  `--var backend=copilot`; `JUDGE_BACKEND=claude` → `--var backend=claude`;
  `JUDGE_BACKEND=cluade` → exit 64 before the lock is taken; artifact path
  is `tmp/draft-judgement-<backend>-<fr-slug>.md`; the startup `rm -f`
  touches only that path (a pre-created `tmp/draft-judgement-copilot-other.md`
  survives a claude run).
- [ ] AC-05: `adapters/prompts/judge.yaml` contains `{{ artifact_path }}`
  and no literal `tmp/draft-judgement.md`; doctrine.md unchanged (diff
  empty).
- [ ] AC-06 (C-7): the witness file's *Authoring proof* section exists with
  the report digest, lint, smoke, and graph SHA; the FR text nowhere claims
  the local authoring report is committed.
- [ ] AC-07 (C-8): a human reviewer other than the enforcer signs the
  witness ("Enforcement-infrastructure diff and payer boundary reviewed by
  <name>, <date>") before this FR moves to Implemented.
- [ ] AC-08: README and SKILL.md paragraphs per §3 present; README links
  FR-959's residual payer list rather than restating it.

Live (each recorded in the witness):

- [ ] AC-09 (C-4): `JUDGE_BACKEND=claude scripts/judge.sh <FR>` on a host
  with a subscription login and no `ANTHROPIC_API_KEY` writes
  `tmp/draft-judgement-claude-<slug>.md` with a `**Verdict:**` line; the
  FR-959 preflight's reported auth mode is in the witness.
- [ ] AC-10: with `ANTHROPIC_API_KEY=sk-invalid-on-purpose` exported, AC-09
  still succeeds (FR-959 AC-13 at the judge level).
- [ ] AC-11: the default backend run on the same FR, same host, writes
  `tmp/draft-judgement-copilot-<slug>.md`; both files exist afterwards
  (the clobber is gone).
- [ ] AC-12: the witness's disagreement table is complete: every finding in
  one draft absent from the other, with evidence; zero rows recorded as a
  finding, not a pass.
- [ ] AC-13 (kill): if AC-09 fails on auth, FR-959's kill criterion has
  already fired and this FR is REJECTED with it; no payer rescues the run.

## Alternatives Considered (with dissent preserved)

| Alternative | Probe (2026-09-02) | Disposition | Dissent |
|---|---|---|---|
| Second adapter graph `graph-claude.yaml`, wrapper picks the file | `adapters/README.md`: "one judge to rule them all — the graph above is the sole route" | REJECTED — two files read as two routes | Two small graphs are easier to lint and diff than one graph with a passthrough and two conditional edges; the "route" is arguably the wrapper, not the file. The doctrine's wording decides it, not the engineering. |
| Only change `model:` on the existing Copilot node | `step-judge-v2.yaml:24` already runs `claude-sonnet-4.6` through Copilot | REJECTED — same harness, same permission model, same seat | Cheapest possible second opinion, zero new auth surface. Sufficient if the concern is weights alone. It is not. |
| Keep the shared artifact path; rely on the lock | `scripts/judge.sh:25-38`: lock serializes runs; `rm -f` at line 41 | REJECTED — the lock protects the run, not the previous output; witnessed loss 2026-09-02 | A per-run name means operators must know which file to open; the README fix is one line, and the wrapper prints the path. Real but small cost. |
| Per-run artifact via run id instead of backend+slug | run id exists in the graph run log (`yamlgraph.route` event) | REJECTED — not known to the wrapper before the run; backend+slug is deterministic and human-readable | A UUID never collides even for two runs of the same backend on the same FR; backend+slug collides on a re-run (which then overwrites its own earlier draft, arguably fine). Accepted trade. |
| Give the Claude judge `allow_all_tools` like the Copilot node | NC-414 record: Copilot needed it because denial was silent | REJECTED — Claude has a real availability control; using it is the point (R-2) | Symmetry between the two nodes would make the dual-run comparison cleaner (same tool surface). The asymmetry is deliberate: the comparison is *of judges*, not of tool sets, and a judge with Bash is a judge that can run the judge. |
| Do the dual-run comparison as a graph (`map` over backends, `llm` diff node) | `yamlgraph graph list` — no judge-comparison graph exists; `is_this_a_graph` | DEFERRED — a hand-written disagreement table for the first N witnesses is the raw read the comparison graph would later be built from (`read_raw_output_first`) | It is exactly the "for each item, ask the model" shape the Scripture says to graph first. Correct; after three witnesses, file it. |

Is this a graph? The judge selection is already inside a graph. The
comparison is not yet a graph, on purpose (last row).

## Out of Scope

- Anything in FR-959 (runtime, lint, payer preflight).
- A third judge backend (Codex, Gemini CLI). The edge shape admits it; no
  consumer (`would_you_use_this`).
- Migrating `scripts/review.sh` / `scripts/author.sh` adapters; separate
  FRs after the first committed witness.
- Changing the default judge backend or model.
- Usage-limit wait/reroute (FR-958 §Follow-on).
- Automated disagreement scoring (last dissent row).
- Per-run artifact naming for the other sole-route wrappers (scripts/judge.sh, scripts/review.sh, scripts/author.sh, scripts/research.sh
  share the fixed-name `rm -f` pattern, census 2026-09-02); convention FR after
  this one's naming survives its first dual run.

## Related

- `.github/skills/judge-fr/adapters/graph.yaml`, `adapters/prompts/judge.yaml`,
  `adapters/README.md`, `SKILL.md`, `scripts/judge.sh`
- `tmp/judge-fr958.log`, `tmp/judge-fr955-957.log` (the clobber's raw record;
  local, quoted in the witness when written)
- FR-959 evidence files

## Judgement (pending)

Route: `scripts/judge.sh feature-requests/FR-960-claude-judge-variant.md`
(default backend). Never in the author's session.
