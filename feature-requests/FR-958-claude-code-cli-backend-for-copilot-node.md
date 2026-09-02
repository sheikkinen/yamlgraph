# Feature Request: FR-958 `backend: claude` — Claude Code CLI as a copilot-node agent backend, with a Claude judge variant

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1.5 days (1 day backend + lint + tests; 0.5 day judge variant + live witness)
**Requested:** 2026-09-02
**First consumer / first event:** the operator runs `JUDGE_BACKEND=claude scripts/judge.sh feature-requests/FR-958-claude-code-cli-backend-for-copilot-node.md` on a host where `claude` is authenticated and reads a `tmp/draft-judgement.md` verdict rendered by Claude Code instead of Copilot CLI. Second event, same day: the same FR is judged by both backends and the two drafts are diffed (the `forced_opposite` method applied to the judge itself).
**Research:** in-body dispositioned alternatives table below (FR-952 / FR-954 precedent for the in-body route); every row carries a probe executed 2026-09-02 on this host or a cited committed record.
**Prior art:**
- [FR-081-copilot-node.md](FR-081-copilot-node.md) [Implemented] — created `type: copilot` and its `backend` field with `cli | sampling`. This FR adds a third agent-CLI value to the same field; it does not add a node type. FR-081's own YAML example already uses a Claude model through Copilot, which is the seam this FR replaces with a direct Claude Code invocation.
- [FR-383-copilot-node-backend-api-fallback.md](FR-383-copilot-node-backend-api-fallback.md) [Implemented] — made `backend` real at runtime and added `api`. It is the structural template: one `_execute_*` function per backend, `CopilotResult.backend` stamped, linter made backend-aware (REQ-YG-356/357). This FR follows it exactly and extends the same linter.
- [054-copilot-cli-reflection.md](054-copilot-cli-reflection.md) [Implemented, 2026-02-20] — the decision that REJECTED `claude -p` in favour of Copilot CLI: "Has the same flags but requires separate OAuth auth that expires. Copilot CLI uses GitHub auth — already authenticated." This is the binding precedent (FR-737 rule). Distinguished below under *Why the FR-054 rejection no longer binds*: the rejection was about the auth channel of one workstation in February 2026, not about the node design, and the FR makes the auth witness an explicit acceptance criterion rather than an assumption.
- [FR-329-agent-sdk-planner-spike.md](FR-329-agent-sdk-planner-spike.md) [Implemented] — in-process Anthropic Agent SDK spike, explicitly scoped to *not* change the copilot runtime. The SDK is the in-process alternative to spawning the `claude` binary; dispositioned in the alternatives table (rejected for this FR, kept as the future `sampling` successor).
- [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md) [Judged: APPROVED WITH REVISIONS] — remote Copilot CLI delegation over WinRM. Orthogonal transport concern; it did not touch CAP-30 (its C-7). Shared lesson inherited here: verify by artifact, never by exit code, and freeze the child argv byte-for-byte in tests (its R-1).
- [FR-105](FR-105-copilot-session-continuations.md) / CAP-30 REQ-YG-105 — session continuation via `--resume` / `--continue` and `CopilotResult.session_id`. Claude Code exposes the same two flags and returns the session id in its JSON result, so the same `cli_flags` keys map 1:1; no new keys.
- `.github/skills/judge-fr/adapters/graph.yaml` (NC-412/NC-414/NC-415) — the sole-route judge adapter, currently hard-wired to `backend: cli` with `gpt-5.6-sol`. The Claude judge variant is a second node in this graph, not a second route.

## Summary

Add `backend: claude` to `type: copilot`. It spawns the Claude Code CLI in
print mode (`claude -p ... --output-format json`) with the same `cli_flags`
vocabulary the `cli` backend already has, parses the JSON result envelope
into the existing `CopilotResult`, and makes the linter backend-aware for
the new value. The backend authenticates with the Claude subscription
login only: API-key and cloud-provider variables are stripped from the
child environment, so the Anthropic API account never pays for a run the
author placed on the subscription. On top of it, add a Claude judge node to the sole-route judge
adapter graph, selectable by a `backend` graph variable, so `scripts/judge.sh`
can render the same FR verdict through either agent.

## Value Statement

Graph authors who run Claude Code get an agent backend that loads
`CLAUDE.md` natively, needs no GitHub Copilot seat, and bills the Claude
subscription rather than the Anthropic API account; the
chaplain gets a second, independently-weighted judge so a verdict can be
cross-examined instead of trusted.

