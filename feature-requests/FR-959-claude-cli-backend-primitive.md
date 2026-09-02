# Feature Request: FR-959 `backend: claude` — Claude Code CLI as a copilot-node backend (primitive)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed (child of FR-958 SPLIT, D-1)
**Effort:** 1 day
**Requested:** 2026-09-02
**First consumer / first event:** an operator on a host with Claude Code logged in and **no** GitHub Copilot seat edits `examples/demos/session-continuation/graph.yaml`, sets `backend: claude` on its copilot nodes, runs the graph, and gets a `CopilotResult` whose `session_id` the second node resumes. Second consumer, same week: FR-960 swaps the judge adapter onto this backend.
**Research:** in-body dispositioned alternatives table below, with a *Dissent* column preserving the strongest disagreement per row (FR-958 judgement R-7; FR-952/FR-954 precedent for the in-body route). Every probe executed 2026-09-02 on this host or cites a committed record.
**Prior art:**
- [FR-958-claude-code-cli-backend-for-copilot-node.md](FR-958-claude-code-cli-backend-for-copilot-node.md) [SPLIT 2026-09-02] and its [judgement](FR-958-claude-code-cli-backend-for-copilot-node.judgement.md) — the parent. This FR is deliverable D-1 and folds R-2, R-3, R-4, R-5, R-6, and the research half of R-7. It contains no judge-adapter, wrapper, or enforcement-infrastructure change (that is FR-960).
- [FR-081-copilot-node.md](FR-081-copilot-node.md) [Implemented] — created `type: copilot` and the `backend` field. Extended, not duplicated.
- [FR-383-copilot-node-backend-api-fallback.md](FR-383-copilot-node-backend-api-fallback.md) [Implemented] — one `_execute_*` per backend, `CopilotResult.backend` stamped, backend-aware lint (REQ-YG-356/357). Structural template followed exactly.
- [054-copilot-cli-reflection.md](054-copilot-cli-reflection.md) [Implemented 2026-02-20] — REJECTED `claude -p` because OAuth expired on one workstation. Distinguished: this FR does not assume that changed; it makes non-interactive subscription auth a witnessed criterion with a kill criterion, and forbids the API-key rescue (different payer).
- [FR-329-agent-sdk-planner-spike.md](FR-329-agent-sdk-planner-spike.md) [Implemented] — in-process Agent SDK spike, scoped to not touch the copilot runtime. Dispositioned in the table as the future `sampling` successor, rejected here.
- [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md) [Judged] — transport concern, did not touch CAP-30. Inherited discipline: byte-for-byte argv tests (its R-1), verify by artifact never by exit code.
- [FR-105](FR-105-copilot-session-continuations.md) / CAP-30 REQ-YG-105 — `resume`/`continue_session` keys reused 1:1.

## Summary

Add a fourth, closed value `claude` to the copilot node's `backend` enum.
It spawns Claude Code in print mode (`claude -p <prompt> --output-format json`),
maps the shared `cli_flags` keys plus three claude-only keys (`tools`,
`allowed_tools`, `max_turns`), parses the JSON envelope into the existing
`CopilotResult`, and authenticates with the Claude subscription login only:
API-key and cloud-provider variables are stripped from the child environment
**and** a fail-closed auth-status preflight refuses to run when the CLI
reports any other credential. Unknown backend values fail before any
subprocess. The linter learns the new value and its flags.

## Value Statement

Graph authors who run Claude Code get an agent backend that loads `CLAUDE.md`
natively, needs no Copilot seat, and bills the Claude subscription rather
than the Anthropic API account or the GitHub seat.

## Problem

Unchanged from FR-958 §Problem items 1, 3, and 4, restated minimally:

1. `type: copilot` is the only agent-invoking node and its `cli` backend is
   hard-wired to the `copilot` binary (`yamlgraph/node_factory/copilot_runtime.py:92`).
   Twelve agentic graphs depend on one vendor seat.
2. `docs/diary/diary-2026-05-31-letter-to-the-philosopher.md:326` claims the
   node invokes "VS Code Copilot or Claude CLI". No such path exists.
