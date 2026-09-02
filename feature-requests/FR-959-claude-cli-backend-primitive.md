# Feature Request: FR-959 `backend: claude` — Claude Code CLI as a copilot-node backend (primitive)

**Priority:** MEDIUM
**Type:** Feature
**Status:** **Implemented 2026-09-02** on branch `feat/fr-959-claude-backend` (judged the same day — APPROVED WITH REVISIONS, [judgement](FR-959-claude-cli-backend-primitive.judgement.md); R-1..R-6 folded; C-1 probe incl. capture (a) committed; C-2 Option A signed; live witness [evidence/FR-959-claude-backend-witness.md](evidence/FR-959-claude-backend-witness.md)). Open: AC-15's logged-out half (see witness §Limitations). FR-960's gate (C-2 there) requires this on **main**.
**Effort:** 1.5 days
**Requested:** 2026-09-02
**First consumer / first event:** an operator on a host with Claude Code logged in on a subscription and **no** GitHub Copilot seat runs the disposable two-node integration witness (§AC-14) with `backend: claude`, and gets a `CopilotResult` whose real `session_id` the second node resumes byte-for-byte. Second consumer, same week: FR-960 swaps the judge adapter onto this backend.
**Research:** in-body dispositioned alternatives table below, with a *Dissent* column preserving the strongest disagreement per row (FR-958 judgement R-7; FR-952/FR-954 precedent for the in-body route). Every probe executed 2026-09-02 on this host or cites a committed record.
**Evidence:** [evidence/FR-959-claude-auth-probe.md](evidence/FR-959-claude-auth-probe.md) — redacted raw captures on the pinned CLI version (judgement R-1): auth status under every observed credential/routing switch, settings `env` precedence, `--tools` grammar, print-mode failure envelope. Capture (a), the browser subscription login, is owed by the operator (§6 of the evidence file).
**Prior art:**
- [FR-958-claude-code-cli-backend-for-copilot-node.md](FR-958-claude-code-cli-backend-for-copilot-node.md) [SPLIT 2026-09-02] and its [judgement](FR-958-claude-code-cli-backend-for-copilot-node.judgement.md) — the parent. This FR is deliverable D-1 and folds R-2, R-3, R-4, R-5, R-6, and the research half of R-7. It contains no judge-adapter, wrapper, or enforcement-infrastructure change (that is FR-960).
- [FR-081-copilot-node.md](FR-081-copilot-node.md) [Implemented] — created `type: copilot` and the `backend` field. Extended, not duplicated.
- [FR-383-copilot-node-backend-api-fallback.md](FR-383-copilot-node-backend-api-fallback.md) [Implemented] — one `_execute_*` per backend, `CopilotResult.backend` stamped, backend-aware lint (REQ-YG-356/357). Structural template followed exactly.
- [054-copilot-cli-reflection.md](054-copilot-cli-reflection.md) [Implemented 2026-02-20] — REJECTED `claude -p` because OAuth expired on one workstation. Distinguished: this FR does not assume that changed; it makes non-interactive subscription auth a witnessed, per-invocation criterion with a kill criterion, and forbids the API-key rescue (different payer).
- [FR-329-agent-sdk-planner-spike.md](FR-329-agent-sdk-planner-spike.md) [Implemented] — in-process Agent SDK spike, scoped to not touch the copilot runtime. Dispositioned in the table as the future `sampling` successor, rejected here.
- [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md) [Judged] — transport concern, did not touch CAP-30. Inherited discipline: byte-for-byte argv tests (its R-1), verify by artifact never by exit code.
- [FR-105](FR-105-copilot-session-continuations.md) / CAP-30 REQ-YG-105 — `resume`/`continue_session` keys reused 1:1.
- [FR-363](FR-363-per-node-otel-scoping-in-copilot-node.md) — `YAMLGRAPH_OTEL_DIR` layering preserved on the stripped child environment.

## Summary

Add a fourth, closed value `claude` to the copilot node's `backend` enum.
It spawns Claude Code in print mode (`claude -p <prompt> --output-format json`),
maps the shared `cli_flags` keys plus three claude-only, **typed** keys
(`tools`, `allowed_tools`, `max_turns`), parses the JSON envelope through a
private Pydantic model into the existing `CopilotResult`, and guards the
payer **on every invocation**: the child environment is stripped of the
observed API-key, bearer, base-URL and cloud-provider switches, then a
fail-closed preflight checks the exact CLI version and requires
`claude auth status` to report a subscription method before each `-p` call.
Enumerated settings-file surfaces can still reroute the payer after the
preflight; that residual is documented and signed by the spend owner (§Human
decisions). Unknown backend values and malformed Claude flags fail before any
subprocess, including the probes. The linter learns the new value, its flags,
and their shapes.