## Problem

`type: copilot` is the only node that invokes an *agent* (an LLM with file
and tool access, arriving with repo doctrine loaded). Its `cli` backend is
hard-wired to the `copilot` binary
(`yamlgraph/node_factory/copilot_runtime.py:92`, `cmd = ["copilot", "--silent"]`).
The `api` backend bypasses agents entirely (no tools, no doctrine). The
`sampling` backend raises `NotImplementedError`. Consequences:

1. **Single-vendor agent seam.** Every agentic graph in the repo (12 files
   under `.chaplain/graphs/`, `.github/skills/*/adapters/`, `examples/ebook/`)
   depends on a GitHub Copilot subscription and the Copilot CLI's
   permission model. A host with Claude Code but no Copilot cannot run
   the judge, the reviewer, the author, or the ebook pipeline.
2. **The judge has one brain.** `.github/skills/judge-fr/adapters/graph.yaml`
   pins `gpt-5.6-sol` via Copilot. The Scripture's `forced_opposite`
   method and `model_as_trusted_peer` trap both ask for an adversarial
   second reading of enforcement outputs; today the only way to get one
   is to re-run the same route with a different `model:` string, which
   changes the weights but not the harness, tools, or instruction loading.
3. **A diary claim is false.** `docs/diary/diary-2026-05-31-letter-to-the-philosopher.md:326`
   describes the copilot node as invoking "VS Code Copilot or Claude CLI".
   No such path exists (grep of `yamlgraph/` for `claude` finds only a
   model-name pattern in the provider linter). The FR either makes the
   claim true or the claim should be corrected; this FR makes it true.
4. **Claude Code's headless contract is a better fit for the judge's
   file-write seam than Copilot's.** NC-414 recorded that Copilot CLI
   exits 0 while silently denying the `tmp/draft-judgement.md` write
   unless `--allow-all-tools` is set. Claude Code's print mode takes an
   explicit `--allowedTools` list, so the judge can be granted exactly
   `Read, Glob, Grep, Write` instead of everything.

### Why the FR-054 rejection no longer binds

FR-054 (2026-02-20) rejected `claude -p` because "OAuth tokens expired
constantly" on the operator's workstation and Copilot was already
authenticated. Three things changed:

- The credential in question is the Claude *subscription* login
  (`claude` device/OAuth flow, stored by the CLI itself), and that is the
  only credential this backend may use. FR-054 measured token expiry once,
  on one workstation, in February. This FR does not assume the answer has
  changed; it makes non-interactive subscription auth the AC-11 witness
  with a kill criterion. The tempting shortcut, falling back to
  `ANTHROPIC_API_KEY`, is forbidden here because it changes **who pays**:
  the API key bills the Anthropic API account (the `backend: api` payer),
  the subscription bills the Claude plan, the Copilot CLI bills the
  GitHub seat. Three backends, three payers, no silent cross-billing.
- The problem FR-054 solved was "invoke an agent that has read the
  Scripture". Claude Code reads `CLAUDE.md` natively and this repo's
  `CLAUDE.md` points at `.github/copilot-instructions.md` as doctrine
  ("read it first"), so the agent arrives ordained by the same mechanism.
- FR-054 chose the *road already built*. Six months later the Copilot road
  is a single point of failure for every enforcement graph. A second road
  is now the cheaper insurance, and the auth objection becomes a
  measurable acceptance criterion (AC-11) instead of a reason not to look.

## Ideal Result

A graph author writes `backend: claude` on any existing `type: copilot`
node and nothing else changes: the same `prompt`, `variables`,
`state_key`, `timeout`, `cli_flags.model`, `cli_flags.resume`,
`cli_flags.continue_session` work; the node returns the same
`CopilotResult` with `backend="claude"` and a real `session_id`. The
judge adapter graph has two judge nodes sharing one prompt; the wrapper
picks one with `JUDGE_BACKEND`. Running both on the same FR yields two
drafts whose disagreements are the most valuable lines in either.

## Proposed Solution

### 1. Runtime: `_execute_claude` in `copilot_runtime.py`

One new function beside `_execute_cli`, same signature, same
`CopilotResult` return. The argv contract is frozen (FR-948 R-1
discipline) and tested byte-for-byte:

