# Problem brief: operators whose agent is opencode have no copilot-node backend

**Prior art:** the "backend/brief" noun matches below are vocabulary collisions,
not precedents — `fr-926-error-surfacing-problem-brief.md` (error surfacing),
`fr982-unit-suite-traces-live-brief.md` (unit-suite tracing),
`judge-round-sentinel.md` and `review-round-sentinel.md` (round sentinels),
`pi-agent-runtime-brief.md` (PI agent runtime). None shares the
opencode-backend problem; the substantive prior art (FR-546 server/SDK route,
FR-959 CLI route) is dispositioned in the FR itself.

## Problem statement

`type: copilot` is the only agent-invoking node in the graph, and its
`backend` field is a closed enum of four values: `cli` (GitHub Copilot CLI, a
seat), `api` (provider API via `execute_prompt()`, no tools, no filesystem,
no `session_id`), `sampling` (unimplemented), and `claude` (Claude Code CLI on
a subscription, FR-959). There is no path for an operator whose agent is
opencode and whose only credentials are provider API keys.

Two facts distinguish opencode from the backends that already exist, and both
were witnessed live this session (opencode 1.18.31, `/usr/local/bin/opencode`):

1. **Its headless output is a JSONL stream, not a single envelope.** `opencode
   run <prompt> --format json` emits one line per event — `step_start`
   (carrying `sessionID`), one or more incremental `text` events (the answer),
   a terminal `step_finish` (carrying `reason`, `tokens`, `cost`), and on
   failure an `error` event. The Claude backend's contract is a single JSON
   object (`result`/`session_id`/`is_error`); a single `json.loads(stdout)`
   against opencode parses only the first line and drops the answer.

2. **Its payer model is provider keys, not a subscription.** `opencode
   providers list` reports API-key credentials in
   `~/.local/share/opencode/auth.json` (this host: `local`, `Inception`,
   `DeepSeek`, `myprovider`). There is no `opencode auth status` analogue whose
   `authMethod` proves who pays; the question is instead *which provider/model
   the child will bill*. The Claude backend's whole payer boundary is built to
   protect a subscription from an ambient API-key reroute; that logic does not
   transfer.

## Classification

judgement/analysis/generation

## Constraints

- **Closed enum**: `backend` is a `Literal` (FR-959 REQ-YG-640). A fifth value
  must ride the same exact-match, typed-flag, fail-before-subprocess
  discipline; a naive `else: _execute_cli` would regress the closed set.
- **`CopilotResult` shape frozen** (REQ-YG-087): `output`, `exit_code`,
  `model`, `backend`, `session_id`. A new backend maps into this; it does not
  extend it.
- **Argv is a list, prompt is one element** (REQ-YG-087; FR-948 R-1); no
  shell; no `os.environ` or `auth.json` contents are ever logged.
- **Exit code is not the only failure signal.** Witnessed: a bad-model run
  exits 1 *and* emits a terminal `error` event; the durable signal is the
  event, not the code. A run that dies mid-stream must not be reported as
  success because its last line happened to parse.
- **Payer boundary is inverted vs. Claude.** opencode has no subscription to
  protect; the provider key *is* the payer. Any boundary must make the chosen
  provider/model explicit, not strip ambient credentials (stripping would
  break auth).
- **Version pin**: the CLI banner must be pinned and widened only on a new
  evidence capture, exactly as `CLAUDE_SUPPORTED_BANNERS`.
- **No new node type.** The existing `type: copilot` carries rendering,
  variables, guards, and `CopilotResult`; a new value extends it. (The naming
  lie — a "copilot" node running opencode — is recorded but the wider
  `agent_cli` rename is out of scope for the primitive.)
- **Doctrine**: this is a node backend, not a graph (`is_this_a_graph`).

## Witnessed incidents

- 2026-09-15, opencode 1.18.31: `opencode run --format json --model
  inception/mercury-2.5 "reply with the single word: ok"` emitted four JSONL
  lines — `step_start` (`sessionID: ses_f5a120d3affeGbukIlEa2wuFPl`), a `text`
  event (`part.text: "\n\nok"`), a second `text` event, and `step_finish`
  (`reason: "stop"`, `tokens`, `cost`). Exit 0. The answer is the ordered
  concatenation of `text` events; `sessionID` is `ses_<…>`, not a UUID.
- 2026-09-15: `opencode run --format json --model nonexistent/probably "x"`
  exited 1 and emitted a single `error` event
  (`error.name: "UnknownError"`, `error.data.message`). The failure signal is
  the `error` event, not (only) the exit code.
- 2026-09-15: `opencode run --format json --session ses_nonexistent123 "ok"`
  exited 1 with `Session not found` on stderr and **no** JSON event — a
  resumption failure produces no stream to parse.
- 2026-09-15: default (non-`--format json`) `opencode run` prints a header line
  (`> build · mercury-2.5`) then the answer — the header would pollute a plain
  `stdout` read, so `--format json` is the only parseable path.
- 2026-09-15: `opencode providers list` reports 4 API-key credentials; no
  subscription/auth-status command exists in the CLI (`opencode providers`
  has only `list`/`login`/`logout`).

## Deliverable sought

A ranked set of viable opencode-as-backend approaches, each with: the frozen
argv contract; how the JSONL stream maps to `CopilotResult` (and what a
non-`stop` finish or missing terminal event means); how `resume`/
`continue_session` map to `--session`/`--continue`; how the provider/model is
made explicit (vs. a config default deciding the payer); whether an auth
preflight exists at all; and a live two-node witness design. Each stated with
enough precision to become the FR-1048 body + acceptance criteria.
