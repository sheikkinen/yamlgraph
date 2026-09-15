# Feature Request: FR-1048 `backend: opencode` — opencode CLI as a copilot-node backend (primitive)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-09-15
**First consumer / first event:** an operator who runs opencode (provider
keys in `~/.local/share/opencode/auth.json`, no Copilot seat, no Claude
subscription) runs the disposable two-node integration witness (§AC-12) with
`backend: opencode`, and gets a `CopilotResult` whose real `session_id` the
second node resumes byte-for-byte via `--session`. Second consumer, same
week: any graph that wants a provider-agnostic agent backend without a
vendor seat.
**Research:** [FR-1048.research.md](FR-1048.research.md) — the FR-890 sole
route (`scripts/research.sh`), brief
`feature-requests/research-briefs/fr-1048-opencode-backend-brief.md`, run
2026-09-15, five personas executed. Four of five converge on "fifth closed
enum value + JSONL stream reader"; the subtractionist dissents ("retire the
requirement / new node type"). Retrieval hit **FR-546** (same territory,
server/SDK route) — dispositioned in `**Prior art:**` below and in the
research record. Raw CLI probe captures are recorded inline in §Summary/§3/§5;
promotion to a committed `evidence/FR-1048-opencode-cli-probe.md` is §AC-01.
**Evidence:** [evidence/FR-1048-opencode-cli-probe.md](evidence/FR-1048-opencode-cli-probe.md)
— committed raw captures on the pinned version `1.18.31`: `opencode --version`,
the full `--format json` event stream for a one-word prompt, exit-code
behaviour on success and error, `--session` with a nonexistent id,
`opencode providers list`, and `opencode models`.
**Prior art:**
- [FR-546-opencode-copilot-backend.md](FR-546-opencode-copilot-backend.md)
  [Judged 2026-06-20, scope frozen, authority granted, never enforced] — the
  same "opencode as a copilot-node backend" territory via the **server/SDK
  route**: `opencode serve` HTTP surface, an `httpx` optional dependency,
  server lifecycle, `json_schema` structured output, agent-markdown permission
  sandbox, and a new `CopilotResult.structured_output` field. FR-546 predates
  FR-959; it was written before the CLI-subprocess backend pattern existed.
  This FR is the **CLI route**: `opencode run <prompt> --format json` as a
  subprocess, mirroring FR-959's `claude -p` seam exactly — no new dependency,
  no server lifecycle, no `CopilotResult` field change. Distinguished, not a
  duplicate: the server route buys structured output + sandbox at the cost of a
  second runtime surface; the CLI route buys a provider-agnostic agent backend
  at the cost of structured output. The Judge decides which route to enforce
  now; if FR-546's granted authority is the better precedent, this FR dies by
  it (FR-737). The subtractionist dissent below is FR-546's argument.
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
  / CAP-30 REQ-YG-105 — `resume`/`continue_session` reused 1:1, mapped to
  opencode's `--session`/`--continue`.
- [FR-363-per-node-otel-scoping-in-copilot-node.md](FR-363-per-node-otel-scoping-in-copilot-node.md)
  — `YAMLGRAPH_OTEL_DIR` layering preserved.

## Summary

Add a fifth, closed value `opencode` to the copilot node's `backend` enum.
It spawns opencode in print mode (`opencode run <prompt> --format json`),
parses the **JSONL event stream** (not a single envelope) through a private
accumulator into the existing `CopilotResult`, maps the shared `cli_flags`
keys plus four opencode-only, **typed** keys (`agent`, `dir`, `variant`,
`thinking`), and treats failure as: non-zero exit, a terminal `error` event,
or a `step_finish` with `reason != "stop"`. There is no subscription to
protect: the payer is the provider key the child opencode resolves, so the
boundary is *make the model explicit and witness it*, not *strip ambient
keys*. Unknown backend values and malformed opencode flags fail before any
subprocess, including the version probe. The linter learns the new value,
its flags, and their shapes.

## Value Statement