```python
cmd = ["claude", "-p", prompt, "--output-format", "json"]
if model := cli_flags.get("model"):
    cmd.extend(["--model", model])
if resume := <resolved cli_flags.resume>:          # same state-expression resolution as cli
    cmd.extend(["--resume", str(resume)])
elif cli_flags.get("continue_session"):
    cmd.append("--continue")
if cli_flags.get("allow_all_tools"):
    cmd.append("--dangerously-skip-permissions")
elif tools := cli_flags.get("allowed_tools"):      # NEW key, claude-only
    cmd.extend(["--allowedTools", ",".join(tools)])
if cli_flags.get("allow_all_paths"):
    cmd.extend(["--add-dir", str(Path.cwd())])     # nearest equivalent; see note
if max_turns := cli_flags.get("max_turns"):         # NEW key, claude-only
    cmd.extend(["--max-turns", str(max_turns)])

# Payer isolation: the child must authenticate with the Claude subscription
# login only. Strip every variable that would route billing elsewhere.
CLAUDE_PAYER_DENYLIST = (
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
)
child_env = {k: v for k, v in os.environ.items() if k not in CLAUDE_PAYER_DENYLIST}
# YAMLGRAPH_OTEL_DIR handling (FR-363) is layered on child_env as in _execute_cli.
```

Flag mapping (the `cli_flags` vocabulary is shared; two keys are added).
Flag spellings verified against the Claude Code CLI reference and headless
docs on 2026-09-02 (URLs under *Related*):

| `cli_flags` key | `backend: cli` (copilot) | `backend: claude` |
|---|---|---|
| `model` | `--model <m>` | `--model <m>` (aliases `sonnet`/`opus`/`haiku` or a full id) |
| `resume` | `--resume <id>` | `--resume <id>` |
| `continue_session` | `--continue` | `--continue` |
| `allow_all_tools` | `--allow-all-tools` | `--dangerously-skip-permissions` |
| `allow_all_paths` | `--allow-all-paths` | `--add-dir <cwd>` (Claude has no global path switch; cwd is already trusted) |
| `allowed_tools` (new) | linter error E-COPILOT-CLI-FLAGS | `--allowedTools "A,B,C"` (one comma-joined argv element, the form the headless docs show) |
| `max_turns` (new) | linter error E-COPILOT-CLI-FLAGS | `--max-turns N` |
| (always) | `--silent`, `--share <tmp>` | `--output-format json` |

Not mapped, deliberately: `--bare` (skips memory/CLAUDE.md discovery, which
would un-ordain the agent), `--no-session-persistence` (would kill
`session_id`), `--permission-mode` (subsumed by the two tool keys above),
`--system-prompt*` (prompts live in YAML, Critical Rule 1),
`--max-budget-usd` (a USD ceiling is a metered-API concept; under the
subscription the number is notional and would mislead; `max_turns` is the
bound that means something for this payer).

Result parsing normalizes at the boundary (the one law). Claude Code's
exit code is meaningful, unlike Copilot's: 0 success; 1 failure (error,
max-turns, permission denied); 2 partial (auth rejected before the first
turn). Contract:

- exit 0 and stdout parses as one JSON object → `result` →
  `CopilotResult.output`, `session_id` → `session_id`, `exit_code=0`,
  `backend="claude"`. If the object carries `is_error: true` it is
  treated as a failure regardless of exit code.
- exit ≠ 0 → `RuntimeError` naming the node, the exit code, and the
  first 200 chars of `result` if stdout parsed, else of stderr. Exit 2
  with auth rejection is the FR-054 failure mode surfaced as a typed
  error, not as an empty result. Because the deny-list above removes the
  API key, an expired subscription login cannot be papered over by the
  API account; it fails loudly, which is the point.
- exit 0 with non-JSON stdout → `RuntimeError` ("claude returned exit 0
  but no JSON envelope"), never an empty-output substitute (Commandment
  6; the NC-414 lesson from the Copilot path).
- `FileNotFoundError` → the same "binary not found, is Claude Code
  installed and on PATH?" message pattern the copilot path uses.
  `TimeoutExpired` → same mapping as `_execute_cli`.
- **Usage-limit refusal is classified, not handled (v1).** A Claude
  subscription has rolling usage windows (a 5-hour window and a weekly
  one); when exhausted the CLI refuses the turn until the window resets,
  worst case days away. v1 raises `ClaudeUsageLimitError(RuntimeError)`
  with an optional `resets_at` parsed from the refusal text, instead of a
  bare `RuntimeError`, so a caller can tell "come back later" from
  "broken". The detection pattern is lifted from a real refusal, not
  guessed (see AC-15). Waiting and rerouting are the follow-on below.