## Value Statement

Graph authors who run Claude Code get an agent backend that loads `CLAUDE.md`
natively, needs no Copilot seat, strips the observed ambient payer switches,
and verifies subscription authentication immediately before each invocation,
so the invoice lands on the Claude subscription unless an enumerated settings
surface has been deliberately configured to say otherwise.

## Problem

Unchanged from FR-958 §Problem items 1, 3, and 4, restated minimally:

1. `type: copilot` is the only agent-invoking node and its `cli` backend is
   hard-wired to the `copilot` binary (`yamlgraph/node_factory/copilot_runtime.py:92`).
   Twelve agentic graphs depend on one vendor seat.
2. `docs/diary/diary-2026-05-31-letter-to-the-philosopher.md:326` claims the
   node invokes "VS Code Copilot or Claude CLI". No such path exists.
3. **Dispatch is open** (FR-958 judgement R-5): `NodeConfig.backend` is an
   unrestricted `str` (`yamlgraph/models/node_schema.py:107-109`), non-strings
   normalize to `cli`, and every unknown string falls through to
   `_execute_cli` (`copilot_node.py:183-191,227-228`). `backend: cluade`
   succeeds today by running Copilot. Adding a fourth value on top of an
   open enum would widen that hole.
4. **Flags are untyped** (FR-959 judgement R-4): `cli_flags` is
   `dict[str, Any]`; a string where a list is expected, or `max_turns: true`,
   would be silently mis-rendered or dropped by Python truthiness.

## Ideal Result

A graph author writes `backend: claude` on any `type: copilot` node and
nothing else changes: same `prompt`, `variables`, `state_key`, `timeout`,
`cli_flags.model/resume/continue_session`; same `CopilotResult`, now with
`backend="claude"` and a real `session_id`. A misspelled backend or a
malformed Claude flag is an error at lint and at compile, never a Copilot run
and never a subprocess. Every Claude invocation first proves the CLI is the
supported version and is authenticated on the subscription; when it cannot
prove that, it refuses before the agent prompt. The one payer window that
remains — a settings-file surface changing credentials between the preflight
and the call — is written down and signed, not hidden.

## Proposed Solution

### 1. Closed backend enum (FR-958 R-5; judgement AC-02)

- `yamlgraph/models/node_schema.py`: `backend: Literal["cli", "api", "sampling", "claude"] | None`.
- `create_copilot_node`: normalize once; anything outside the set (including
  non-strings and `""`) raises `ValueError(f"Copilot node '{name}': unknown backend {value!r}; expected one of ...")`
  at compile time, before any node function exists. `None` alone defaults to `cli`.
- `_execute_backend_once`: explicit dispatch on the four values; the final
  branch is `raise ValueError`, not `return _execute_cli(...)`.
