# FR-1048 opencode CLI probe — raw captures (pinned version 1.18.31)

**Prior art:** FR-959's evidence chain — `FR-959-claude-auth-probe.md`,
`FR-959-claude-backend-witness.md`, `FR-960-claude-judge-witness.md` — is the
Claude backend's analogue: the same "raw CLI probe" role, a different CLI.
`FR-1005-research-route-run-failures.md` and `FR-860-req-audit-run-scaffolding.md`
are "cli" noun matches only (research-route failure records; req-audit
scaffolding). None is a duplicate: this file pins the opencode CLI's contract,
which no prior record captures.

Raw captures recorded 2026-09-15 on the authoring host, `/usr/local/bin/opencode`.
Redaction: none required — the captures contain model ids, session ids, and
token counts, no credentials. This file pins the external contract the FR
freezes (§3/§5); widening the supported version set requires a new capture.

## §1 Version

```
$ opencode --version
1.18.31
```

## §2 Headless JSONL event stream (one-word prompt)

```
$ opencode run --format json --model inception/mercury-2.5 "reply with the single word: ok"
{"type":"step_start","timestamp":1789491050580,"sessionID":"ses_f5a05a0faffe3TbMvYHe3wGo2f","part":{"id":"prt_0a5fa7848001IMrWctxigSyXQ7","messageID":"msg_0a5fa61ad0011zCUwDaNJ7fT7g","sessionID":"ses_f5a05a0faffe3TbMvYHe3wGo2f","snapshot":"2353182d8f0c55f51d7bc39f4c2f92d04d38e38e","type":"step-start"}}
{"type":"text","timestamp":1789491050580,"sessionID":"ses_f5a05a0faffe3TbMvYHe3wGo2f","part":{"id":"prt_0a5fa784c001fz8AYJ4CvJeQK4","messageID":"msg_0a5fa61ad0011zCUwDaNJ7fT7g","sessionID":"ses_f5a05a0faffe3TbMvYHe3wGo2f","type":"text","text":"\n\nok","time":{"start":1789491050572,"end":1789491050576}}}
{"type":"step_finish","timestamp":1789491050735,"sessionID":"ses_f5a05a0faffe3TbMvYHe3wGo2f","part":{"id":"prt_0a5fa78e9001euO88QQIeWifGO","reason":"stop","snapshot":"2353182d8f0c55f51d7bc39f4c2f92d04d38e38e","messageID":"msg_0a5fa61ad0011zCUwDaNJ7fT7g","sessionID":"ses_f5a05a0faffe3TbMvYHe3wGo2f","type":"step-finish","tokens":{"total":8877,"input":8694,"output":4,"reasoning":179,"cache":{"write":0,"read":0}},"cost":0.00037521}}
```

Observations:

- stdout is **JSONL** — one JSON object per line, not a single envelope.
- `sessionID` is `ses_<…>` (not a UUID); present on every event.
- The answer is the concatenation of `text` events in order (`part.text`).
  This run emitted one `text` event; multi-`text` streams are expected and
  must be ordered.
- `step_finish` is terminal and carries `reason` (`"stop"`), `tokens`, `cost`.
- Exit code 0.

## §3 Error run — the failure signal is the `error` event

```
$ opencode run --format json --model nonexistent/probably "x"
{"type":"error","timestamp":1789491053013,"sessionID":"ses_f5a058081ffearrcyJGTf4ftU4","error":{"name":"UnknownError","data":{"message":"Unexpected server error. Check server logs for details.","ref":"err_62f454e7"}}}
exit=1
```

Observations: a failed run emits a terminal `error` event (with `error.name`
and `error.data.message`) **and** exits 1. The `error` event is the durable
failure signal; the exit code alone is not sufficient (see §4).

## §4 Session-not-found — no JSON event at all

```
$ opencode run --format json --session ses_nonexistent123 "ok"
Error: Session not found
exit=1
```

Observations: a resumption failure writes `Session not found` to stderr and
**no** JSON event to stdout, then exits 1. A stream with no terminal
`step_finish` and no `error` event is therefore a failure, not an empty
success (Commandment 6).

## §5 Default (non-`--format json`) output is not parseable

```
$ opencode run --model inception/mercury-2.5 "reply with the single word: ok"
> build · mercury-2.5

ok
```

Observations: the default formatter emits a header line (the model/title)
before the answer. A plain `stdout` read would pollute the result with the
header, so `--format json` is the only parseable contract.

## §6 Credentials — provider API keys, no subscription

```
$ opencode providers list
Credentials ~/.local/share/opencode/auth.json
  local      api
  Inception  api
  myprovider api
  DeepSeek   api
  4 credentials
```

Observations: opencode authenticates via per-provider **API keys** stored in
`~/.local/share/opencode/auth.json`. There is no subscription login and no
`auth status` command (`opencode providers` exposes only
`list`/`login`/`logout`). The payer is the provider key the child resolves,
not a single subscription — the inverse of the Claude backend's boundary.

## §7 CLI flags (from `opencode run --help`, v1.18.31)

Relevant to the frozen argv contract:

- `--format json` (default `default`) — JSONL event stream.
- `--model <provider/model>` — model selection; no `--format`-independent default.
- `--session <id>` / `--continue` — resume a named session / continue the last.
- `--agent <name>` — a named opencode agent.
- `--dir <path>` — working directory.
- `--variant <v>` — reasoning effort (e.g. `high`, `max`).
- `--thinking` — show thinking blocks.
- `--auto` — auto-approve permissions not explicitly denied (the CLI labels it
  dangerous).

No `--allow-all-paths` exists; `--dir` is the closest primitive and is a
positive directory choice, not a blanket grant.

## §8 Models (provider-scoped)

```
$ opencode models
opencode/big-pickle
opencode/ling-3.0-flash-fin-free
...
deepseek/deepseek-v4-pro
inception/mercury-2
inception/mercury-2.5
...
```

Model ids are `provider/model`. The resolved model is what the child bills;
there is no server-reported model id in the JSONL events (§2/§3), so the
selected model is witnessed by the `--model` argv the node passes, not by
reading the stream back.