`total_cost_usd` from the envelope is logged at DEBUG per node, labelled
"notional": under subscription auth it is the CLI's own estimate, not an
invoice. It is not added to `CopilotResult` (shape frozen; a cost field
is its own FR if a consumer appears).

`_execute_backend_once` in `copilot_node.py` gains one branch:
`if backend == "claude": return _execute_claude(...)`. `CopilotResult.backend`
docstring lists the fourth value. `node_schema.py:108` description updated.

### 2. Linter: backend-aware rules extended (`linter/patterns/copilot.py`)

- `backend: claude` with `resume` **and** `continue_session` → existing
  mutual-exclusion error, unchanged.
- `backend: cli` (or omitted) with `allowed_tools` or `max_turns` → new
  error `E-COPILOT-CLI-FLAGS` ("claude-only cli_flags on copilot
  backend"), symmetric to the existing `E-COPILOT-API-FLAGS`. The same
  two keys on `backend: api` join the existing `E-COPILOT-API-FLAGS` list.
- `backend: claude` with a node-level `provider:` key → new error
  `E-COPILOT-CLAUDE-PROVIDER`: `provider` selects an API-key payer via
  `create_llm()` and has no meaning for the subscription-authenticated
  CLI; its presence signals the author expects API billing.
- `backend: claude` with `allow_all_tools: true` **and** `allowed_tools`
  → new warning `W-COPILOT-CLAUDE-TOOLS` (the broad flag makes the
  narrow list dead).
- `backend: claude` with a model string matching the Copilot-only
  pattern (`gpt-*`, `*-sol`) → warning `W-COPILOT-CLAUDE-MODEL`
  (the CLI would reject it at runtime; catch it at lint).

### 3. Judge variant: second node in the sole-route adapter graph

`.github/skills/judge-fr/adapters/graph.yaml` stays the ONE route (NC-412
"one judge to rule them all"). It gains a `backend` state variable, a
Claude judge node sharing the existing `judge` prompt, and state-condition
edges:

```yaml
state:
  fr_path: str
  backend: str          # "copilot" (default, set by wrapper) | "claude"
  judge_result: dict

nodes:
  select:
    type: passthrough
  judge:                # unchanged: Copilot CLI, gpt-5.6-sol
    type: copilot
    backend: cli
    ...
  judge_claude:
    type: copilot
    backend: claude
    cli_flags:
      model: opus                       # alias; pinned exact id in AC-09 witness
      allowed_tools: [Read, Glob, Grep, Write]   # exactly the judge's seam (NC-414 lesson, narrowed)
      max_turns: 40                     # the bound that matters under subscription billing
    prompt: judge                       # SAME prompt file — zero doctrine duplication (NC-412)
    variables:
      fr_path: "{state.fr_path}"
    state_key: judge_result
    timeout: 600

edges:
  - from: START
    to: select
  - from: select
    to: judge
    condition: backend != "claude"
  - from: select
    to: judge_claude
    condition: backend == "claude"
  - from: judge
    to: END
  - from: judge_claude
    to: END
```

`scripts/judge.sh` passes `--var backend=${JUDGE_BACKEND:-copilot}`. The
artifact contract (`tmp/draft-judgement.md` exists, non-empty, has a
`**Verdict:**` line) is unchanged and backend-independent. The
`adapters/README.md` gains one paragraph: how to select the backend, that
the Claude node is granted exactly four tools instead of all, and that
the Claude judge bills the operator's Claude subscription, never the
repo's API key (the one operator-side exception, an `apiKeyHelper` in
Claude Code settings, is named so nobody discovers it on an invoice).

This graph edit is graph authoring under `.github/skills/graph-authoring/doctrine.md`
and MUST go through `scripts/author.sh` with a task brief; the YAML above
is the brief's target shape, not a hand edit.

### 4. Documentation

- `reference/graph-yaml.md` copilot section: `backend` enum gains
  `claude`; flag table gains the mapping table above; "Backend semantics"
  gains one bullet.
- `reference/getting-started.md:101`: "Delegate task to Copilot CLI or
  Claude Code CLI".
- `docs/diary/diary-2026-05-31-letter-to-the-philosopher.md:326` becomes
  true; no edit.
