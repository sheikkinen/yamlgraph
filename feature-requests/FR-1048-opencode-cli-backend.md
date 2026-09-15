# Feature Request: FR-1048 `backend: opencode` — opencode CLI as a copilot-node backend (contrib/example backend contribution)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed (judged APPROVED WITH REVISIONS 2026-09-15; R-1..R-5 folded, awaiting re-judgement)
**Effort:** 1.5 days
**Requested:** 2026-09-15
**Strategic classification:** contrib/example — backend contribution, not a
framework primitive (one named consumer; no three-distinct-use-case evidence).
**First consumer / first event:** an operator who runs opencode (provider
keys in `~/.local/share/opencode/auth.json`, no Copilot seat, no Claude
subscription) runs the disposable two-node integration witness (§AC-14) with
`backend: opencode`, and the second node recalls a nonce from the first
node's session — proving byte-for-byte `--session` resumption of a real
`session_id`. Second consumer, same week: any graph that wants a
provider-agnostic agent backend without a vendor seat.
**Research:** [FR-1048.research.md](FR-1048.research.md) — the FR-890 sole
route (`scripts/research.sh`), brief
`feature-requests/research-briefs/fr-1048-opencode-backend-brief.md`, run
2026-09-15, five personas executed. Four of five converge on "fifth closed
enum value + JSONL stream reader"; the subtractionist dissents ("retire the
requirement / new node type"), which is FR-546's argument.
**Evidence:** [evidence/FR-1048-opencode-cli-probe.md](evidence/FR-1048-opencode-cli-probe.md)
— committed raw captures on the pinned version `1.18.31`: `opencode --version`,
the full `--format json` event stream for a one-word prompt, `--session`
resume with nonce recall, `--continue` non-determinism, a tool-bearing run's
full event vocabulary, exit-code behaviour on success and error, and
`opencode providers list`.
**Prior art:**
- [FR-546-opencode-copilot-backend.md](FR-546-opencode-copilot-backend.md)
  [Judged 2026-06-20, scope frozen, authority granted, never enforced] — the
  same "opencode as a copilot-node backend" territory via the **server/SDK
  route**: `opencode serve` HTTP surface, an `httpx` optional dependency,
  server lifecycle, `json_schema` structured output, agent-markdown permission
  sandbox, and a new `CopilotResult.structured_output` field. **FR-1048
  supersedes FR-546 for the `opencode` backend name.** The FR-546 server/SDK
  route, its structured output, server lifecycle, permission sandbox, `httpx`
  dependency, and `CopilotResult.structured_output` are not concurrently
  authorized; reviving any of them is a new FR with a distinct contract.
  FR-546 predates FR-959; it was written before the CLI-subprocess backend
  pattern existed. FR-1048 is the **CLI route**: `opencode run <prompt>
  --format json` as a subprocess, mirroring FR-959's `claude -p` seam exactly —
  no new dependency, no server lifecycle, no `CopilotResult` field change.
- [FR-959-claude-cli-backend-primitive.md](FR-959-claude-cli-backend-primitive.md)
  [Implemented] — the structural template, followed exactly: closed backend
  enum, one `_execute_*` per backend, typed backend-only flags, a private
  envelope Pydantic model, per-invocation preflight, disposable live witness,
  byte-for-byte argv tests. This FR differs in one load-bearing way: the payer
  model (see §5) — Claude Code has a subscription to protect; opencode has
  only provider keys, so the boundary is inverted.
- [FR-081-copilot-node.md](FR-081-copilot-node.md) [Implemented] — created
  `type: copilot` and the `backend` field. Extended, not duplicated.
- [FR-383-copilot-node-backend-api-fallback.md](FR-383-copilot-node-backend-api-fallback.md)
  [Implemented] — `CopilotResult.backend` stamped; backend-aware lint
  (REQ-YG-356/357). Same discipline.
- [FR-105-copilot-session-continuations.md](FR-105-copilot-session-continuations.md)
  / CAP-30 REQ-YG-105 — `resume` reused 1:1, mapped to opencode's `--session`.