Graph authors who already run opencode get an agent backend that bills the
provider key they already configured, needs no vendor seat and no
subscription, selects its model through one `provider/model` value, and
fails loudly on a non-`stop` finish instead of silently returning whatever
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
   `--format json` emits a JSONL stream of `step_start` / `text` /
   `step_finish` / `error` events. A single `json.loads(stdout)` (the Claude
   path) would parse only the first line and silently drop the rest — a
   plausible-wrong-answer failure.
4. **Exit code is not the only signal** (mirrors FR-959 evidence §5). An
   error run can still carry exit 1, but the durable signal is the terminal
   `error` event; a run that hits a tool-permission refusal mid-stream must
   not be reported as success because the final line happened to parse.
5. **Payer is provider-key, not subscription.** There is no `claude auth
   status` equivalent whose `authMethod` proves who pays. The equivalent
   question is *which provider/model is the child going to bill*, and the
   only honest answers are: the `--model` we pass, or a config default we
   did not choose.

## Ideal Result

A graph author writes `backend: opencode` on any `type: copilot` node and
nothing else changes: same `prompt`, `variables`, `state_key`, `timeout`,
`cli_flags.model/resume/continue_session`; same `CopilotResult`, now with
`backend="opencode"` and a real `session_id`. A misspelled backend or a
malformed opencode flag is an error at lint and at compile, never an opencode
run and never a subprocess. Every opencode invocation first proves the CLI is
the supported version, and the model it will bill is either the explicitly
passed `--model` or a documented-and-linted default — never a silent surprise.
The result text is the concatenation of every `text` event in order, and any
run whose terminal event is an `error` or whose `step_finish.reason` is not
`stop` is a typed failure, not an empty or partial success.

## Proposed Solution

### 1. Closed backend enum

- `yamlgraph/models/schemas.py`: `COPILOT_BACKENDS = ("cli", "api", "sampling", "claude", "opencode")`.
- `yamlgraph/models/node_schema.py`: `backend: Literal["cli", "api", "sampling", "claude", "opencode"] | None`.
- `create_copilot_node` / `_execute_backend_once`: add the explicit `opencode`
  branch; the final branch remains `raise ValueError`. `normalize_backend`
  already reads `COPILOT_BACKENDS`, so the closed-set guard extends for free.
- Lint: `E-COPILOT-BACKEND-UNKNOWN` covers the new set automatically (it
  reads the same tuple; verify one new test).

### 2. Typed opencode flags

A private Pydantic model `OpenCodeCliFlags` (`extra="forbid"`, `strict=True`)
validates `cli_flags` **only when `backend == "opencode"`**; every other
backend keeps its current behaviour unchanged. Shared keys reuse the existing
`resume`/`continue_session` contract (FR-105) and map as:

| key | type | opencode flag | notes |
|---|---|---|---|
| `model` | `str` | `--model <provider/model>` | required to bill an explicit payer (§5) |
| `resume` | `str` | `--session <id>` | may be a `{state.…}` expression; resolves to the prior `CopilotResult.session_id` |
| `continue_session` | `bool` | `--continue` | exclusive with `resume` (existing rule) |
| `agent` | `str` | `--agent <name>` | opencode named agent |
| `dir` | `str` | `--dir <path>` | working directory for the run |
| `variant` | `str` | `--variant <v>` | reasoning effort (`high`, `max`, …); not validated against a fixed list (vendor-owned, changing) |
| `thinking` | `bool` | `--thinking` | show thinking blocks |
| `auto` | `bool` | `--auto` | auto-approve permissions not explicitly denied |

`allow_all_tools` → `--auto` is **deliberately not** mapped automatically:
opencode's permission model differs from Copilot's `--allow-all-tools`, and
auto-approving is a dangerous default (the CLI itself labels it so). A node
author opts in with the typed `auto: true`. `allow_all_paths` is **not
mapped**: opencode has no `--allow-all-paths`; `--dir` is the closest
primitive and is a positive directory choice, not a blanket grant. Both
non-mappings are recorded in `reference/graph-yaml.md`, not silently dropped.

Validation runs at schema load, again in `create_copilot_node` for the
linter-free dict path, and in lint as `E-COPILOT-OPENCODE-FLAG-SHAPE`. All
fire before the version probe and the agent subprocess.

### 3. `_execute_opencode` — argv frozen, stream accumulated

