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

## §7 Raw `opencode run --help` (v1.18.31)

```
$ opencode run --help
opencode run [message..]

run opencode with a message

Positionals:
  message  message to send                                                     [array] [default: []]

Options:
  -h, --help         show help                                                             [boolean]
  -v, --version      show version number                                                   [boolean]
      --print-logs   print logs to stderr                                                  [boolean]
      --log-level    log level                  [string] [choices: "DEBUG", "INFO", "WARN", "ERROR"]
      --pure         run without external plugins                                          [boolean]
      --command      the command to run, use message for args                               [string]
  -c, --continue     continue the last session                                             [boolean]
  -s, --session      session id to continue                                                 [string]
      --fork         fork the session before continuing (requires --continue or --session) [boolean]
      --share        share the session                                                     [boolean]
  -m, --model        model to use in the format of provider/model                           [string]
      --agent        agent to use                                                           [string]
      --format       format: default (formatted) or json (raw JSON events)
                                          [string] [choices: "default", "json"] [default: "default"]
  -f, --file         file(s) to attach to message                                            [array]
      --title        title for the session (uses truncated prompt if no value provided)     [string]
      --attach       attach to a running opencode server (e.g., http://localhost:4096)      [string]
  -p, --password     basic auth password (defaults to OPENCODE_SERVER_PASSWORD)             [string]
  -u, --username     basic auth username (defaults to OPENCODE_SERVER_USERNAME or 'opencode')
                                                                                            [string]
      --dir          directory to run in, path on remote server if attaching                [string]
      --port         port for the local server (defaults to random port if no value provided)
                                                                                            [number]
      --variant      model variant (provider-specific reasoning effort, e.g., high, max, minimal)
                                                                                            [string]
      --thinking     show thinking blocks                                                  [boolean]
  -i, --interactive  run in direct interactive split-footer mode          [boolean] [default: false]
      --auto         auto-approve permissions that are not explicitly denied (dangerous!)
                                                                          [boolean] [default: false]
```

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

## §9 Successful `--session <id>` resume (with nonce recall)

Working directory: the worktree root. Command, complete stdout, and exit
status, unedited (no ellipses):

```
$ opencode run --format json --model inception/mercury-2.5 "my name is probe; remember this: NONCE-7419"
{"type":"step_start","timestamp":1789491699364,"sessionID":"ses_f59fbb04effetBRETURmQKxx8H","part":{"id":"prt_0a6045e9800168m2LDw6AgzPIN","messageID":"msg_0a6045210001rVyN0AEufjnwK6","sessionID":"ses_f59fbb04effetBRETURmQKxx8H","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","type":"step-start"}}
{"type":"text","timestamp":1789491699364,"sessionID":"ses_f59fbb04effetBRETURmQKxx8H","part":{"id":"prt_0a6045e9c001avYFZ1ttrMvi8q","messageID":"msg_0a6045210001rVyN0AEufjnwK6","sessionID":"ses_f59fbb04effetBRETURmQKxx8H","type":"text","text":"\n\nHello probe. I've noted NONCE-7419. How can I help you today?","time":{"start":1789491699356,"end":1789491699360}}}
{"type":"step_finish","timestamp":1789491699528,"sessionID":"ses_f59fbb04effetBRETURmQKxx8H","part":{"id":"prt_0a6045f43001qn7iNPXUWBV6Fi","reason":"stop","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","messageID":"msg_0a6045210001rVyN0AEufjnwK6","sessionID":"ses_f59fbb04effetBRETURmQKxx8H","type":"step-finish","tokens":{"total":9150,"input":8710,"output":27,"reasoning":413,"cache":{"write":0,"read":0}},"cost":0.0004144}}
exit=0
```

Second invocation resumes that exact session id (complete stdout, exit 0):