- [FR-363-per-node-otel-scoping-in-copilot-node.md](FR-363-per-node-otel-scoping-in-copilot-node.md)
  — `YAMLGRAPH_OTEL_DIR` layering preserved.

## Summary

Add a fifth, closed value `opencode` to the copilot node's `backend` enum.
It spawns opencode in print mode (`opencode run <prompt> --format json`),
parses the **JSONL event stream** through a typed, fail-closed state machine
into the existing `CopilotResult`, and maps the shared `cli_flags` keys to
two typed flags: `model` (`provider/model`, compile-time fail-closed) and
`resume` (`--session <id>`). There is no subscription to protect: the payer
is the provider key the child opencode resolves, so the boundary is *make the
model explicit at compile time and witness it*. Unknown backend values,
malformed flags, and a missing or malformed `provider/model` fail before any
subprocess, including the version probe. The linter learns the new value, its
flags, and their shapes.

## Value Statement

Graph authors who already run opencode get an agent backend that bills the
provider key they already configured, needs no vendor seat and no
subscription, selects its model through one required `provider/model` value,
and fails loudly on a non-`stop` finish instead of silently returning whatever
the process printed before dying.

## Problem

1. `type: copilot` is the only agent-invoking node, and its backends are
   `cli` (Copilot seat), `api` (no tools, no filesystem), and `claude`
   (Claude subscription). There is no path for an operator whose agent is
   opencode and whose only credentials are provider API keys.
2. **Dispatch is closed but finite** (FR-959 REQ-YG-640): adding a fifth
   value on top of `Literal["cli", "api", "sampling", "claude"]` is safe, but
   only if it rides the same exact-match, typed-flag, fail-before-subprocess
   discipline; a naive `else: _execute_cli` would regress the closed enum.
3. **Output is a stream, not an envelope.** Claude's `--output-format json`
   returns one object (`result`/`session_id`/`is_error`). opencode's
   `--format json` emits a JSONL stream of `step_start` / `text` / `tool_use`
   / `step_finish` / `error` events, with multiple step cycles per run
   (evidence §11). A single `json.loads(stdout)` (the Claude path) would parse
   only the first line and silently drop the rest — a plausible-wrong-answer
   failure.
4. **Exit code is not the only signal** (mirrors FR-959 evidence §5). A
   failed run exits 1 *and* emits a terminal `error` event; the durable signal
   is the event, not the code. A run that hits a tool-permission refusal
   mid-stream must not be reported as success because its last line happened
   to parse.
5. **Payer is provider-key, not subscription.** There is no `claude auth
   status` equivalent whose `authMethod` proves who pays. The equivalent
   question is *which provider/model is the child going to bill*, and the only
   honest answer is: the `--model` we pass. So it must be required, at compile
   time, before any subprocess.

## Ideal Result

A graph author writes `backend: opencode` on any `type: copilot` node and
nothing else changes: same `prompt`, `variables`, `state_key`, `timeout`,
`cli_flags.model/resume`; same `CopilotResult`, now with `backend="opencode"`
and a real `session_id`. A misspelled backend, a malformed flag, or a missing
or malformed `provider/model` is an error at lint and at compile, never an
opencode run and never a subprocess. Every opencode invocation first proves the
CLI is the supported version, and the model it will bill is always the
resolved `--model` the node computed — there is no config-default fallback.
The result text is the ordered concatenation of every `text` event, and any
run whose terminal event is an `error`, whose terminal `step_finish.reason` is
not `stop`, or that fails the typed state machine is a typed failure, not an
empty or partial success.

## Proposed Solution

### 1. Closed backend enum

- `yamlgraph/models/schemas.py`: `COPILOT_BACKENDS = ("cli", "api", "sampling", "claude", "opencode")`.
- `yamlgraph/models/node_schema.py`: `backend: Literal["cli", "api", "sampling", "claude", "opencode"] | None`.
- `create_copilot_node` / `_execute_backend_once`: add the explicit `opencode`
  branch; the final branch remains `raise ValueError`. `normalize_backend`
  already reads `COPILOT_BACKENDS`, so the closed-set guard extends for free.