- `capabilities/CAP-30-copilot-node.yaml`: two new REQ ids (below), `fr:`
  gains `FR-958` via the multi-FR mechanism (FR-954 precedent).

### Requirements (ADR-001)

Numbering note (2026-09-02): FR-955, FR-956, and FR-957 are reserved by
the FR-936 split briefs in `feature-requests/research-briefs/fr955-*`,
`fr956-*`, `fr957-*` (a sibling session's untracked work; `one_session_one_repo`),
so this FR takes FR-958. The two REQ ids below are provisional
(`max + 1` over `ARCHITECTURE.md` at authoring time) and are re-derived
at enforce time if the sibling FRs land first.

- **REQ-YG-639** — Copilot node supports `backend: claude`: spawns
  `claude -p <prompt> --output-format json` as a list argv; maps
  `model`/`resume`/`continue_session`/`allow_all_tools`/`allow_all_paths`
  and the claude-only `allowed_tools`/`max_turns`; launches the child
  with `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
  `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX` removed from its
  environment so only the Claude subscription login can authenticate;
  parses the JSON envelope into
  `CopilotResult(backend="claude", session_id=<id>)`; raises on non-zero
  exit, `is_error`, non-JSON stdout, missing binary, and timeout; a
  subscription usage-limit refusal raises the distinguishable
  `ClaudeUsageLimitError` carrying `resets_at` when parseable.
- **REQ-YG-640** — Copilot lint rules cover `backend: claude`:
  claude-only flags on the `cli` backend are an error; a `provider:` key
  on a claude-backend node is an error (API-key payer signal);
  broad+narrow tool grants together warn; Copilot-only model names warn.

## Acceptance Criteria

Offline (mocked `subprocess.run`, no binary, no network):

- [ ] AC-01: `backend: claude` with prompt + model builds argv exactly
  `["claude", "-p", <rendered>, "--output-format", "json", "--model", "opus"]`
  (byte-for-byte list equality, FR-948 R-1 discipline).
- [ ] AC-02: `allow_all_tools: true` → `--dangerously-skip-permissions`;
  `allowed_tools: [Read, Write]` → `--allowedTools`, `Read,Write`; both
  set → only the broad flag is emitted; `max_turns: 40` →
  `--max-turns`, `40`.
- [ ] AC-03: `resume: "{state.prev.session_id}"` resolves through
  `resolve_state_expression` and emits `--resume <id>`; `continue_session`
  emits `--continue`; both set → linter error (existing test extended).
- [ ] AC-04: stdout `{"type":"result","subtype":"success","is_error":false,"result":"…","session_id":"abc-123"}`
  → `CopilotResult(output="…", backend="claude", session_id="abc-123", exit_code=0)`.
- [ ] AC-05: exit 1 with a JSON `result` → `RuntimeError` whose message
  contains the exit code and the `result` text; exit 2 with empty stdout
  and stderr "authentication" → `RuntimeError` containing "exit 2" and
  the stderr head; exit 0 with `is_error: true` → `RuntimeError`. In all
  three, state is not updated.
- [ ] AC-06: non-JSON stdout with exit 0 → `RuntimeError` (no empty
  `CopilotResult` substitute).
- [ ] AC-07: `FileNotFoundError` → `RuntimeError` naming "claude" and
  "PATH"; `TimeoutExpired` → `RuntimeError` naming the node and timeout.
- [ ] AC-08: linter — `backend: cli` + `allowed_tools` → `E-COPILOT-CLI-FLAGS`;
  `backend: claude` + `allow_all_tools` + `allowed_tools` → `W-COPILOT-CLAUDE-TOOLS`;
  `backend: claude` + `model: gpt-5.6-sol` → `W-COPILOT-CLAUDE-MODEL`;
  `backend: claude` + `provider: anthropic` → `E-COPILOT-CLAUDE-PROVIDER`;
  `backend: api` behaviour (REQ-YG-357 tests) unchanged.
- [ ] AC-09: `yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml`
  reports 0 errors; the graph has exactly two `type: copilot` nodes
  sharing `prompt: judge`; `tmp/draft-authoring-report.md` from
  `scripts/author.sh` is committed as evidence.
- [ ] AC-10: `scripts/judge.sh` passes `--var backend=<JUDGE_BACKEND or copilot>`;
  a shell test asserts the default when the variable is unset.

Live witnesses (this FR's *demo*, not its tests — `demo_vs_test`; each
recorded in `feature-requests/evidence/FR-958-claude-judge-witness.md`
with the command, timestamps, and the artifact's first 10 lines):

- [ ] AC-11: on a host with `claude` on PATH, logged in with a Claude
  subscription, and **no** `ANTHROPIC_API_KEY` in the shell,
  `JUDGE_BACKEND=claude scripts/judge.sh feature-requests/FR-958-…md`
  produces `tmp/draft-judgement.md` with a `**Verdict:**` line, and the
  JSON envelope's `session_id` is non-null in the run log. This is the
  FR-054 auth objection, measured on the subscription credential alone.
- [ ] AC-13 (offline): with `ANTHROPIC_API_KEY=sk-test` and
  `CLAUDE_CODE_USE_BEDROCK=1` in the parent environment, the `env`
  kwarg passed to the mocked `subprocess.run` contains neither, still
  contains `PATH`, and still contains the FR-363 OTel path when
  `YAMLGRAPH_OTEL_DIR` is set.
- [ ] AC-14 (live): with `ANTHROPIC_API_KEY=sk-invalid-on-purpose`
  exported in the parent shell, the AC-11 run still succeeds. An invalid
  key that reached the child would be used and rejected, so success
  proves the deny-list is effective, not merely present.
- [ ] AC-15 (offline, raw-record first): a fixture holding a **real**
  usage-limit refusal from `claude -p --output-format json` (captured on
  the AC-11 host when it occurs, or lifted from the detection regex the
  operator's pre-yamlgraph `loop.sh` already used, per
  `docs/diary/diary-2026-08-08-the-ancestor-in-the-deployed-folder.md:11`)
  → `ClaudeUsageLimitError`, with `resets_at` populated when the text
  carries a reset time. A generic `is_error` result must NOT be classified
  as a limit. If no real refusal has been captured by enforce time, the
  classifier ships with the `loop.sh` pattern and the fixture is marked
  `provenance: loop.sh`, never invented.
- [ ] AC-12: the same FR judged with `JUDGE_BACKEND=copilot` on the same
  host; both drafts committed under `evidence/`; the witness file lists
  every finding present in one draft and absent from the other. Zero
  disagreements is a *finding* (the second judge adds nothing), not a
  pass.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-639")` / `("REQ-YG-640")`;
  `python scripts/req_coverage.py --strict` green.
- [ ] Changelog fragment `changelog/unreleased/fr-958-claude-backend.md`
  (`type: feat`, `scope: copilot`, `req: REQ-YG-639`).
- [ ] Documentation updated (section 4).

## Alternatives Considered

| Alternative | Probe executed (2026-09-02) | Disposition |
|---|---|---|
| New node type `type: claude` | `sed -n 10,27p yamlgraph/constants.py` → 15 node types; `type: copilot` already carries a `backend` enum whose *purpose* is selecting the agent runtime (FR-383) | REJECTED — a second agent node duplicates prompt rendering, variable resolution, guards, and `CopilotResult`; `false_duplicate` in reverse. The backend field exists for exactly this. |
| Route Claude through `backend: api` with `provider: anthropic` | `sed -n 359,398p yamlgraph/node_factory/copilot_node.py` → `execute_prompt()` path, no tools, no filesystem, `session_id=None` | REJECTED for the judge — the judge must *write* `tmp/draft-judgement.md` and *read* cited evidence; `api` is a bare completion. It also bills the Anthropic API account, a different payer from the Claude subscription this backend is scoped to. Remains the right choice for reasoning-only nodes whose author intends API billing. |
| Let `backend: claude` fall back to `ANTHROPIC_API_KEY` when the subscription login is missing or expired | `grep -n ANTHROPIC_API_KEY reference/development-operations.md` → the key is provisioned repo-wide for the `anthropic` provider, so a fallback would fire silently on every developer host | REJECTED — silent payer switch; the operator asked for a Claude run on the subscription and gets an API invoice. Cured by the deny-list, AC-13, AC-14, and the kill criterion's explicit refusal of the rescue. |
| In-process Anthropic Agent SDK (`claude_agent_sdk`) backend | `sed -n 1,50p feature-requests/FR-329-agent-sdk-planner-spike.md`; `docs/plan-research-dependency-negative-space.md:27` → SDK imported only by an undeclared example, not a declared dependency | REJECTED for this FR — adds a runtime dependency and a second permission model to the core package; the CLI subprocess reuses the exact seam `_execute_cli` already owns. Recorded as the natural implementation of the reserved `sampling` backend if it is ever revived. |
| Route Claude via Copilot CLI's `--model claude-*` (status quo) | `grep -n 'model:' .chaplain/graphs/watcher-plan/step-judge-v2.yaml` → already `claude-sonnet-4.6` through Copilot | REJECTED as the *only* option — changes the weights, keeps the harness, permission model, instruction loading, and vendor dependency. Does not answer problem 1 or 4. Stays available; this FR adds, not replaces. |
| Second adapter graph file `graph-claude.yaml` selected by the wrapper | `cat .github/skills/judge-fr/adapters/README.md` → "one judge to rule them all — the graph above is the sole route" | REJECTED — two files is two routes by the doctrine's own wording; a state-condition edge inside one graph is the yamlgraph-native form (`is_this_a_graph`), and `reference/graph-yaml.md:769` shows the exact edge syntax. |
| Make `backend` itself a runtime state expression (`backend: "{state.backend}"`) | `sed -n 1,40p feature-requests/runtime-prompt-interpolation.md` → node config is resolved at compile time; only `cli_flags.resume` is runtime-resolved, by special case | REJECTED — would generalize a compile/runtime split this repo has explicitly declined (LOW priority FR, never taken); the conditional edge needs no new primitive. |
| Do nothing; correct the 2026-05-31 diary line instead | `grep -rn 'Claude CLI' docs/diary/diary-2026-05-31-letter-to-the-philosopher.md` → one claim, one line | REJECTED — pruning the claim is the honest fallback (`growth_as_default` cure) and is what happens if AC-11 fails. Filed as the explicit kill criterion below. |

## Kill criterion

If AC-11 cannot be witnessed within one working session on a provisioned
host (Claude Code installed and logged in with a subscription, no API
key) because print mode cannot authenticate non-interactively on the
subscription credential, FR-054's objection stands: retire this FR as
REJECTED with the log attached, and edit the 2026-05-31 diary line to
say "Copilot CLI" only. Falling back to `ANTHROPIC_API_KEY` to rescue the
witness is not an option; it would prove a different backend for a
different payer. No half-landed backend.

## Constraints

- **Argv is a list, never a shell string**; prompt text is exactly one
  argv element (REQ-YG-087 discipline; FR-948 R-1).
- **Payer isolation (the reason this FR exists in this shape)**: the
  Claude backend authenticates with the Claude subscription login only.
  The child environment is built from `os.environ` minus a frozen
  deny-list (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
  `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`). The node never
  reads, sets, or forwards an API key; `provider:` on a claude-backend
  node is a lint error. Operator-side settings that inject a key
  (`apiKeyHelper` in Claude Code settings) are outside the node's
  boundary and are named in the README as the one remaining way to
  cross-bill.
- **No secrets in argv or logs**: the node must not log `os.environ` or
  `child_env`. The existing `YAMLGRAPH_OTEL_DIR` per-node env injection
  (FR-363) is layered on `child_env` unchanged; Claude's own OTel export
  variables are out of scope.
- **`CopilotResult` shape is frozen**; the fourth `backend` value is the
  only change to the model.
- **Copilot behaviour byte-identical**: every existing test in
  `tests/unit/test_copilot_node*.py` and `test_linter_patterns_copilot.py`
  passes without modification.
- **Module size**: `copilot_runtime.py` is 192 lines; adding
  `_execute_claude` (~70 lines) stays under 300. If the JSON parsing
  helper pushes it past 400, split `copilot_runtime_claude.py`.
- **Host fact, recorded**: on the authoring host (Windows 11, this
  session) `where.exe claude` finds nothing while `copilot` resolves via
  WinGet and npm. The Claude Code desktop app does not put a `claude`
  binary on PATH. AC-11 therefore requires an explicit
  `npm install -g @anthropic-ai/claude-code` (or equivalent) step in the
  witness log; the FR must not assume the binary because a Claude Code
  session is running.

## Out of Scope

- `backend: sampling` — stays reserved and unimplemented.
- Waiting out or rerouting around a subscription usage limit — v1 only
  classifies it (`ClaudeUsageLimitError`). Design sketch in *Follow-on*
  below; it is its own FR because it touches node error policy, not the
  backend.
- Streaming (`--output-format stream-json`) — the copilot node is a
  batch node; streaming is a different FR if a consumer appears.
- Remote/LAN delegation of the `claude` binary (FR-948 territory).
- Changing the default judge model or backend. `copilot` remains the
  default; the Claude judge is opt-in per run.
- A third judge (Codex, Gemini CLI). The conditional-edge shape admits
  it, but no consumer exists (`would_you_use_this`).
- Migrating the review (`scripts/review.sh`) or author (`scripts/author.sh`)
  adapters. Same mechanism, separate FRs once the judge witness exists.

## Follow-on (not v1): usage-limit cooldown — wait or reroute

Recorded here so the successor FR starts from the record, not from
memory (`what_would_the_successor_need`).

**The phenomenon.** Subscription usage is metered in rolling windows.
Once a window is exhausted every `claude -p` call is refused until the
window resets: hours for the short window, up to days for the weekly
one. A graph that hits this mid-pipeline has two honest options and one
dishonest one. The dishonest one, silently switching to the API key, is
excluded by this FR's payer rule.

**Option A — wait.** Treat `ClaudeUsageLimitError.resets_at` as a
scheduling fact: the node sleeps until the reset and retries, or the
graph checkpoints and a scheduler resumes it. Prior art: the operator's
own `loop.sh` did exactly this ("5-hour-limit detection and countdown
sleeps", diary 2026-08-08), and the Scripture seed
`verification_checkpoint_primitive` names the missing piece for the
multi-day case. Waiting inside a node is only acceptable for the short
window; for the weekly window the graph must checkpoint (SQLite/Redis
checkpointer, `--thread`) and exit, leaving a resume-at timestamp in
state. A `timeout` of 600s cannot host a day-long wait.

**Option B — reroute.** Spend subscription credits first, then move the
node to another backend when the limit hits. This is the existing
`on_error: fallback` mechanism, which today knows only
`fallback: {provider}` on llm nodes (`yamlgraph/node_factory/llm_nodes.py:130`).
Extending it to copilot nodes with `fallback: {backend: copilot}` (or
`backend: api`) makes the reroute a **declared, per-node payer decision**
by the graph author, visible in the YAML and lintable, which is the only
form of cross-billing consistent with this FR:

```yaml
judge_claude:
  type: copilot
  backend: claude
  on_error: fallback
  fallback:
    backend: copilot            # explicit second payer; author's call, in the record
    only_on: usage_limit        # never reroute a genuine failure
```

`only_on: usage_limit` is the reason v1 types the error: a reroute that
fires on every `RuntimeError` would mask real defects behind a working
second backend (`plausible_wrong_answer` at the pipeline level).

**Open questions for that FR** (not answered here): does a rerouted judge
still count as "the same judge" for NC-412's one-route rule, or must the
draft record which backend rendered it (it should, and `CopilotResult.backend`
already carries it); should the wait option be a node property or a
graph-level policy; and where the reset timestamp is parsed from if the
CLI's refusal text changes (normalize at the boundary, one regex, one
fixture).

## Related

- `yamlgraph/node_factory/copilot_node.py`, `yamlgraph/node_factory/copilot_runtime.py`
- `yamlgraph/linter/patterns/copilot.py`, `yamlgraph/models/node_schema.py:106-112`, `yamlgraph/models/schemas.py:154-170`
- `.github/skills/judge-fr/adapters/graph.yaml`, `adapters/README.md`, `scripts/judge.sh`
- `capabilities/CAP-30-copilot-node.yaml`
- `docs/diary-2026-02-20.md:504` (the original `claude -p` trap record)
- Claude Code docs consulted 2026-09-02 (CLI version to be pinned in the witness file):
  - headless / print mode, output formats, exit codes, tool denial behaviour: <https://code.claude.com/docs/en/headless>
  - CLI flag reference (`--resume`, `--continue`, `--model`, `--allowedTools`, `--add-dir`, `--max-turns`, `--dangerously-skip-permissions`): <https://code.claude.com/docs/en/cli-reference>
  - environment variables (source of the payer deny-list: `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`; also model alias vars, `DISABLE_TELEMETRY`): <https://code.claude.com/docs/en/env-vars>
  - Agent SDK overview (the in-process alternative dispositioned above): <https://code.claude.com/docs/en/agent-sdk/overview>

## Judgement (pending)

Not yet judged. Route: `scripts/judge.sh feature-requests/FR-958-claude-code-cli-backend-for-copilot-node.md`
(Copilot backend — the Claude backend cannot judge the FR that creates it).