Lives in a new `yamlgraph/node_factory/copilot_runtime_opencode.py`
(`copilot_runtime.py` is 229 lines; the stream accumulator plus preflight
would push it past the 400 target). Same signature and return as
`_execute_cli` / `_execute_claude`. Argv frozen and tested byte-for-byte, in
this order:

```python
cmd = ["opencode", "run", prompt, "--format", "json"]
if flags.model:      cmd += ["--model", flags.model]
if resume:           cmd += ["--session", str(resume)]  # resolved via resolve_state_expression, as _execute_cli
elif flags.continue_session: cmd += ["--continue"]
if flags.agent:      cmd += ["--agent", flags.agent]
if flags.dir:        cmd += ["--dir", flags.dir]
if flags.variant:    cmd += ["--variant", flags.variant]
if flags.thinking:   cmd += ["--thinking"]
if flags.auto:       cmd += ["--auto"]
```

The prompt is one list element (REQ-YG-087; FR-948 R-1); no shell. The
message form (`opencode run <message>`) is used, not `--command` — the
positional message is the prompt.

#### Stream envelope (the one real difference from Claude)

stdout is JSONL. A private `_OpenCodeEvent` reader consumes it line by line
(`strict` Pydantic, `extra="ignore"` per event, since event shapes carry
extra `part.*`/`timestamp`/`tokens` fields):

- `sessionID` is captured from the first event that carries it (all events
  do; `ses_<…>`, not a UUID).
- `type == "text"` → append `part.text` in order to the result buffer.
- `type == "error"` → typed failure, regardless of exit code.
- `type == "step_finish"` → terminal; accept only if `reason == "stop"`.
  Any other `reason` (e.g. an aborted/max-turns finish) is a failure, not a
  partial success. (`reason` vocabulary is vendor-owned; the contract is
  "only `stop` is success", not an allow-list of failure strings.)
- A stream that ends with **no** `step_finish` (or no `text` events and no
  `error`) is a failure — never an empty substitute (Commandment 6).
- Non-zero exit with a parseable `error` event → `RuntimeError` naming the
  `error.name` and `error.data.message`; non-zero exit without one → name the
  exit code and the first 200 chars of the tail.

Success maps the concatenated text to `CopilotResult(output=…,
session_id=…, exit_code=0, backend="opencode", model=flags.model)`.

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
equivalent boundary is §5's model-explicit rule plus the documented residual,
not a `claude auth status` analogue.

### 5. Payer boundary — make the model explicit, witness what is chosen

The Claude backend's job was to stop a silent API-key reroute *away* from a
subscription. opencode's job is the inverse: the provider key **is** the
payer, and the only variable is *which one*. So:

- **Strip nothing.** opencode's provider credentials live in
  `~/.local/share/opencode/auth.json`, in `opencode.json` config, or in
  provider env vars. Stripping them (as the Claude backend strips Anthropic
  keys) would *break* auth, not protect a payer. `YAMLGRAPH_OTEL_DIR` layering
  (FR-363) is applied on top, unchanged.
- **Explicit model.** A `backend: opencode` node **must** set
  `cli_flags.model` (or a node/graph-level `model`) as `provider/model`; an
  omitted model means the child's `opencode.json` default decides the payer.
  Lint: `E-COPILOT-OPENCODE-MODEL` (error) when no model signal is present —
  the strict analogue of REQ-YG-357's API-backend warning, promoted to error
  because the payer is a real provider key, not a session default.
- **Witness what was chosen** at DEBUG: log the resolved `--model` string.
  This is not a preflight; it is an honest record of what the child was told
  to bill. It cannot detect a config default we did not choose — that is
  exactly what the lint error prevents.
- **Residual (enumerated in `reference/graph-yaml.md`):** a config default in
  `opencode.json`/`~/.config/opencode/` can still be selected if the lint
  error is bypassed; `opencode providers login` (OAuth) vs a plain API key
  are both "provider key" to this boundary and are treated identically. The
  residual is documented, not hidden.

### 6. Result contract — no usage-limit classifier, frozen field set