- Lint: `E-COPILOT-BACKEND-UNKNOWN` covers the new set automatically (it
  reads the same tuple; verify one new test).

### 2. Typed opencode flags (model + resume only)

A private Pydantic model `OpenCodeCliFlags` (`extra="forbid"`, `strict=True`)
validates `cli_flags` **only when `backend == "opencode"`**; every other
backend keeps its current behaviour unchanged:

| key | type | opencode flag | notes |
|---|---|---|---|
| `model` | `str \| None` | `--model <provider/model>` | shape-validated only; the *resolved* model is a compile-time requirement (§5) |
| `resume` | `str` | `--session <id>` | may be a `{state.…}` expression; resolves to the prior `CopilotResult.session_id` |

`continue_session` is **deliberately absent**: evidence §10 shows opencode's
`--continue` resolves "the last session" against a directory-scoped session
store and, with no prior session, **silently starts a new session** — the
opposite of `--session <id>`'s fail-loud behaviour (§4). A node's `--continue`
would resume whatever interactive session a human last ran in that directory.
The explicit `resume` → `--session` is the only safe resumption.

`agent`, `dir`, `variant`, `thinking`, and `auto` are **not mapped** (no
named consumer needs them; permission auto-approval and agent/sandbox
selection must not re-enter FR-546's territory through CLI flags). They are
rejected as extras by `extra="forbid"`, never silently dropped.

Validation runs at schema load, again in `create_copilot_node` for the
linter-free dict path, and in lint as `E-COPILOT-OPENCODE-FLAG-SHAPE`. All
fire before the version probe and the agent subprocess.

### 3. `_execute_opencode` — argv frozen, stream state machine

Lives in a new `yamlgraph/node_factory/copilot_runtime_opencode.py`
(`copilot_runtime.py` is 229 lines; the state machine plus preflight would
push it past the 400 target). Same signature and return as `_execute_cli` /
`_execute_claude`. Argv frozen and tested byte-for-byte, in this order:

```python
cmd = ["opencode", "run", prompt, "--format", "json", "--model", resolved_model]
if resume: cmd += ["--session", str(resume)]  # resolved via resolve_state_expression, as _execute_cli
```

The prompt is one list element (REQ-YG-087; FR-948 R-1); no shell. The
message form (`opencode run <message>`) is used, not `--command`. `--model` is
always emitted from the resolved model (§5).

#### Typed, fail-closed JSONL state machine (R-4)

stdout is JSONL. Every non-empty line must parse as one JSON object and
validate against one of these strict private models (each requires a non-empty
`type` and a non-empty `sessionID`; `extra="ignore"`):

- `_StepStartEvent` — `type == "step_start"`, `part.type == "step-start"`.
- `_TextEvent` — `type == "text"`, `part.type == "text"`, `part.text: str`.
- `_ToolUseEvent` — `type == "tool_use"`, `part.type == "tool"`. **Neutral**:
  ignored for result assembly (evidence §11).
- `_StepFinishEvent` — `type == "step_finish"`, `part.type == "step-finish"`,
  `part.reason: str` in the frozen set `{stop, tool-calls}` (evidence §11).
- `_ErrorEvent` — `type == "error"`, `error.name: str`,
  `error.data.message: str`. Terminal failure.

The state machine enforces:

- a single consistent, non-empty `sessionID` across every event;
- `step_finish(reason="tool-calls")` is an intermediate boundary (the agent
  will call a tool), **not** a terminal and not a failure;
- `step_finish(reason="stop")` is the **only** terminal success signal;
- at most one terminal event, no event after it;
- at least one `text` event whose ordered concatenation is the result.

Each of the following is a typed failure with **no** `CopilotResult` and no
state update: an unknown event `type` or `part.type`; a malformed recognized
event; a non-JSON line; a missing/empty/conflicting `sessionID`; a
`step_finish.reason` outside `{stop, tool-calls}`; a duplicate terminal event;
an event after the terminal; a stream with no terminal `step_finish(stop)`;
no `text` events; any `error` event; or non-zero process exit.

Success maps the ordered `text` concatenation to
`CopilotResult(output=…, session_id=<consistent sessionID>, exit_code=0,
backend="opencode", model=resolved_model)`.

### 4. Per-invocation preflight: version only

No cache. Every opencode node execution runs `opencode --version` with the
same environment as the agent call, before the run:

- The whole banner is compared against `OPENCODE_SUPPORTED_BANNERS` (initially
  the probed `1.18.31`), exactly as `CLAUDE_SUPPORTED_BANNERS` does. A
  matching numeric prefix on a different product string is version drift.
- Widening the set requires a new evidence capture on the new version,
  recorded in the evidence file.

There is **no auth preflight** (unlike Claude). opencode has no single
subscription to witness; it fans out across configured providers. The
equivalent boundary is §5's compile-time model requirement, not a
`claude auth status` analogue.

### 5. Payer boundary — model is resolved and fail-closed at compile time (R-2)

The Claude backend's job was to stop a silent API-key reroute *away* from a
subscription. opencode's job is the inverse: the provider key **is** the
payer, and the only variable is *which one*. So:

- **Strip nothing.** opencode's provider credentials live in
  `~/.local/share/opencode/auth.json`, in `opencode.json` config, or in
  provider env vars. Stripping them (as the Claude backend strips Anthropic
  keys) would *break* auth, not protect a payer. `YAMLGRAPH_OTEL_DIR` layering
  (FR-363) is applied on top, unchanged.
- **Compile-time fail-closed model.** The model is resolved through the
  established priority chain — `cli_flags.model` > node `model` >
  `defaults.model` (ARCHITECTURE.md:1682-1690; `copilot_node.py:250-257`) —
  then `create_copilot_node` **rejects** an opencode node whose resolved model
  is absent **or** not a non-empty `provider/model` identifier, before the
  version probe or any subprocess. Substance, not only presence: `""`,
  `"model-only"`, `"/model"`, and `"provider/"` are rejected at compile and
  lint. The runtime receives the one resolved model and always emits
  `--model <resolved>`.
- **No config-default fallback.** The runtime never runs opencode without an
  explicit `--model`. There is no authorized path that lets an opencode
  configuration default choose the payer.

### 6. Result contract — no usage-limit classifier, frozen field set

`CopilotResult` field set is frozen (REQ-YG-087). No `total_cost_usd`,
`tokens`, or `reason` is added — `step_finish.tokens`/`cost` are logged at
DEBUG, not stored. `FileNotFoundError` → "opencode binary not found, on
PATH?"; `TimeoutExpired` → the shared mapping. An `error` event failure names
`error.name` and `error.data.message`; a non-event failure names the exit code
and a bounded stderr/stdout tail — never environment or credential contents.

### 7. Linter (`linter/patterns/copilot.py`)

| Code | Condition | Severity |
|---|---|---|
| `E-COPILOT-BACKEND-UNKNOWN` | `backend` not in the closed set (covers `opencode` once the tuple grows; one test) | error |
| `E-COPILOT-OPENCODE-FLAG-SHAPE` | any `OpenCodeCliFlags` validation failure (non-string `model`/`resume`, unknown key incl. the five dropped flags) | error |
| `E-COPILOT-OPENCODE-MODEL` | `backend: opencode` whose resolved model is absent or not a non-empty `provider/model` (`""`, `model-only`, `/model`, `provider/`) | error |
| `E-COPILOT-CLI-FLAGS` | opencode-only keys (`resume` on the `api` backend is already covered; the opencode set is shared with the `cli` backend so no new exclusivity) | error |

There is no `continue_session` for opencode (evidence §10), so the
`resume`/`continue_session` mutual-exclusion rule does not apply to this
backend.

### 8. Documentation and traceability

- `reference/graph-yaml.md` copilot section: the fifth enum value, the two
  typed flags, the stream state machine, the compile-time model rule and the
  absence of `continue_session`.
  `reference/getting-started.md:101`: "Copilot CLI, Claude Code CLI, or
  opencode CLI".
- `capabilities/CAP-30-copilot-node.yaml`: `fr: FR-082, FR-959, FR-1048`, plus
  the REQ ids below. `ARCHITECTURE.md` regenerated.
- Changelog fragment `changelog/unreleased/fr-1048-opencode-backend.md`
  (`type: feat`, `scope: copilot`, `req: REQ-YG-679`).
- `docs/confessions.md`: one CONF entry for the new `subprocess.run` site.

### Requirements (ADR-001; ids `max+1` at authoring = 679..681, re-derived at enforce)

- **REQ-YG-679** — Copilot node supports `backend: opencode`: list argv
  `opencode run <prompt> --format json --model <resolved>` (plus `--session`
  when `resume` is set) in the frozen order; stdout crosses a typed, fail-closed
  JSONL state machine (recognized events `step_start`/`text`/`tool_use`/
  `step_finish`/`error`; `step_finish.reason ∈ {stop, tool-calls}`; `stop` is
  the only terminal success) before `CopilotResult(backend="opencode")`;
  failure on unknown/malformed events, session-ID inconsistency, missing or
  duplicate terminal, non-`stop` reason, no text, any `error` event, non-zero
  exit, missing binary, timeout; no usage-limit classifier.
- **REQ-YG-680** — Copilot `backend` closed enum extended to `opencode` at
  schema, compile, and lint; unknown or non-string values fail before any
  subprocess; opencode flags are typed (`OpenCodeCliFlags`, strict, only
  `model`/`resume`) and malformed shapes or dropped flags fail at schema,
  compile, and lint before any probe; lint covers backend-incompatible flags
  and the compile-time model rule.
- **REQ-YG-681** — opencode backend payer boundary: the child environment is
  **not** stripped of provider credentials (they are the payer); the resolved
  model is a compile-time requirement (absent, empty, or non-`provider/model`
  values fail before any subprocess), emitted as `--model` on every run, and
  logged at DEBUG; there is no config-default fallback.

## Acceptance Criteria

- [ ] AC-01: the FR supersedes FR-546 for the `opencode` backend name,
  identifies as contrib/example "backend contribution", and carries only the
  `model` and `resume` flags.
- [ ] AC-02: `evidence/FR-1048-opencode-cli-probe.md` contains raw
  version/help, successful `--session` with nonce recall, `--continue`
  non-determinism, a tool-bearing stream, an error-event capture, and a
  no-stream session-failure capture for opencode 1.18.31; widening the banner
  or event set requires a new capture.
- [ ] AC-03: `backend: opencode` is the fifth accepted value at schema,
  compile, dispatch, and lint; misspelled, empty, and non-string values fail
  naming the five-value set before every subprocess, while `None` still
  selects `cli`.
- [ ] AC-04: `OpenCodeCliFlags` is strict and forbids extras; `resume` and
  `model` accept only strings (or `None` for `model`); the five dropped flags
  (`agent`, `dir`, `variant`, `thinking`, `auto`) and `continue_session` are
  rejected as extras; every invalid shape has direct schema, compile, and lint
  coverage before a probe.
- [ ] AC-05: model resolution follows `cli_flags.model` > node `model` >
  `defaults.model`; the resolved value must be a non-empty `provider/model`;
  `""`, `"model-only"`, `"/model"`, `"provider/"`, and absent all fail compile
  and lint before a probe; every accepted source produces the same
  `--model <resolved>` argv and `CopilotResult.model`.
- [ ] AC-06: exact argv equality covers
  `["opencode", "run", <one prompt element>, "--format", "json", "--model", <resolved>]`
  and `resume` → `--session` in the frozen order, with no shell.
- [ ] AC-07: every recognized stdout line crosses the typed state machine;
  ordered text, one consistent non-empty session ID, exactly one terminal
  `step_finish(reason="stop")`, and exit zero map to
  `CopilotResult(backend="opencode")`; `tool_use` and intermediate
  `step_finish(reason="tool-calls")` events are neutral and ignored for result
  assembly.
- [ ] AC-08: unknown/malformed events, malformed JSON lines, conflicting or
  missing session IDs, duplicate/missing terminal events, post-terminal
  events, no text, any `error` event, non-`stop` reason (outside
  `{stop, tool-calls}`), non-zero exit, missing binary, and timeout all raise
  without constructing a result or updating state.
- [ ] AC-09: error-event failures name `error.name` and `error.data.message`;
  non-event failures name the exit code and a bounded stderr/stdout tail,
  without logging environment or credential contents.
- [ ] AC-10: every opencode execution performs one exact-banner version probe
  immediately before one agent call with no cache; two node executions yield
  probe/call/probe/call ordering.
- [ ] AC-11: the version probe and agent call receive the same child
  environment; provider credential variables and `PATH` are retained, FR-363
  OTel scoping is retained when configured, and neither environment nor
  auth-file contents are logged.
- [ ] AC-12: direct lint tests cover unknown backend, missing/malformed model,
  malformed opencode flags, and dropped flags rejected as extras.
- [ ] AC-13: existing Copilot CLI, API, sampling, Claude, model-precedence,
  session, provider, OTel, and copilot-linter assertions still pass, except
  exact closed-set expectations updated from four values to five.
- [ ] AC-14: the gated disposable two-node witness proves the second argv uses
  the first real `session_id`, both streams report the same session ID, and
  the second output recalls a nonce supplied by the first node; the committed
  session-continuation demo remains untouched.
- [ ] AC-15: the invalid-session witness raises an error containing
  `Session not found` and the attempted id, returns no `CopilotResult`, and
  performs no state update.
- [ ] AC-16: CAP-30 carries the final re-derived requirement IDs,
  `ARCHITECTURE.md` is regenerated, references document the exact
  banner/event/model/payer contract, the confession covers the new subprocess
  site, the changelog cites the backend requirement, and
  `python scripts/req_coverage.py --strict` passes.

## Alternatives Considered (with dissent preserved)

| Alternative | Probe (2026-09-15) | Disposition | Dissent (strongest case against the disposition) |
|---|---|---|---|
| New node type `type: opencode` | 15 node types; `backend` exists to select the agent runtime (FR-383) | REJECTED — duplicates rendering, variables, guards, `CopilotResult` | Same naming lie as the Claude case: a `copilot` node running opencode. The honest fix is renaming the node `agent_cli`, a wider refactor this FR declines. |
| opencode server/SDK route (FR-546's design) | FR-546 [Judged, never enforced]: `opencode serve` + `httpx` + `json_schema` + agent sandbox | REJECTED for v1 and **superseded** for the backend name — a long-lived server is a second lifecycle plus an `httpx` dependency and a `CopilotResult` field change; the CLI reuses the `_execute_cli` seam with zero new deps | The server route buys schema-validated verdicts and a real permission sandbox — the two gaps `_execute_cli` cannot close. If structured output or sandboxing is the actual need, that is a *new* FR (FR-546's route is not concurrently authorized), not this one. |
| Route opencode via `backend: api` + `provider:` | `execute_prompt()` has no tools, no filesystem, `session_id=None` | REJECTED — loses the agent harness (tools, files, sessions) | For reasoning-only nodes it is strictly simpler and already exists. This FR does not replace it. |
| Keep `continue_session` (→ `--continue`) | evidence §10: `--continue` silently starts a new session in a dir with no prior session | REJECTED — non-deterministic, directory-scoped "last session" that can resume a human's interactive session; `--session <id>` fails loudly instead | `--continue` is what the `cli`/`claude` backends already do; dropping it is an inconsistency. But those backends bill a single session store; opencode's is shared with a human's interactive TUI. |
| Parse only the **last** JSON line instead of the full stream | the stream's first line is `step_start`, not the answer | REJECTED — drops ordered multi-`text` output and cannot see an early `error` | Stream parse is slightly more code, but it is the only way to satisfy Commandment 6 and not report a truncated answer as success. |

Is this a graph? No. It is a node backend; the witness graph is a disposable
fixture, and the committed consumer (`examples/demos/session-continuation`) is
untouched under this FR (FR-959 R-6 analogue).

## Kill criterion

If AC-14 cannot be witnessed on this host within one working session because
the pinned `--format json` stream cannot be parsed into a stable result and a
real `--session` continuation, REJECT this FR with the log attached. No
API-key injection, Copilot/claude-backend fallback, or weakened model-explicit
claim rescues the witness.

## Constraints

- Argv is a list, prompt is one element (REQ-YG-087; FR-948 R-1).
- Never log `os.environ`, the child env, or `auth.json` contents.
- `CopilotResult` shape frozen; fifth `backend` value only.
- Copilot, API, and Claude behaviour byte-identical (AC-13).
- New module `copilot_runtime_opencode.py` stays under 400 lines.
- Not authorized: FR-546's server/SDK route, `httpx`, structured output, a
  permission sandbox, the five dropped flags or `continue_session`,
  `allow_all_tools`/`allow_all_paths` mapping, any `CopilotResult` field
  change, a config-default model fallback, a new node type, edits to graphs or
  prompts, call-site adoption, enforcement infrastructure, `backend: sampling`,
  streaming, remote delegation, or any default/Copilot/API/Claude behaviour
  change.

## Out of Scope

- Any change to enforcement infrastructure (judge/review/author adapters) —
  a separate FR if a consumer swaps onto this backend (the FR-960 analogue).
- FR-546's server/SDK route (structured output, sandbox, `httpx`, server
  lifecycle) — superseded, not revived.