```
$ opencode run --format json --model inception/mercury-2.5 --session ses_f59fbb04effetBRETURmQKxx8H "what is my name and what NONCE did I give you? reply in one line"
{"type":"step_start","timestamp":1789491704762,"sessionID":"ses_f59fbb04effetBRETURmQKxx8H","part":{"id":"prt_0a60473aa001LtCavv7rT6Qxps","messageID":"msg_0a60468ce001xxA9BhTasV5JVq","sessionID":"ses_f59fbb04effetBRETURmQKxx8H","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","type":"step-start"}}
{"type":"text","timestamp":1789491704762,"sessionID":"ses_f59fbb04effetBRETURmQKxx8H","part":{"id":"prt_0a60473ae001JEzT314sUUT3gr","messageID":"msg_0a60468ce001xxA9BhTasV5JVq","sessionID":"ses_f59fbb04effetBRETURmQKxx8H","type":"text","text":"\n\nYour name is probe and you provided NONCE-7419.","time":{"start":1789491704750,"end":1789491704756}}}
{"type":"step_finish","timestamp":1789491704928,"sessionID":"ses_f59fbb04effetBRETURmQKxx8H","part":{"id":"prt_0a604745b001r14XNYEfdwRRFJ","reason":"stop","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","messageID":"msg_0a60468ce001xxA9BhTasV5JVq","sessionID":"ses_f59fbb04effetBRETURmQKxx8H","type":"step-finish","tokens":{"total":9316,"input":9021,"output":22,"reasoning":273,"cache":{"write":0,"read":0}},"cost":0.00040509}}
exit=0
```

Observations: `--session <id>` resumes deterministically — the second stream
carries the **same** `sessionID`, and the model recalls the prior-session
nonce. Every event carries `sessionID` at the top level **and** inside `part`.
This is the resumption contract the FR's `resume` flag maps to. A missing id
fails loudly (§4); an explicit id is the only safe resumption.

## §10 `--continue` is directory-scoped and silently non-deterministic

Working directory: `tmp/oc-disposable` (fresh, no prior session). Command,
complete stdout, and exit status:

```
$ opencode run --format json --model inception/mercury-2.5 --continue "what was the nonce I gave you earlier? reply one line"
{"type":"step_start","timestamp":1789492130411,"sessionID":"ses_f59faea28ffe1I9uKQvZLizXs7","part":{"id":"prt_0a60af24f001rsGCe1HC6DqatA","messageID":"msg_0a60ae4700011LFJERuHbe1HuX","sessionID":"ses_f59faea28ffe1I9uKQvZLizXs7","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","type":"step-start"}}
{"type":"text","timestamp":1789492130411,"sessionID":"ses_f59faea28ffe1I9uKQvZLizXs7","part":{"id":"prt_0a60af253001t6VCnDsA7DBVJE","messageID":"msg_0a60ae4700011LFJERuHbe1HuX","sessionID":"ses_f59faea28ffe1I9uKQvZLizXs7","type":"text","text":"\n\nYou haven't provided a nonce earlier in this conversation.","time":{"start":1789492130387,"end":1789492130403}}}
{"type":"step_finish","timestamp":1789492130536,"sessionID":"ses_f59faea28ffe1I9uKQvZLizXs7","part":{"id":"prt_0a60af2e2001gxeUaPp29SuG30","reason":"stop","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","messageID":"msg_0a60ae4700011LFJERuHbe1HuX","sessionID":"ses_f59faea28ffe1I9uKQvZLizXs7","type":"step-finish","tokens":{"total":9137,"input":8849,"output":12,"reasoning":276,"cache":{"write":0,"read":0}},"cost":0.00039716}}
exit=0
```

Observations: `--continue` resolves "the last session" against opencode's
session store scoped to the working directory; with no prior session there it
starts a **new** session (`ses_f59faea28ffe1I9uKQvZLizXs7`, not the §9 id) with
no error and no prior context. That is the opposite of `--session <id>`'s
fail-loud behaviour (§4). A node's `--continue` would resume whatever
interactive session a human last ran in that directory — a non-deterministic,
unsafe default. **The FR therefore drops `continue_session` and keeps only the
explicit `resume` → `--session`.**

## §11 Tool-bearing run — full event vocabulary

Working directory: `tmp/oc-disposable` containing `hello.txt` = `hello tool
world`. Command, complete stdout, and exit status:

```
$ opencode run --format json --model inception/mercury-2.5 "read the file hello.txt in this directory and tell me its exact contents in one line"
{"type":"step_start","timestamp":1789492152602,"sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","part":{"id":"prt_0a60b4911001JlUHR24K82ay26","messageID":"msg_0a60b3f44001In1auH1jhK3NUK","sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","type":"step-start"}}
{"type":"tool_use","timestamp":1789492152646,"sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","part":{"type":"tool","tool":"read","callID":"call_237fad6b865f4a9bb7d81809","state":{"status":"completed","input":{"filePath":"/Users/sheikki/Documents/src/yamlgraph/tmp/worktrees/feat/fr-1048-opencode-backend/tmp/oc-disposable/hello.txt"},"output":"<path>/Users/sheikki/Documents/src/yamlgraph/tmp/worktrees/feat/fr-1048-opencode-backend/tmp/oc-disposable/hello.txt</path>\n<type>file</type>\n<content>\n1: hello tool world\n\n(End of file - total 1 lines)\n</content>","metadata":{"preview":"hello tool world","truncated":false,"loaded":[],"display":{"type":"file","path":"/Users/sheikki/Documents/src/yamlgraph/tmp/worktrees/feat/fr-1048-opencode-backend/tmp/oc-disposable/hello.txt","text":"hello tool world","lineStart":1,"lineEnd":1,"totalLines":1,"truncated":false}},"title":"tmp/oc-disposable/hello.txt","time":{"start":1789492152621,"end":1789492152642}},"id":"prt_0a60b4915001yZuDHyEWMVYmOL","sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","messageID":"msg_0a60b3f44001In1auH1jhK3NUK"}}
{"type":"step_finish","timestamp":1789492152746,"sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","part":{"id":"prt_0a60b49a5001K82sHdvEGSdg2P","reason":"tool-calls","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","messageID":"msg_0a60b3f44001In1auH1jhK3NUK","sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","type":"step-finish","tokens":{"total":8945,"input":8854,"output":19,"reasoning":72,"cache":{"write":0,"read":0}},"cost":0.00036781}}
{"type":"step_start","timestamp":1789492153806,"sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","part":{"id":"prt_0a60b4dc9001ThL2eabf1zGCqJ","messageID":"msg_0a60b4a01001yeucPr0pMNKr47","sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","type":"step-start"}}
{"type":"text","timestamp":1789492154027,"sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","part":{"id":"prt_0a60b4dcb001bMdCOhndgF7SGV","messageID":"msg_0a60b4a01001yeucPr0pMNKr47","sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","type":"text","text":"\n\nhello tool world","time":{"start":1789492153803,"end":1789492154024}}}
{"type":"step_finish","timestamp":1789492154120,"sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","part":{"id":"prt_0a60b4f040017veuG2tT4uqPRy","reason":"stop","snapshot":"423d329d4732dd85190b1cf72d4a1c1a23d99c24","messageID":"msg_0a60b4a01001yeucPr0pMNKr47","sessionID":"ses_f59f4c2d5ffeLWm4Iqk9TBRR6k","type":"step-finish","tokens":{"total":9189,"input":9155,"output":11,"reasoning":23,"cache":{"write":0,"read":0}},"cost":0.0003713}}
exit=0
```

Observations — the event vocabulary is richer than §2's one-word run:

- **`step_start` / `step_finish` repeat per agent step.** A tool-using run
  emits multiple step cycles: `step_start → tool_use → step_finish(tool-calls)
  → step_start → text → step_finish(stop)`.
- **`step_finish.reason` has two observed values:** `tool-calls` (intermediate —
  the step ended because the agent wants to call a tool) and `stop` (terminal).
  `stop` is the **only** terminal success signal; `tool-calls` is an
  intermediate that must be followed by another `step_start`.
- **`tool_use`** (`type == "tool_use"`, `part.type == "tool"`) is a neutral
  tool event carrying `part.tool` (name), `part.callID`, and `part.state`
  (`status`/`input`/`output`/`metadata`/`title`/`time`). It contributes nothing
  to the result text; it is ignored for result assembly. Note `tool_use` also
  carries `sessionID` and `messageID` at the top level.
- **`text`** events carry `part.text`; the answer is the ordered concatenation
  of `text` events across steps.
- **`error`** (§3) is the terminal failure event.

Frozen event vocabulary (only these may be recognized): `step_start`, `text`,
`tool_use`, `step_finish`, `error`. Frozen `step_finish.reason` set:
`{stop, tool-calls}`. Any other event `type`, `part.type`, or `reason` is a
failure (unknown-event policy), not silently ignored. Widening either set
requires a new committed capture on the widened version.