`CopilotResult` field set is frozen (REQ-YG-087). No `total_cost_usd`,
`tokens`, or `reason` is added — `step_finish.tokens`/`cost` are logged at
DEBUG, not stored. `FileNotFoundError` → "opencode binary not found, on
PATH?"; `TimeoutExpired` → the shared mapping.

### 7. Linter (`linter/patterns/copilot.py`)

| Code | Condition | Severity |
|---|---|---|
| `E-COPILOT-BACKEND-UNKNOWN` | `backend` not in the closed set (already covers `opencode` once the tuple grows; one test) | error |
| `E-COPILOT-OPENCODE-FLAG-SHAPE` | any `OpenCodeCliFlags` validation failure (non-string `model`/`agent`/`dir`/`variant`, non-bool `thinking`/`auto`, unknown key) | error |
| `E-COPILOT-OPENCODE-MODEL` | `backend: opencode` with no `model` signal (node `model`, `defaults.model`, or `cli_flags.model`) | error |
| `E-COPILOT-CLI-FLAGS` | opencode-only keys (`agent`, `dir`, `variant`, `thinking`, `auto`) on `cli` backend (joins the existing claude-only-key rule) | error |
| `E-COPILOT-API-FLAGS` | the same keys on `api` backend | error |
| `W-COPILOT-OPENCODE-AUTO` | `auto: true` (dangerous approval default; author opts in, linter still calls it out) | warning |

Existing `resume`/`continue_session` mutual exclusion applies unchanged.

### 8. Documentation and traceability

- `reference/graph-yaml.md` copilot section: the fifth enum value, the flag
  table with types and the `--auto`/`--dir` non-mappings, the stream envelope,
  the model-explicit payer rule and the residual.
  `reference/getting-started.md:101`: "Copilot CLI, Claude Code CLI, or
  opencode CLI".
- `capabilities/CAP-30-copilot-node.yaml`: `fr: FR-082, FR-959, FR-1048`, plus
  the REQ ids below. `ARCHITECTURE.md` regenerated.
- Changelog fragment `changelog/unreleased/fr-1048-opencode-backend.md`
  (`type: feat`, `scope: copilot`, `req: REQ-YG-679`).
- `docs/confessions.md`: one CONF entry for the new `subprocess.run` site.

### Requirements (ADR-001; ids `max+1` at authoring = 679..681, re-derived at enforce)

- **REQ-YG-679** — Copilot node supports `backend: opencode`: list argv
  `opencode run <prompt> --format json` with the frozen flag mapping
  (`--model`, `--session`/`--continue`, `--agent`, `--dir`, `--variant`,
  `--thinking`, `--auto`); stdout crosses a JSONL stream reader
  (`sessionID`, ordered `text` accumulation, `error`, `step_finish`) before
  `CopilotResult(backend="opencode")`; failure on non-zero exit, `error`
  event, non-`stop` `reason`, stream with no terminal `step_finish`, missing
  binary, timeout; no usage-limit classifier.
- **REQ-YG-680** — Copilot `backend` closed enum extended to `opencode` at
  schema, compile, and lint; unknown or non-string values fail before any
  subprocess; opencode-only flags are typed (`OpenCodeCliFlags`) and malformed
  shapes fail at schema, compile, and lint before any probe; lint covers
  backend-incompatible flags and the model-explicit rule.
- **REQ-YG-681** — opencode backend payer boundary: the child environment is
  **not** stripped of provider credentials (they are the payer); a
  `backend: opencode` node must carry an explicit `provider/model` model
  signal (lint error otherwise) so the billed provider is chosen by the graph,
  not a config default; the resolved `--model` is logged at DEBUG; the
  config-default residual is enumerated in docs.

## Acceptance Criteria

Offline (mocked `subprocess.run`; no binary, no network):

- [ ] AC-01: `evidence/FR-1048-opencode-cli-probe.md` is committed (complete
  as of this FR) and freezes one argv contract with no conditional fallback;
  any widening of the supported version set adds a new capture to that file.
- [ ] AC-02: `backend: opencode`, `backend: opnecode`, `backend: 3`,
  `backend: ""` behave exactly as the closed set demands — the misspellings
  and non-strings fail schema/compile/lint naming the five accepted values,
  before any subprocess; `None` defaults to `cli`; `cli`, `api`, `sampling`
  (`NotImplementedError`), `claude`, `opencode` keep their behaviour.