- Lint: `E-COPILOT-BACKEND-UNKNOWN` for the same condition (schema catches
  it first when the graph is loaded through Pydantic; the lint rule exists
  for the linter's own dict path, REQ-YG-357 style).

### 2. Typed Claude flags (judgement R-4)

A private Pydantic model `ClaudeCliFlags` (`extra="forbid"`) validates
`cli_flags` **only when `backend == "claude"`**; other backends keep the
untyped dict and their exact current behaviour (AC-13):

| key | type | notes |
|---|---|---|
| `model` | `str` | alias or full id |
| `resume` | `str` | may be a `{state.…}` expression |
| `continue_session` | `bool` | exclusive with `resume` (existing rule) |
| `tools` | `list[str]` | `[]` is meaningful: **no tools** (`--tools ""`) |
| `allowed_tools` | `list[str]` | approval only |
| `allow_all_tools` | `bool` | broad approval |
| `allow_all_paths` | `bool` | `--add-dir <cwd>` |
| `max_turns` | `int`, `> 0`, `strict` | rejects `True`, `0`, negatives, `"40"` |

Validation runs at schema load (a `model_validator` on `NodeConfig`), again
in `create_copilot_node` for the linter-free dict path, and in lint as
`E-COPILOT-CLAUDE-FLAG-SHAPE`. All three fire before the version probe, the
auth probe, and the agent subprocess. No truthiness shortcuts: a malformed
value is an error, never an omitted flag.

### 3. `_execute_claude` — argv frozen from the pinned version (R-1)

Lives in a new `yamlgraph/node_factory/copilot_runtime_claude.py`
(`copilot_runtime.py` is 192 lines; the preflight plus envelope would push
it past the 400 target). Same signature and return as `_execute_cli`. Argv
frozen and tested byte-for-byte, in this order:

```python
cmd = ["claude", "-p", prompt, "--output-format", "json"]
if flags.model:                      cmd += ["--model", flags.model]
if resume:                           cmd += ["--resume", str(resume)]   # resolved via resolve_state_expression, as _execute_cli
elif flags.continue_session:         cmd += ["--continue"]
if flags.tools is not None:          cmd += ["--tools", ",".join(flags.tools)]       # [] → ""  (evidence §4.1)
if flags.allow_all_tools:            cmd += ["--dangerously-skip-permissions"]
elif flags.allowed_tools:            cmd += ["--allowedTools", ",".join(flags.allowed_tools)]
if flags.allow_all_paths:            cmd += ["--add-dir", str(Path.cwd())]
if flags.max_turns:                  cmd += ["--max-turns", str(flags.max_turns)]
```

#### Tool contract (FR-958 R-2), one observed form

| `cli_flags` key | Meaning | Claude flag (evidence §4) | Copilot backend |
|---|---|---|---|
| `tools: [A, B]` | which tools **exist**; `[]` means none | `--tools "A,B"`; `--tools ""` | `E-COPILOT-CLI-FLAGS` |
| `allowed_tools: [A, B]` | which existing tools run **without a permission prompt** | `--allowedTools "A,B"` | `E-COPILOT-CLI-FLAGS` |
| `allow_all_tools: true` | approve everything that exists | `--dangerously-skip-permissions` | `--allow-all-tools` |

The grammar is pinned from `claude --help` on 2.1.255: `--tools` takes a
comma-separated list of built-in tool names and `""` disables all tools
(evidence §4, verbatim). The pre-judgement `--disallowedTools` fallback is
**deleted**; there is one form. `--max-turns` is accepted by the parser on
2.1.255 but absent from its `--help` (evidence §4.3); the exact-version pin
in §4 is what keeps that mapping honest.

A node that sets `allowed_tools` without `tools` gets every default tool
available and only the listed ones auto-approved; in print mode an
un-approved tool call fails rather than prompts. The linter warns
(`W-COPILOT-CLAUDE-APPROVE-WITHOUT-RESTRICT`).

Not mapped, deliberately: `--bare` (drops CLAUDE.md discovery and OAuth —
evidence §4), `--no-session-persistence` (kills `session_id`),
`--permission-mode` (subsumed by the two keys), `--system-prompt*` (prompts
live in YAML), `--max-budget-usd` (metered-API concept), `--settings` /
`--setting-sources` / `--restricted` (§Human decisions Option B territory).

### 4. Per-invocation preflight: version, then auth (judgement R-2, R-3)

No cache. Every Claude node execution runs, in order, with the **same
stripped environment** (§5) as the agent call:

1. `claude --version` → stdout must be exactly `2.1.255 (Claude Code)`
   (evidence §1). Accepted set `CLAUDE_SUPPORTED_VERSIONS = {"2.1.255"}`;
   anything else raises `RuntimeError` naming the observed and accepted
   versions, before the auth probe. Widening the set requires a new
   evidence capture on the new version, recorded in this FR.
2. `claude auth status` (JSON is the default) → must exit 0 and parse into a
   private `_ClaudeAuthStatus` model with `loggedIn: bool`,
   `authMethod: str`, `apiProvider: str`. Accepted iff `loggedIn` is true,
   `apiProvider == "firstParty"`, and `authMethod` is in
   `CLAUDE_SUBSCRIPTION_AUTH_METHODS`. That set contains `oauth_token`
   (evidence §2.7, setup-token "requires Claude subscription") and the
   browser-login value **once capture (a) is committed**; until then the
   browser-login case fails closed. Observed refusals: `none` (§2.1),
   `api_key` (§2.2, §3), `third_party` (§2.4). Non-zero exit, unparseable
   JSON, or a missing binary raise `RuntimeError` naming what was seen.

Two node executions produce two version probes, two auth probes, two agent
calls (AC-06). The probes share one helper; the helper has no module state.

### 5. Payer boundary — strip what is owned, witness what is not (R-2)

- **Strip** (derived from evidence §7, not from a fixed guess): child env is
  `os.environ` minus `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
  `ANTHROPIC_BASE_URL`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`,
  `CLAUDE_CODE_USE_FOUNDRY`. `CLAUDE_CODE_OAUTH_TOKEN` and `PATH` are kept;
  FR-363's `YAMLGRAPH_OTEL_DIR` layering is applied on top, unchanged.
- **Witness**: §4 step 2, per invocation.
- **Residual** (enumerated in `reference/graph-yaml.md`): user, project,
  local, and managed settings `env` blocks (evidence §3 shows a settings
  block alone selects `api_key`); `apiKeyHelper`; enterprise cloud-provider
  settings. The preflight *detects* these states after settings are applied;
  it cannot prevent a change made between the preflight and the `-p` call.
- **Lint**: `provider:` on a claude-backend node → `E-COPILOT-CLAUDE-PROVIDER`.

### Human decisions (judgement R-2, C-2 — GATE; the enforcer may not infer consent)

| Option | Consequence | Recommendation |
|---|---|---|
| **A** — accept the enumerated residual | Wording throughout this FR stays as written above ("strips observed ambient payer switches and verifies subscription auth immediately before each invocation; enumerated settings changes can still reroute"). Implementation proceeds. | **Recommended** — minimal, honest, one probe |
| **B** — preserve an absolute subscription-only claim | Requires a separately proved controlled-settings boundary (`--setting-sources` / `--restricted` precedence proofs, or managed policy); that is its own FR and this FR blocks on it. | Correct long-term; not the minimal path |

**Residual payer boundary accepted (Option A) by:** sheikkinen (repository owner and spend owner), 2026-09-02 — decision given in the enforcing session after the two options were laid out; recorded here by the enforcer verbatim ("A").

### 6. Result contract — typed envelope (R-5, FR-958 R-4/R-6)

A private `_ClaudeEnvelope(BaseModel)` with `result: str`, `session_id: str`,
`is_error: bool = False` (extra keys ignored) is the boundary between Claude's
stdout and `CopilotResult`:

- exit 0 and stdout parses into `_ClaudeEnvelope` with `is_error` false →
  `CopilotResult(output=result, session_id=session_id, exit_code=0,
  backend="claude", model=flags.model)`.
- `is_error: true` → `RuntimeError` regardless of exit code (evidence §5:
  `subtype` reads `"success"` on a failed run; only `is_error` signals).
- exit ≠ 0 → `RuntimeError` naming the node, the exit code, and the first
  200 chars of `result` if stdout parsed, else of stderr. **No numeric
  subtype is interpreted.**
- exit 0 with stdout that is not a JSON object, a JSON array, missing
  `result`, non-string `result`, missing/non-string `session_id`, or
  non-boolean `is_error` → `RuntimeError`, never an empty substitute
  (Commandment 6; NC-414). State is not updated in any failure.
- `FileNotFoundError` → "claude binary not found, on PATH?"; `TimeoutExpired`
  → same mapping as Copilot.
- **No usage-limit classifier**. A subscription cooldown surfaces as the
  generic `is_error`/non-zero failure. `total_cost_usd` logged at DEBUG as
  "notional"; not added to `CopilotResult` (field set frozen).

### 7. Linter (`linter/patterns/copilot.py`)

| Code | Condition | Severity |
|---|---|---|
| `E-COPILOT-BACKEND-UNKNOWN` | `backend` not in the closed set (incl. non-string, `""`) | error |
| `E-COPILOT-CLAUDE-FLAG-SHAPE` | any `ClaudeCliFlags` validation failure (string for list, non-string member, `max_turns` ≤ 0 / bool / string, non-bool switch, unknown key) | error |
| `E-COPILOT-CLI-FLAGS` | `tools`/`allowed_tools`/`max_turns` on `cli` backend | error |
| `E-COPILOT-API-FLAGS` | the same three keys on `api` (joins the existing list) | error |
| `E-COPILOT-CLAUDE-PROVIDER` | `provider:` on `claude` backend | error |
| `W-COPILOT-CLAUDE-TOOLS` | `allow_all_tools` together with `allowed_tools` (narrow list dead) | warning |
| `W-COPILOT-CLAUDE-APPROVE-WITHOUT-RESTRICT` | `allowed_tools` without `tools` | warning |
| `W-COPILOT-CLAUDE-MODEL` | model matches Copilot-only pattern (`gpt-*`, `*-sol`) | warning |

Existing `resume`/`continue_session` mutual exclusion applies unchanged.

### 8. Documentation and traceability

- `reference/graph-yaml.md` copilot section: enum, flag table with types and
  the availability/approval split, per-invocation preflight, the exact
  supported version, residual payer list and the signed option.
  `reference/getting-started.md:101`: "Copilot CLI or Claude Code CLI".
- `capabilities/CAP-30-copilot-node.yaml`: `fr: FR-082, FR-959`, plus the
  REQ ids below. `ARCHITECTURE.md` regenerated.
- Changelog fragment `changelog/unreleased/fr-959-claude-backend.md`
  (`type: feat`, `scope: copilot`, `req: REQ-YG-639`).
- `docs/confessions.md`: one CONF entry for the new `subprocess.run` sites.
- `docs/diary/diary-2026-05-31-letter-to-the-philosopher.md:326` becomes
  true; no edit.

### Requirements (ADR-001; ids `max+1` at authoring = 639..641, re-derived at enforce)

- **REQ-YG-639** — Copilot node supports `backend: claude`: list argv
  `claude -p <prompt> --output-format json` with the frozen flag mapping
  (`--tools` comma grammar, `--allowedTools`, `--dangerously-skip-permissions`,
  `--add-dir`, `--max-turns`, `--model`, `--resume`/`--continue`); stdout
  crosses a private typed envelope (`result: str`, `session_id: str`,
  `is_error: bool`) before `CopilotResult(backend="claude")`; failure on
  non-zero exit, `is_error`, malformed envelope, missing binary, timeout; no
  numeric exit subtype interpreted; no usage-limit classifier.
- **REQ-YG-640** — Copilot `backend` is a closed enum (`cli`, `api`,
  `sampling`, `claude`) at schema, compile, and lint; unknown or non-string
  values fail before any subprocess; Claude-only flags are typed
  (`ClaudeCliFlags`) and malformed shapes fail at schema, compile, and lint
  before any probe; lint covers backend-incompatible flags,
  approval-vs-availability, provider-on-claude, and Copilot-only models.
- **REQ-YG-641** — Claude backend payer boundary, per invocation: child env
  stripped of the evidenced credential and routing switches; exact
  supported-version check then fail-closed subscription auth-status check,
  both pinned to the committed raw probe and both run before every `-p`
  call with no cache; residual settings surface enumerated in docs and
  accepted by a named spend owner.

## Acceptance Criteria (revised by the judgement; C-n = gate)

Offline (mocked `subprocess.run`; no binary, no network):

- [ ] AC-01 (C-1, C-5): `evidence/FR-959-claude-auth-probe.md` names the
  supported CLI version and contains the auth, settings-precedence,
  environment-key, tool-grammar, and empty-tool-list observations; this FR
  freezes one argv contract with no conditional fallback. Capture (a) is
  recorded as owed with the operator command; the preflight fails closed on
  it until committed.
- [ ] AC-02 (C-3): `backend: cluade`, `backend: 3`, `backend: ""` fail
  schema/compile and lint with the four accepted values named, before any
  subprocess; `None` alone defaults to `cli`; `cli`, `api`, `sampling`
  (`NotImplementedError`, unchanged), `claude` keep their behaviour.
- [ ] AC-03: exact argv tests (list equality) cover prompt/output format,
  model, resolved `resume`, `continue_session`, `tools: [Read, Grep]` →
  `--tools`, `Read,Grep`; `tools: []` → `--tools`, `""`; `allowed_tools`
  → `--allowedTools`; `allow_all_tools` → `--dangerously-skip-permissions`
  and no `--allowedTools`; `allow_all_paths` → `--add-dir <cwd>`;
  `max_turns: 40` → `--max-turns`, `40`; order as §3.
- [ ] AC-04: a test asserts `--allowedTools` is never the only tool flag when
  `tools` is set; `W-COPILOT-CLAUDE-TOOLS` fires for broad+narrow; the
  reference text names both flags and the distinction.
- [ ] AC-05 (C-3): every invalid shape in §2 (string for list, non-string
  member, `max_turns` 0 / -1 / `True` / `"40"`, non-bool switch, unknown
  key) fails at schema and lint before version, auth, or agent subprocess,
  one direct test each.
- [ ] AC-06 (C-4): two node executions → two version probes, two auth
  probes, two agent calls, in that order each time; no module-level cache.
- [ ] AC-07: with `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
  `ANTHROPIC_BASE_URL`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`,
  `CLAUDE_CODE_USE_FOUNDRY` set in the parent, the `env` kwarg of **all
  three** subprocess calls lacks every one, keeps `PATH` and
  `CLAUDE_CODE_OAUTH_TOKEN`, and carries the FR-363 OTel path when
  `YAMLGRAPH_OTEL_DIR` is set.
- [ ] AC-08 (C-2): the §Human decisions line is signed with Option A or B by
  the named spend owner; all billing wording matches the signed option.
- [ ] AC-09: preflight acceptance/refusal fixtures are the evidence file's
  captures: `oauth_token`+firstParty proceeds; `none`, `api_key`,
  `third_party`/bedrock, malformed JSON, non-zero exit, missing binary, and
  version `2.1.254 (Claude Code)` each fail before `-p`, naming what was seen.
- [ ] AC-10 (C-6): envelope success maps `result`/`session_id`; JSON array,
  missing `result`, non-string `result`, missing/non-string `session_id`,
  non-boolean `is_error`, `is_error: true` (with `subtype: "success"`, as
  observed), non-zero exit, timeout, non-JSON stdout each raise without a
  state update.
- [ ] AC-11: exit 1 and exit 7 are generic; no symbol `ClaudeUsageLimitError`,
  reset-time parser, or refusal regex exists in the package (grep-checked).
- [ ] AC-12: every lint code in §7 has one direct test.
- [ ] AC-13: every existing test in `tests/unit/test_copilot_node*.py` and
  `test_linter_patterns_copilot.py` passes unmodified; default dispatch,
  Copilot argv, API path, session, provider, OTel and lint behaviour unchanged.

Live (each recorded in `evidence/FR-959-claude-backend-witness.md`; C-7):

- [ ] AC-14 (C-7): a disposable two-node integration harness
  (`tests/integration/test_fr959_claude_backend_live.py`, gated by
  `YAMLGRAPH_LIVE_CLAUDE=1`) writes a temporary graph in `tmp_path` with two
  `type: copilot` / `backend: claude` nodes, `tools: []`, prompts that only
  ask for a one-word reply, the second node's `resume` bound to the first
  result's `session_id`. It passes when the second argv carries `--resume`
  with the first node's real `session_id` byte-for-byte. The committed
  `examples/demos/session-continuation/**` is **not** modified or executed.
  The witness records command, temp-graph digest, `claude --version`, auth
  method as reported by the preflight, timestamps, both redacted argv lists,
  both session IDs, result heads, limitations.
- [ ] AC-15 (C-8): the same harness with `ANTHROPIC_API_KEY=sk-invalid-on-purpose`
  exported still succeeds (the key never reaches the child); with the login
  removed the preflight refuses before any `-p` call and the error names the
  auth method it saw.
- [ ] AC-16: CAP-30 carries REQ-YG-639..641, `ARCHITECTURE.md` regenerated,
  references document the exact supported version and residual payer
  contract, changelog fragment cites REQ-YG-639, and
  `python scripts/req_coverage.py --strict` passes.

## Alternatives Considered (with dissent preserved)

| Alternative | Probe (2026-09-02) | Disposition | Dissent (strongest case against the disposition) |
|---|---|---|---|
| New node type `type: claude` | `sed -n 10,27p yamlgraph/constants.py`: 15 node types; `backend` exists to select the agent runtime (FR-383) | REJECTED — duplicates rendering, variables, guards, `CopilotResult` | A `copilot` node called "copilot" that runs Claude is a naming lie; the honest fix is renaming the node type `agent_cli`, which is a wider refactor this FR declines. Recorded, not resolved. |
| In-process Agent SDK (`claude-agent-sdk`) backend | FR-329 spike; `docs/plan-research-dependency-negative-space.md:27`: SDK imported only by an undeclared example | REJECTED — new runtime dependency and a second permission model in core; the CLI reuses the `_execute_cli` seam | The SDK gives tool-approval callbacks and typed messages, which would make the payer preflight and the tool contract *in-process assertions* instead of argv tests against a moving CLI. It is the better long-term boundary; it is not the minimal one. Natural successor for `sampling`. |
| Route Claude via Copilot CLI `--model claude-*` (status quo) | `.chaplain/graphs/watcher-plan/step-judge-v2.yaml:24` already does this | REJECTED as the only option — changes weights, keeps harness, permissions, seat | It already works, costs nothing new, and avoids a second auth surface. If the goal were only "a Claude-weighted judge", this would win. The goal is a second harness and payer. |
| `backend: api` with `provider: anthropic` | `copilot_node.py:359-398`: `execute_prompt()`, no tools, `session_id=None` | REJECTED — no tools, no filesystem, API payer | For reasoning-only nodes it is strictly simpler and already exists. This FR does not replace it. |
| Fall back to `ANTHROPIC_API_KEY` when the login is missing | `grep -n ANTHROPIC_API_KEY reference/development-operations.md`: key provisioned repo-wide | REJECTED — silent payer switch | Availability: a fallback would make the backend work on every dev host today. The FR trades availability for an honest invoice; some operators would take the other trade. They can, explicitly, via FR-958's follow-on reroute design. |
| Narrow settings via `--setting-sources` / `--restricted` instead of witnessing auth | evidence §4 (`--restricted` "ignores user, project and local settings files (managed settings and --settings still apply)") | REJECTED for v1 (= Option A) — we would then have to prove the flag's precedence too; witnessing the outcome is one probe | Narrowing is *preventive*; witnessing is *detective*. A preflight that passes and a settings `env` that flips the key one second later is a real window. The dissent is right that both belong eventually; it is Option B in §Human decisions. |
| Once-per-process auth cache (pre-judgement text) | judgement R-2 | REJECTED — a cached pass outlives logout, settings edits, `apiKeyHelper` changes | Two extra subprocesses per node call (each ~150 ms, evidence §5 durations) is a real cost on a 40-node graph. Accepted: correctness of the payer claim over 300 ms. |

Is this a graph? No. It is a node backend; the witness graph is a disposable
fixture, and the committed consumer (`examples/demos/session-continuation`)
is untouched under this FR (judgement R-6).

## Kill criterion (C-8)

If AC-14 cannot be witnessed on a provisioned host (subscription login, pinned
version) within one working session because print mode cannot authenticate
on the subscription login, or the pinned version's `--tools` grammar cannot
express the contract, or a real `session_id` is not resumable, FR-054's
objection stands: REJECT this FR with the log attached and correct the
2026-05-31 diary line to "Copilot CLI". No API key, cloud provider, Copilot
backend, or weakened billing claim rescues the witness.

## Constraints

- Argv is a list, prompt is one element (REQ-YG-087; FR-948 R-1).
- Never log `os.environ` or the child env.
- `CopilotResult` shape frozen; fourth `backend` value only.
- Copilot and API behaviour byte-identical (AC-13).
- New module `copilot_runtime_claude.py` stays under 400 lines.
- Host fact: on the authoring host `claude` is not on PATH; the desktop app
  bundles `%APPDATA%/Claude/claude-code/2.1.255/claude.exe` (evidence header).
  The witness records how PATH was extended.
- Not authorized (judgement): edits to `.github/skills/judge-fr/**`,
  `scripts/judge.sh`, FR-960 surfaces, committed graph or prompt YAML,
  `examples/demos/session-continuation/**`, `backend: sampling`, usage-limit
  classifier or wait/reroute, streaming, remote delegation, settings-file
  mutation, managed policy, new dependencies, `CopilotResult` fields,
  renaming `type: copilot`, or any default/Copilot/API behaviour change.

## Out of Scope

- Any change to `.github/skills/judge-fr/**`, `scripts/judge.sh`, or other
  enforcement infrastructure (FR-960; blocked until this FR is Implemented
  and human-reviewed — judgement C-9).
- `backend: sampling`; streaming; remote delegation (FR-948); usage-limit
  wait/reroute (FR-958 §Follow-on); review/author adapter migration.
- Renaming `type: copilot` (dissent row 1). Option B's controlled-settings
  boundary (its own FR if signed).

## Related

- `yamlgraph/node_factory/copilot_node.py`, `copilot_runtime.py`,
  `copilot_runtime_claude.py` (new), `yamlgraph/linter/patterns/copilot.py`,
  `yamlgraph/models/node_schema.py`, `yamlgraph/models/schemas.py`,
  `capabilities/CAP-30-copilot-node.yaml`
- [evidence/FR-959-claude-auth-probe.md](evidence/FR-959-claude-auth-probe.md)
- Claude Code docs (pinned by the evidence, not by these links): headless
  <https://code.claude.com/docs/en/headless>, CLI reference
  <https://code.claude.com/docs/en/cli-reference>, settings
  <https://code.claude.com/docs/en/settings>, env vars
  <https://code.claude.com/docs/en/env-vars>

## Judgement (2026-09-02)

**Verdict:** APPROVED WITH REVISIONS — [FR-959-claude-cli-backend-primitive.judgement.md](FR-959-claude-cli-backend-primitive.judgement.md)
(sole route `scripts/judge.sh`, Copilot CLI gpt-5.6-sol, session
`2e931a2b-851f-4ae8-aa34-55d5dcdb0fba`; not the author's session).

**Folded 2026-09-02:** R-1 (probe committed, one `--tools` form, fallback
deleted), R-2 (no cache, evidence-derived strip set, Human decisions block),
R-3 (exact-version preflight), R-4 (`ClaudeCliFlags`), R-5 (`_ClaudeEnvelope`),
R-6 (disposable two-node witness; demo untouched). Acceptance criteria
replaced by the judgement's revised set.

**Gates open at fold time:** C-1 capture (a) owed by the operator (evidence
§6); C-2 spend-owner signature (§Human decisions). D-1/D-3/D-4 RED tests may
be committed; D-2 production code waits for both.

## Implementation Status

- 2026-09-02: judgement folded; evidence file committed; branch
  `feat/fr-959-claude-backend`.
- 2026-09-02: RED committed (`tests/unit/test_fr959_claude_backend.py`,
  `tests/unit/test_fr959_claude_lint.py`; 90 failing, 10 unchanged-behaviour
  guards passing; existing copilot suites 39 passed / 12 skipped, untouched).
  Every fixture is a string from the evidence file. Production module
  `copilot_runtime_claude.py`, schema/lint changes, docs, CAP-30, changelog
  (D-2, D-3, D-6) **not started**: gated on C-1 capture (a) — operator runs
  the §6 command of the evidence file — and C-2 — spend owner signs Option A
  or B in §Human decisions. Diary:
  `docs/diary/diary-2026-09-02-reflection-fr-959-960-the-gate-the-enforcer-cannot-open.md`.
- 2026-09-02 (later, same session): C-2 satisfied — spend owner chose
  **Option A** in the enforcing session; signed above. GREEN committed:
  - `yamlgraph/models/schemas.py`: `COPILOT_BACKENDS`, `CLAUDE_ONLY_CLI_FLAGS`,
    `ClaudeCliFlags` (strict, extra forbidden).
  - `yamlgraph/models/node_schema.py`: `backend` is `Literal[...]`; after-validator
    runs `ClaudeCliFlags` for copilot nodes with `backend: claude`.
  - `yamlgraph/node_factory/copilot_runtime.py`: `normalize_backend`,
    `unknown_backend_message`, and `_resolve_resume` extracted from
    `_execute_cli` (shared with the Claude backend; Copilot argv unchanged).
  - `yamlgraph/node_factory/copilot_runtime_claude.py` (new, 290 lines):
    env strip, per-invocation version + auth preflight (no module state),
    frozen argv, `_ClaudeEnvelope`, `_execute_claude`.
  - `yamlgraph/node_factory/copilot_node.py`: closed dispatch (`claude`,
    `cli`, else `ValueError`); compile-time flag validation. 417 lines
    (target 400, max 450 — the two new imports and the explicit `cli` branch
    are the growth; noted, not split).
  - `yamlgraph/linter/patterns/copilot.py`: all §7 codes.
  - Docs: `reference/graph-yaml.md` Claude section, `reference/getting-started.md`;
    CAP-30 (`fr: FR-082, FR-959`, REQ-YG-639/640/641); `ARCHITECTURE.md`
    regenerated; changelog fragment; CONF-452.
  - Verification: FR-959 + copilot suites 139 passed / 12 skipped;
    `ruff check` clean; `lint-imports` 3 kept; `validate_capabilities --strict`
    and `req_coverage.py --strict` pass. Full fast unit suite result recorded
    in the GREEN commit message.
  - `tests/integration/test_fr959_claude_backend_live.py`: the AC-14 harness,
    gated by `YAMLGRAPH_LIVE_CLAUDE=1`; **not yet run** — needs capture (a).
- 2026-09-02 (evening): operator logged in from PowerShell and pasted
  capture (a): `authMethod: "claude.ai"`, `subscriptionType: "team"`
  (evidence §2.3; email/orgId redacted). Accepted set pinned to
  `{"claude.ai", "oauth_token"}`; AC-09 test extended. Live witness run
  twice from the enforcing session with the MSIX binary on PATH:
  AC-14 passed (real `session_id` resumed byte-for-byte, `--tools ""`
  accepted, version+auth probes before each `-p`); AC-15 API-key half passed
  with `ANTHROPIC_API_KEY=sk-invalid-on-purpose` exported. Record:
  `evidence/FR-959-claude-backend-witness.md`. **Status → Implemented.**
- **Open:** AC-15 logged-out half (enforcer may not run `claude auth logout`;
  raw capture + unit fixture cover the refusal path; live re-run command in
  the witness §Limitations). `copilot_node.py` at 417 lines (> 400 target).
  FR-960 unblocks when this branch is merged to main.

### Acceptance record

| AC | State | Where |
|---|---|---|
| AC-01..AC-05, AC-07, AC-09..AC-13 | passed (offline) | `tests/unit/test_fr959_claude_backend.py`, `tests/unit/test_fr959_claude_lint.py`; 141 targeted tests green |
| AC-06 | passed (offline + live) | unit `test_version_then_auth_then_agent_on_every_invocation`; witness argv[1..6] |
| AC-08 | passed | §Human decisions, Option A signed |
| AC-14 | **passed live** | witness run 1 and run 2 |
| AC-15 | passed for the API-key half; logged-out half by raw capture + unit fixture, live re-run owed | witness §Limitations |
| AC-16 | passed | CAP-30, `ARCHITECTURE.md`, `reference/graph-yaml.md`, changelog fragment; `req_coverage.py --strict` and `validate_capabilities.py --strict` green |