- `backend: sampling`; streaming; remote delegation (FR-948); a
  single-subscription auth preflight (until such a login exists); renaming
  `type: copilot`; the `continue_session`/`agent`/`dir`/`variant`/`thinking`/
  `auto` flags.

## Related

- `yamlgraph/node_factory/copilot_node.py`, `copilot_runtime.py`,
  `copilot_runtime_opencode.py` (new), `yamlgraph/linter/patterns/copilot.py`,
  `yamlgraph/models/node_schema.py`, `yamlgraph/models/schemas.py`,
  `capabilities/CAP-30-copilot-node.yaml`
- [evidence/FR-1048-opencode-cli-probe.md](evidence/FR-1048-opencode-cli-probe.md)
- opencode docs (pinned by the evidence, not by these links): CLI reference
  and headless mode at <https://opencode.ai/docs/cli/>

## Judgement

Pending re-judgement — sole route `scripts/judge.sh`. Not judged in the
author's session. Prior round: APPROVED WITH REVISIONS (R-1..R-5 folded).

## Implementation Status

- 2026-09-15: Proposed. Raw probe captures recorded inline in §Summary/§3/§5
  (version `1.18.31`, JSONL event shapes, exit-code and session behaviour);
  promotion to the committed evidence file is §AC-02. No code written.
- 2026-09-15: Research sole route run (`scripts/research.sh`, five personas,
  `FR-1048.research.md` promoted). Retrieval surfaced FR-546 (same territory,
  server/SDK route) — dispositioned in `**Prior art:**` and the alternatives
  table. Four personas pursue the CLI route; the subtractionist dissents.
- 2026-09-15: Judged APPROVED WITH REVISIONS (round 1). Revisions folded:
  R-1 (supersede FR-546, reclassify contrib/example, drop five convenience
  flags); R-2 (compile-time fail-closed model resolution, no config-default
  fallback); R-3 (evidence extended: raw `--help`, `--session` nonce recall,
  `--continue` non-determinism → `continue_session` dropped, tool-bearing event
  vocabulary → `tool_use` + `step_finish.reason ∈ {stop, tool-calls}` frozen);
  R-4 (typed fail-closed JSONL state machine); R-5 (nonce-recall witness +
  invalid-session assertion). Awaiting re-judgement.