- [ ] AC-03: exact argv tests (list equality) cover prompt + `--format json`,
  `model` → `--model provider/model`, resolved `resume` → `--session`,
  `continue_session` → `--continue`, `agent` → `--agent`, `dir` → `--dir`,
  `variant` → `--variant`, `thinking` → `--thinking`, `auto` → `--auto`; order
  as §3.
- [ ] AC-04: stream reader tests — `step_start`+`text`+`step_finish(stop)`
  maps text and `sessionID`; two `text` events concatenate in order; an
  `error` event raises naming `name`/`message` regardless of exit 0; a
  `step_finish` with `reason != "stop"` raises; a stream with no terminal
  `step_finish` raises; non-JSON stdout raises; an empty `result` with no
  `error` raises (Commandment 6).
- [ ] AC-05: every invalid shape in §2 (non-string member, non-bool switch,
  unknown key) fails at schema and lint before version or agent subprocess,
  one direct test each.
- [ ] AC-06: two node executions → two version probes, two agent calls, in
  that order each time; no module-level cache.
- [ ] AC-07: with `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`
  set in the parent, the `env` kwarg of the opencode subprocess **keeps**
  them all (they are the payer, not a reroute), keeps `PATH`, and carries the
  FR-363 OTel path when `YAMLGRAPH_OTEL_DIR` is set.
- [ ] AC-08: `E-COPILOT-OPENCODE-MODEL` fires when no `model` signal exists;
  it is silent when `cli_flags.model`, node `model`, or `defaults.model`
  carries a `provider/model` value.
- [ ] AC-09: exit 1 and exit 0-with-error-event are typed failures; no
  `OpenCodeUsageLimitError`, reset-time parser, or refusal regex exists in the
  package (grep-checked).
- [ ] AC-10: every lint code in §7 has one direct test.
- [ ] AC-11: every existing test in `tests/unit/test_copilot_node*.py` and
  `test_linter_patterns_copilot.py` passes unmodified; default dispatch,
  Copilot argv, API path, Claude path, session, provider, OTel and lint
  behaviour unchanged.

Live (each recorded in `evidence/FR-1048-opencode-backend-witness.md`):

- [ ] AC-12: a disposable two-node integration harness
  (`tests/integration/test_fr1048_opencode_backend_live.py`, gated by
  `YAMLGRAPH_LIVE_OPENCODE=1`) writes a temporary graph in `tmp_path` with two
  `type: copilot` / `backend: opencode` nodes, one-word prompts, the second
  node's `resume` bound to the first result's `session_id`. It passes when the
  second argv carries `--session` with the first node's real `session_id`
  byte-for-byte. The committed `examples/demos/session-continuation/**` is
  **not** modified. The witness records command, temp-graph digest,
  `opencode --version`, the resolved model, both argv lists (redacted), both
  session IDs, result heads, limitations.
- [ ] AC-13: the same harness with a nonexistent `--session` id refuses
  before producing a result and the error names what it saw.
- [ ] AC-14: CAP-30 carries REQ-YG-679..681, `ARCHITECTURE.md` regenerated,
  references document the fifth value, the stream envelope, and the
  model-explicit payer contract, changelog fragment cites REQ-YG-679, and
  `python scripts/req_coverage.py --strict` passes.

## Alternatives Considered (with dissent preserved)