3. **Dispatch is open** (judgement R-5): `NodeConfig.backend` is an
   unrestricted `str` (`yamlgraph/models/node_schema.py:107-109`), non-strings
   normalize to `cli`, and every unknown string falls through to
   `_execute_cli` (`copilot_node.py:183-191,227-228`). `backend: cluade`
   succeeds today by running Copilot. Adding a fourth value on top of an
   open enum would widen that hole.

## Ideal Result

A graph author writes `backend: claude` on any `type: copilot` node and
nothing else changes: same `prompt`, `variables`, `state_key`, `timeout`,
`cli_flags.model/resume/continue_session`; same `CopilotResult`, now with
`backend="claude"` and a real `session_id`. A misspelled backend is an error
at lint and at compile, never a Copilot run. The node can only ever bill the
Claude subscription, and when it cannot prove that, it refuses to run.

## Proposed Solution

### 1. Closed backend enum (R-5)

- `yamlgraph/models/node_schema.py`: `backend: Literal["cli", "api", "sampling", "claude"] | None`.
- `create_copilot_node`: normalize once; anything outside the set (including
  non-strings) raises `ValueError(f"Copilot node '{name}': unknown backend {value!r}; expected one of ...")`
  at compile time, before any node function exists.
- `_execute_backend_once`: explicit dispatch on the four values; the final
  branch is `raise ValueError`, not `return _execute_cli(...)`.
- Lint: `E-COPILOT-BACKEND-UNKNOWN` for the same condition (schema catches
  it first when the graph is loaded through Pydantic; the lint rule exists
  for the linter's own dict path, REQ-YG-357 style).

### 2. `_execute_claude` in `copilot_runtime.py`

Same signature and return as `_execute_cli`. Argv frozen and tested
byte-for-byte:

```python
cmd = ["claude", "-p", prompt, "--output-format", "json"]
if model := cli_flags.get("model"):
    cmd.extend(["--model", model])
if resume := <cli_flags.resume resolved via resolve_state_expression, as in _execute_cli>:
    cmd.extend(["--resume", str(resume)])
elif cli_flags.get("continue_session"):
    cmd.append("--continue")
if (tools := cli_flags.get("tools")) is not None:          # availability (R-2)
    cmd.extend(["--tools", ",".join(tools)])               # [] → "" = no tools
if cli_flags.get("allow_all_tools"):
    cmd.append("--dangerously-skip-permissions")           # approval, broad
elif allowed := cli_flags.get("allowed_tools"):            # approval, narrow (R-2)
    cmd.extend(["--allowedTools", ",".join(allowed)])
if cli_flags.get("allow_all_paths"):
    cmd.extend(["--add-dir", str(Path.cwd())])
if max_turns := cli_flags.get("max_turns"):
    cmd.extend(["--max-turns", str(max_turns)])
```

#### Tool contract (R-2)

Two orthogonal controls, two keys, never conflated:

| `cli_flags` key | Meaning | Claude flag | Copilot backend |
|---|---|---|---|
| `tools: [A, B]` | which tools **exist** for the model; `[]` means none | `--tools "A,B"` | `E-COPILOT-CLI-FLAGS` |
| `allowed_tools: [A, B]` | which of the existing tools run **without a permission prompt** | `--allowedTools "A,B"` | `E-COPILOT-CLI-FLAGS` |
| `allow_all_tools: true` | approve everything that exists | `--dangerously-skip-permissions` | `--allow-all-tools` |

A node that sets `allowed_tools` without `tools` gets every default tool
available and only the listed ones auto-approved; in print mode an
un-approved tool call fails rather than prompts. The linter warns
(`W-COPILOT-CLAUDE-APPROVE-WITHOUT-RESTRICT`) because that combination is
almost never what a batch node wants.

Vendor facts, checked 2026-09-02 against the Claude Code docs: the
permissions reference confirms allow rules "let Claude Code use the
specified tool without manual approval" (approval, not availability). The
CLI reference lists `--tools` ("specify available tools") but does **not**
publish its value grammar. The permissions reference does document that a
bare tool name in `--disallowedTools` "removes the tool from Claude's
context entirely", while a scoped rule only blocks matching calls. So:
`tools` maps to `--tools` with the comma grammar **pinned from the pinned
CLI version's own `claude --help` output, captured verbatim in the witness
file** (AC-03, AC-06). If that capture shows `--tools` cannot express the
list, the availability control falls back to bare-name `--disallowedTools`
for every default tool not in `tools`; the argv test asserts whichever form
the capture supports, and the FR records which. Guessing the grammar is
how FR-958 got R-2.

Not mapped, deliberately: `--bare` (drops CLAUDE.md discovery, un-ordains
the agent), `--no-session-persistence` (kills `session_id`),
`--permission-mode` (subsumed by the two keys), `--system-prompt*` (prompts
live in YAML), `--max-budget-usd` (metered-API concept, notional under
subscription), `--settings`/`--setting-sources` (see §3: the boundary is
witnessed, not narrowed by flags whose precedence we would then also have
to prove).

### 3. Payer boundary (R-3)

The judgement's finding: removing keys from `subprocess.run(env=...)` proves
nothing, because Claude settings files carry an `env` object the CLI applies
after launch, and `apiKeyHelper` can mint a credential from a script. The
parent process does not own the child's configuration surface. So the
boundary is **witnessed**, not sanitized:

0. **Why both strip and witness** (documented, 2026-09-02): the
   authentication reference states that with an active subscription and
   `ANTHROPIC_API_KEY` set, "the API key takes precedence once approved";
   its credential precedence ranks the environment key third and
   `apiKeyHelper` fourth, with the subscription OAuth login as the default
   at the bottom. The settings reference states that settings-file values
   override shell environment variables. So stripping the env removes the
   third-ranked credential but cannot remove a key re-injected by a
   settings `env` block or minted by `apiKeyHelper`; only observing the
   child's own answer can.
1. **Strip anyway** (cheap, removes the common case): child env is
   `os.environ` minus `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
   `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`. FR-363's
   `YAMLGRAPH_OTEL_DIR` layering is applied on top, unchanged.
2. **Preflight, fail closed**: once per process (cached on the module), run
   the CLI's auth-status command with the same stripped env and require it
   to report a subscription (OAuth) login. Any other method, an unparseable
   shape, a non-zero exit, or a missing binary raises `RuntimeError` before
   the first `claude -p`. The CLI reference lists `claude auth status`
   (alongside `login`/`logout`); its output format is not published, so the
   parser is **pinned from a committed, redacted raw probe** taken on the
   pinned CLI version (AC-06); the FR does not guess field names.
3. **Enumerate the residual** in `reference/graph-yaml.md`: user, project,
   local, and managed settings `env` blocks; `apiKeyHelper`; enterprise
   cloud-provider settings. These can still change the payer after the
   preflight passes. They are outside the node's boundary. A named spend
   owner accepts that residual in this FR before authority (AC-07, the
   judgement's C-4 gate); default owner is the repository owner.
4. **Lint**: `provider:` on a claude-backend node → `E-COPILOT-CLAUDE-PROVIDER`
   (provider selection is an API-key payer signal).

The kill criterion applies to this section too: if the preflight cannot be
made fail-closed on the pinned version, the backend does not ship with a
billing claim it cannot prove.

### 4. Result contract (R-6, R-4)

- exit 0 and stdout parses as one JSON object → `result` →
  `CopilotResult.output`, `session_id` → `session_id`, `exit_code=0`,
  `backend="claude"`. `is_error: true` in the object is a failure regardless
  of exit code.
- exit ≠ 0 → `RuntimeError` naming the node, the exit code, and the first
  200 chars of `result` if stdout parsed, else of stderr. **No numeric
  subtype is interpreted** (the docs promise only 0 vs non-zero).
- exit 0 with non-JSON stdout → `RuntimeError` ("exit 0 but no JSON
  envelope"), never an empty substitute (Commandment 6; NC-414).
- `FileNotFoundError` → same "binary not found, on PATH?" pattern as
  Copilot; `TimeoutExpired` → same mapping.
- **No usage-limit classifier** (R-4). A subscription cooldown surfaces as
  the generic non-zero/`is_error` failure above. The wait-or-reroute design
  sketched in FR-958 §Follow-on stays there; it re-enters only with a
  committed real refusal.
- `total_cost_usd` logged at DEBUG as "notional"; not added to `CopilotResult`.

### 5. Linter (`linter/patterns/copilot.py`)

| Code | Condition | Severity |
|---|---|---|
| `E-COPILOT-BACKEND-UNKNOWN` | `backend` not in the closed set | error |
| `E-COPILOT-CLI-FLAGS` | `tools`/`allowed_tools`/`max_turns` on `cli` backend | error |
| `E-COPILOT-API-FLAGS` | the same three keys on `api` (joins the existing list) | error |
| `E-COPILOT-CLAUDE-PROVIDER` | `provider:` on `claude` backend | error |
| `W-COPILOT-CLAUDE-TOOLS` | `allow_all_tools` together with `allowed_tools` (narrow list dead) | warning |
| `W-COPILOT-CLAUDE-APPROVE-WITHOUT-RESTRICT` | `allowed_tools` without `tools` | warning |
| `W-COPILOT-CLAUDE-MODEL` | model matches Copilot-only pattern (`gpt-*`, `*-sol`) | warning |

Existing `resume`/`continue_session` mutual exclusion applies unchanged.

### 6. Documentation and traceability

- `reference/graph-yaml.md` copilot section: enum, flag table (with the
  availability/approval split), backend-semantics bullet, residual payer
  list. `reference/getting-started.md:101`: "Copilot CLI or Claude Code CLI".
- `capabilities/CAP-30-copilot-node.yaml`: `fr: FR-082, FR-959` (multi-FR
  mechanism), plus the REQ ids below. `ARCHITECTURE.md` regenerated.
- Changelog fragment `changelog/unreleased/fr-959-claude-backend.md`
  (`type: feat`, `scope: copilot`, `req: REQ-YG-639`).
- `docs/diary/diary-2026-05-31-letter-to-the-philosopher.md:326` becomes
  true; no edit.

### Requirements (ADR-001; ids provisional, `max+1` at authoring, re-derived at enforce)

- **REQ-YG-639** — Copilot node supports `backend: claude`: list argv
  `claude -p <prompt> --output-format json` with the frozen flag mapping;
  JSON envelope parsed into `CopilotResult(backend="claude", session_id=<id>)`;
  failure on non-zero exit, `is_error`, non-JSON stdout, missing binary,
  timeout; no numeric exit subtype interpreted.
- **REQ-YG-640** — Copilot `backend` is a closed enum (`cli`, `api`,
  `sampling`, `claude`) at schema, compile, and lint; unknown or non-string
  values fail before any subprocess; lint rules cover claude-only flags,
  approval-vs-availability, provider-on-claude, and Copilot-only models.
- **REQ-YG-641** — Claude backend payer boundary: child env stripped of
  API-key and cloud-provider variables; fail-closed subscription
  auth-status preflight pinned to a committed raw probe; residual settings
  surface enumerated in docs and accepted by a named spend owner.

## Acceptance Criteria

Offline (mocked `subprocess.run`; no binary, no network):

- [ ] AC-01: `backend: cluade`, `backend: 3`, `backend: ""` each raise at
  `create_copilot_node` with a message listing the four accepted values;
  `subprocess.run` is never called. `cli`, `api`, `sampling`
  (`NotImplementedError`, unchanged), `claude` keep their specified behaviour.
- [ ] AC-02: lint `E-COPILOT-BACKEND-UNKNOWN` fires for the same inputs;
  REQ-YG-357 tests unchanged.
- [ ] AC-03: argv equality, byte-for-byte list compare, for: prompt+model;
  `resume` via state expression; `continue_session`; `tools: [Read, Grep]`
  → `--tools`, `Read,Grep`; `tools: []` → `--tools`, `""`;
  `allowed_tools: [Read, Write]` → `--allowedTools`, `Read,Write`;
  `allow_all_tools` → `--dangerously-skip-permissions` and no
  `--allowedTools`; `allow_all_paths` → `--add-dir <cwd>`; `max_turns: 40`
  → `--max-turns`, `40`. Order fixed as in §2.
- [ ] AC-04: a test asserts `--allowedTools` is **never** emitted as the
  only tool flag when `tools` is set, and documentation text states the
  availability/approval distinction (grep for both flag names in the
  reference section).
- [ ] AC-05: envelope success → `CopilotResult` fields as specified; exit
  1 with JSON `result` → `RuntimeError` containing "exit 1" and the result
  head; exit 7 → "exit 7" (proves no taxonomy); exit 0 + `is_error: true`
  → `RuntimeError`; exit 0 + non-JSON → `RuntimeError`; missing binary and
  timeout → mapped `RuntimeError`s. State is not updated in any failure.
- [ ] AC-06 (raw record first): `feature-requests/evidence/FR-959-claude-auth-probe.md`
  commits a **redacted** raw capture of the auth-status command's stdout on
  the pinned CLI version for (a) a subscription login, (b) `ANTHROPIC_API_KEY`
  exported, (c) logged out; plus a settings-precedence probe showing whether
  a settings-file `env` value overrides an inherited shell value. The
  preflight parser is written from (a)–(c) and its fixtures are those
  captures. If any capture is unobtainable, the FR says so and the
  preflight fails closed on the unobserved case.
- [ ] AC-07: `reference/graph-yaml.md` lists the residual payer surface;
  this FR carries a line "Residual payer boundary accepted by <name>,
  <date>" before authority (judgement C-4).
- [ ] AC-08: with `ANTHROPIC_API_KEY=sk-test` and `CLAUDE_CODE_USE_BEDROCK=1`
  in the parent env, the mocked `env` kwarg lacks both, keeps `PATH`, and
  keeps the FR-363 OTel path when `YAMLGRAPH_OTEL_DIR` is set; the
  preflight is invoked exactly once across two node executions.
- [ ] AC-09: no symbol named `ClaudeUsageLimitError`, no reset-time parser,
  no refusal regex exists in the package (grep-checked).
- [ ] AC-10: lint table §5 fully covered, one test per code.
- [ ] AC-11: every existing test in `tests/unit/test_copilot_node*.py` and
  `test_linter_patterns_copilot.py` passes unmodified; CAP-30, changelog
  fragment, `ARCHITECTURE.md`, and reference docs updated;
  `python scripts/req_coverage.py --strict` green.

Live witness (`feature-requests/evidence/FR-959-claude-backend-witness.md`,
with command, CLI version, timestamps, and redacted output heads):

- [ ] AC-12: on a host with `claude` on PATH, logged in with a subscription,
  no `ANTHROPIC_API_KEY`: the session-continuation demo with
  `backend: claude` completes, the second node's argv carries `--resume`
  with the first node's real `session_id`.
- [ ] AC-13: same host, `ANTHROPIC_API_KEY=sk-invalid-on-purpose` exported:
  the run still succeeds (an invalid key that reached the child would be
  used and rejected). Then with the login removed (`claude logout` or
  equivalent) the preflight refuses before any `-p` call; the error names
  the auth method it saw.

## Alternatives Considered (with dissent preserved)

| Alternative | Probe (2026-09-02) | Disposition | Dissent (strongest case against the disposition) |
|---|---|---|---|
| New node type `type: claude` | `sed -n 10,27p yamlgraph/constants.py`: 15 node types; `backend` exists to select the agent runtime (FR-383) | REJECTED — duplicates rendering, variables, guards, `CopilotResult` | A `copilot` node called "copilot" that runs Claude is a naming lie; the honest fix is renaming the node type `agent_cli`, which is a wider refactor this FR declines. Recorded, not resolved. |
| In-process Agent SDK (`claude-agent-sdk`) backend | FR-329 spike; `docs/plan-research-dependency-negative-space.md:27`: SDK imported only by an undeclared example | REJECTED — new runtime dependency and a second permission model in core; the CLI reuses the `_execute_cli` seam | The SDK gives tool-approval callbacks and typed messages, which would make the payer preflight and the tool contract *in-process assertions* instead of argv tests against a moving CLI. It is the better long-term boundary; it is not the minimal one. Natural successor for `sampling`. |
| Route Claude via Copilot CLI `--model claude-*` (status quo) | `.chaplain/graphs/watcher-plan/step-judge-v2.yaml:24` already does this | REJECTED as the only option — changes weights, keeps harness, permissions, seat | It already works, costs nothing new, and avoids a second auth surface. If the goal were only "a Claude-weighted judge", this would win. The goal is a second harness and payer. |
| `backend: api` with `provider: anthropic` | `copilot_node.py:359-398`: `execute_prompt()`, no tools, `session_id=None` | REJECTED — no tools, no filesystem, API payer | For reasoning-only nodes it is strictly simpler and already exists. This FR does not replace it. |
| Fall back to `ANTHROPIC_API_KEY` when the login is missing | `grep -n ANTHROPIC_API_KEY reference/development-operations.md`: key provisioned repo-wide | REJECTED — silent payer switch | Availability: a fallback would make the backend work on every dev host today. The FR trades availability for an honest invoice; some operators would take the other trade. They can, explicitly, via FR-958's follow-on reroute design. |
| Narrow settings via `--setting-sources` instead of witnessing auth | judgement R-3 names the flag | REJECTED for v1 — we would then have to prove the flag's precedence too; witnessing the outcome is one probe | Narrowing is *preventive*; witnessing is *detective*. A preflight that passes and a settings `env` that flips the key one second later is a real window. The dissent is right that both belong eventually; v1 takes the one whose proof is a raw record. |

Is this a graph? No. It is a node backend; the graph that consumes it
already exists (`examples/demos/session-continuation`).

## Kill criterion

If AC-12 cannot be witnessed on a provisioned host within one working
session because print mode cannot authenticate on the subscription login,
FR-054's objection stands: REJECT this FR with the log attached and correct
the 2026-05-31 diary line to "Copilot CLI". No API key, cloud provider, or
Copilot backend rescues the witness. If AC-06's captures show the auth
status cannot be read fail-closed, the same applies to the billing claim.

## Constraints

- Argv is a list, prompt is one element (REQ-YG-087; FR-948 R-1).
- Never log `os.environ` or the child env.
- `CopilotResult` shape frozen; fourth `backend` value only.
- Copilot and API behaviour byte-identical (AC-11).
- `copilot_runtime.py` is 192 lines; if `_execute_claude` plus the
  preflight push it past 400, split `copilot_runtime_claude.py`.
- Host fact: on the authoring host `claude` is not on PATH (`where.exe claude`
  empty; the desktop app does not install a CLI binary); `copilot` is. The
  witness log records the install step.

## Out of Scope

- Any change to `.github/skills/judge-fr/**`, `scripts/judge.sh`, or other
  enforcement infrastructure (FR-960).
- `backend: sampling`; streaming; remote delegation (FR-948); usage-limit
  wait/reroute (FR-958 §Follow-on); review/author adapter migration.
- Renaming `type: copilot` (dissent row 1).

## Related

- `yamlgraph/node_factory/copilot_node.py`, `copilot_runtime.py`,
  `yamlgraph/linter/patterns/copilot.py`, `yamlgraph/models/node_schema.py`,
  `yamlgraph/models/schemas.py`, `capabilities/CAP-30-copilot-node.yaml`
- Claude Code docs (pin CLI version in the witness): headless
  <https://code.claude.com/docs/en/headless>, CLI reference
  <https://code.claude.com/docs/en/cli-reference>, settings
  <https://code.claude.com/docs/en/settings>, env vars
  <https://code.claude.com/docs/en/env-vars>

## Judgement (pending)

Route: `scripts/judge.sh feature-requests/FR-959-claude-cli-backend-primitive.md`.
Never in the author's session.