| Alternative | Probe (2026-09-15) | Disposition | Dissent (strongest case against the disposition) |
|---|---|---|---|
| New node type `type: opencode` | 15 node types; `backend` exists to select the agent runtime (FR-383) | REJECTED — duplicates rendering, variables, guards, `CopilotResult` | Same naming lie as the Claude case: a `copilot` node running opencode. The honest fix is renaming the node `agent_cli`, a wider refactor this FR declines. |
| Route opencode via `backend: api` + `provider:` | `execute_prompt()` has no tools, no filesystem, `session_id=None` | REJECTED — loses the agent harness (tools, files, sessions) | For reasoning-only nodes it is strictly simpler and already exists. This FR does not replace it. |
| Add opencode as a `claude`-style alias with a subscription auth check | `opencode providers list` shows API-key creds only; no `auth status` command exists | REJECTED — there is no subscription to witness; the payer is per-provider | If opencode later ships a single-subscription login (a "zen" seat), the Claude auth-preflight pattern would transfer 1:1. Until then §5's model-explicit rule is the honest boundary. |
| opencode server/SDK route (FR-546's design) | FR-546 [Judged, never enforced]: `opencode serve` + `httpx` + `json_schema` structured output + agent-markdown sandbox | REJECTED for v1 — a long-lived server is a second lifecycle (port, auth, teardown) plus an `httpx` dependency and a `CopilotResult` field change; the CLI reuses the `_execute_cli` seam with zero new deps | The server route buys schema-validated verdicts and a real permission sandbox — the two gaps `_execute_cli` cannot close. If structured output or sandboxing is the actual need, FR-546's granted authority is the precedent and this FR dies by it (FR-737). This FR only wins if the need is "a second CLI harness and payer", which is exactly FR-959's proof. |
| Parse only the **last** JSON line instead of the full stream | the stream's first line is `step_start`, not the answer | REJECTED — drops ordered multi-`text` output and cannot see an early `error` | Stream parse is slightly more code, but it is the only way to satisfy Commandment 6 and not report a truncated answer as success. |

Is this a graph? No. It is a node backend; the witness graph is a disposable
fixture, and the committed consumer (`examples/demos/session-continuation`) is
untouched under this FR (FR-959 R-6 analogue).

## Kill criterion

If AC-12 cannot be witnessed on this host within one working session because
the pinned `--format json` stream cannot be parsed into a stable result and a
resumable `session_id`, REJECT this FR with the log attached. No API-key
injection, Copilot/claude-backend fallback, or weakened model-explicit claim
rescues the witness.

## Constraints

- Argv is a list, prompt is one element (REQ-YG-087; FR-948 R-1).
- Never log `os.environ`, the child env, or `auth.json` contents.
- `CopilotResult` shape frozen; fifth `backend` value only.
- Copilot, API, and Claude behaviour byte-identical (AC-11).
- New module `copilot_runtime_opencode.py` stays under 400 lines.
- Not authorized: edits to `.github/skills/**` adapters, `scripts/*.sh`,
  `backend: sampling`, streaming, remote delegation, `CopilotResult` fields,
  renaming `type: copilot`, or any default/Copilot/API/Claude behaviour change.

## Out of Scope

- Any change to enforcement infrastructure (judge/review/author adapters) —
  a separate FR if a consumer swaps onto this backend (the FR-960 analogue).
- `backend: sampling`; streaming; remote delegation (FR-948); an opencode
  server/SDK backend; a single-subscription auth preflight (until such a login
  exists); renaming `type: copilot`.

## Related

- `yamlgraph/node_factory/copilot_node.py`, `copilot_runtime.py`,
  `copilot_runtime_opencode.py` (new), `yamlgraph/linter/patterns/copilot.py`,
  `yamlgraph/models/node_schema.py`, `yamlgraph/models/schemas.py`,
  `capabilities/CAP-30-copilot-node.yaml`
- [evidence/FR-1048-opencode-cli-probe.md](evidence/FR-1048-opencode-cli-probe.md)
- opencode docs (pinned by the evidence, not by these links): CLI reference
  and headless mode at <https://opencode.ai/docs/cli/>

## Judgement

Pending — sole route `scripts/judge.sh`. Not judged in the author's session.

## Implementation Status

- 2026-09-15: Proposed. Raw probe captures recorded inline in §Summary/§3/§5
  (version `1.18.31`, JSONL event shapes, exit-code and session behaviour);
  promotion to the committed evidence file is §AC-01. No code written.
- 2026-09-15: Research sole route run (`scripts/research.sh`, five personas,
  `FR-1048.research.md` promoted). Retrieval surfaced FR-546 (same territory,
  server/SDK route) — dispositioned in `**Prior art:**` and the alternatives
  table. Four personas pursue the CLI route; the subtractionist dissents
  (retire / new node type), which is FR-546's argument. Awaiting judgement.
