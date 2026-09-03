# FR-959 Evidence — Claude Code CLI raw probes (auth status, settings precedence, tool grammar, print envelope)

**Date:** 2026-09-02
**Host:** Windows 11 Home 10.0.26200, Git Bash (MSYS) shell
**Binary:** `C:/Users/<user>/AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/Claude/claude-code/2.1.255/claude.exe`
(bundled by the Claude desktop app, an MSIX package; **not on PATH** —
`where.exe claude` is empty. Processes launched *by* the app see the same file
under the virtualized path `%APPDATA%/Claude/claude-code/2.1.255/claude.exe`,
which does not exist for an ordinary shell — the probes below were run from
inside the app's process tree, so their `projectsDirectory` and any path they
print use the virtualized form.)
**Version:** `2.1.255 (Claude Code)` — exact stdout bytes `32 2e 31 2e 32 35 35 20 28 43 6c 61 75 64 65 20 43 6f 64 65 29 0a`
**Purpose:** FR-959 judgement R-1 / revised AC-01. Every observation below is a
verbatim capture; the only edits are the redactions marked `<user>` and the
fake credential strings, which were fake at capture time. Nothing here was
typed from a documentation summary (FR-958 R-2/R-6 lesson).

## 0. Capture status

| Capture | Status | Where |
|---|---|---|
| (a) subscription browser login (`claude auth login`) | captured 2026-09-02 (later the same day) — the operator signed in from their own PowerShell using the §6 command and pasted the output | §2.3 |
| (b) inherited `ANTHROPIC_API_KEY` | captured | §2.2 |
| (c) logged out | captured | §2.1 |
| (d) settings-file `env` block | captured | §3 |
| (e) cloud-provider switches (Bedrock / Vertex / Foundry) | captured | §2.4 |
| (f) `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `CLAUDE_CODE_OAUTH_TOKEN` | captured | §2.5–2.7 |
| (g) tool-availability grammar (`--tools`) | captured from `--help` and accepted by the parser | §4 |
| (h) print-mode JSON envelope, logged out | captured | §5 |
| (i) `--max-turns` | accepted by the parser; **absent from `--help` on this version** | §4.3 |

Consequence for the preflight (FR-959 §3): the accepted `authMethod` set is
exactly the values pinned in this file — `claude.ai` (§2.3) and `oauth_token`
(§2.7) — with `apiProvider == "firstParty"` and `loggedIn == true`. Nothing is
guessed; a new method value needs a new capture here before it is accepted.

## 1. Version

```
$ claude --version
2.1.255 (Claude Code)
```

`claude auth status --help`:

```
Usage: claude auth status [options]

Show authentication status

Options:
  -h, --help  Display help for command
  --json      Output as JSON (default)
  --text      Output as human-readable text
```

`claude auth --help` lists `login [options]`, `logout`, `status [options]`.

## 2. `claude auth status` (JSON is the default output)

### 2.1 (c) Logged out, no credential variables in the environment

```
$ env | grep -c '^ANTHROPIC_API_KEY='
0
$ claude auth status
{
  "loggedIn": false,
  "authMethod": "none",
  "apiProvider": "firstParty",
  "analyticsDisabled": false,
  "projectsDirectory": "C:\\Users\\<user>\\.claude\\projects"
}
rc=1
$ claude auth status --text
Anthropic base URL: https://api.anthropic.com
Not logged in. Run claude auth login to authenticate.
rc=1
```

### 2.2 (b) Inherited `ANTHROPIC_API_KEY` (fake value)

```
$ ANTHROPIC_API_KEY=sk-ant-test-not-a-real-key claude auth status
{
  "loggedIn": true,
  "authMethod": "api_key",
  "apiProvider": "firstParty",
  "analyticsDisabled": false,
  "projectsDirectory": "C:\\Users\\<user>\\.claude\\projects",
  "apiKeySource": "ANTHROPIC_API_KEY"
}
rc=0
$ ANTHROPIC_API_KEY=sk-ant-test-not-a-real-key claude auth status --text
API key: ANTHROPIC_API_KEY
Anthropic base URL: https://api.anthropic.com
rc=0
```

Observation: `loggedIn: true` is reported for a syntactically fake key. Auth
status reports the **method**, not the credential's validity; validity is only
tested by a request (§5 shows the failure envelope shape).

### 2.3 (a) Subscription browser login — captured by the operator

Run by the operator from their own PowerShell after `claude auth login`
(browser flow, Claude Team subscription), pasted verbatim; `email` and `orgId`
redacted, home path redacted:

```
> & "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\2.1.255\claude.exe" auth status
{
  "loggedIn": true,
  "authMethod": "claude.ai",
  "apiProvider": "firstParty",
  "analyticsDisabled": false,
  "projectsDirectory": "C:\\Users\\<user>\\.claude\\projects",
  "email": "<redacted>",
  "orgId": "<redacted>",
  "orgName": "<org>",
  "subscriptionType": "team"
}
rc=0
```

Observations:

1. The browser login reports `authMethod: "claude.ai"`. This is the value the
   preflight accepts (with `oauth_token`, §2.7).
2. The logged-in shape carries four extra keys (`email`, `orgId`, `orgName`,
   `subscriptionType`) absent from every other capture. The preflight model
   ignores extra keys, so the parser needs no change; the keys are recorded
   here because they are personal data and the runtime must never log the
   raw status JSON (FR-959 constraint: never log the child env or auth
   output beyond `authMethod`/`apiProvider`).
3. The same status is visible from inside the Claude desktop app's process
   tree once the operator has logged in (§5.1 below) — the credential store
   is per user, not per process view.

### 2.4 (e) Cloud-provider switches

```
$ CLAUDE_CODE_USE_BEDROCK=1 claude auth status
{
  "loggedIn": true,
  "authMethod": "third_party",
  "apiProvider": "bedrock",
  "analyticsDisabled": true,
  "projectsDirectory": "C:\\Users\\<user>\\.claude\\projects"
}
rc=0
$ CLAUDE_CODE_USE_VERTEX=1 claude auth status
{ ... "authMethod": "third_party", "apiProvider": "vertex", ... }
rc=0
$ CLAUDE_CODE_USE_FOUNDRY=1 claude auth status
{ ... "authMethod": "third_party", "apiProvider": "foundry", ... }
rc=0
```

(Vertex and Foundry outputs are byte-identical to the Bedrock one except for
the `apiProvider` value.)

### 2.5 `ANTHROPIC_AUTH_TOKEN` (fake bearer)

```
$ ANTHROPIC_AUTH_TOKEN=fake-bearer-token claude auth status
{
  "loggedIn": false,
  "authMethod": "none",
  "apiProvider": "firstParty",
  "analyticsDisabled": false,
  "projectsDirectory": "C:\\Users\\<user>\\.claude\\projects"
}
rc=1
```

Observation: a bearer token is **not** reflected by auth status. It is still a
documented credential surface, so FR-959 strips it regardless; auth status
cannot witness its absence.

### 2.6 `ANTHROPIC_BASE_URL` (routing)

```
$ ANTHROPIC_BASE_URL=http://127.0.0.1:9 claude auth status --text
Anthropic base URL: http://127.0.0.1:9
Not logged in. Run claude auth login to authenticate.
rc=1
```

Observation: the base URL is a routing surface the CLI itself reports in text
mode only; it is not a field of the JSON output. A proxy at that URL is a
payer change invisible to the JSON preflight, so FR-959 strips the variable.

### 2.7 `CLAUDE_CODE_OAUTH_TOKEN` (fake long-lived token)

```
$ CLAUDE_CODE_OAUTH_TOKEN=fake-oauth claude auth status
{
  "loggedIn": true,
  "authMethod": "oauth_token",
  "apiProvider": "firstParty",
  "analyticsDisabled": false,
  "projectsDirectory": "C:\\Users\\<user>\\.claude\\projects"
}
rc=0
```

`claude --help` describes `setup-token` as "Set up a long-lived authentication
token (requires Claude subscription)". `oauth_token` is therefore a
subscription-payer method by the vendor's own wording; the fake value again
shows auth status reports method, not validity.

## 3. (d) Settings-file `env` block precedence

```
$ claude --settings '{"env":{"ANTHROPIC_API_KEY":"sk-ant-from-settings-file"}}' auth status
{
  "loggedIn": true,
  "authMethod": "api_key",
  "apiProvider": "firstParty",
  "analyticsDisabled": false,
  "projectsDirectory": "C:\\Users\\<user>\\.claude\\projects",
  "apiKeySource": "ANTHROPIC_API_KEY"
}
rc=0
$ ANTHROPIC_API_KEY=sk-ant-shell claude --settings '{"env":{"ANTHROPIC_API_KEY":"sk-ant-from-settings-file"}}' auth status
{ ... identical to the previous output ... }
rc=0
```

Observations:

1. A settings `env` block **alone** (no shell variable) is enough to put the
   CLI in `api_key` mode. This is the FR-958 R-3 finding reproduced on the
   pinned version: stripping the parent environment does not remove a
   settings-injected key.
2. `apiKeySource` reads `ANTHROPIC_API_KEY` whether the key came from the shell
   or from the settings block; auth status cannot tell the two apart and does
   not print which value wins. The settings reference's statement that
   settings values override shell values remains a documentation claim, not a
   local observation.
3. Consequence: the preflight *detects* the api_key state after settings are
   applied (§2.2 shape) and refuses; it cannot *prevent* a settings block from
   re-injecting a key between the preflight and the `-p` call. That window is
   the residual in FR-959 §3 that the spend owner signs.

## 4. (g) Tool-availability grammar — `claude --help`, verbatim excerpts

```
  --allowedTools, --allowed-tools <tools...>
      Comma or space-separated list of tool names to allow (e.g. "Bash(git *)
      Edit")
  --disallowedTools, --disallowed-tools <tools...>
      Comma or space-separated list of tool names to deny (e.g. "Bash(git *)
      Edit")
  --tools <tools...>                    Specify the list of available tools from
                                        the built-in set. Use "" to disable all
                                        tools, "default" to use all tools, or
                                        specify tool names (e.g.
                                        "Bash,Edit,Read").
  --dangerously-skip-permissions        Bypass all permission checks.
                                        Recommended only for sandboxes with no
                                        internet access.
  --permission-mode <mode>              Permission mode to use for the session
                                        (choices: "acceptEdits", "auto",
                                        "bypassPermissions", "manual",
                                        "dontAsk", "plan")
  --add-dir <directories...>            Additional directories to allow tool
                                        access to
  --model <model>                       Model for the current session. Provide
                                        an alias for the latest model (e.g.
                                        'fable', 'opus', or 'sonnet') or a
                                        model's full name (e.g.
                                        'claude-fable-5').
  -r, --resume [value]                  Resume a conversation by session ID, or
                                        open interactive picker with optional
                                        search term
  -c, --continue                        Continue the most recent conversation in
                                        the current directory
  --output-format <format>              Output format (only works with --print):
                                        "text" (default), "json" (single
                                        result), or "stream-json" (realtime
                                        streaming) (choices: "text", "json",
                                        "stream-json")
  --bare                                Minimal mode: skip hooks, LSP, plugin
                                        sync, attribution, auto-memory,
                                        background prefetches, keychain reads,
                                        and CLAUDE.md auto-discovery. Sets
                                        CLAUDE_CODE_SIMPLE=1. Anthropic auth is
                                        strictly ANTHROPIC_API_KEY or
                                        apiKeyHelper via --settings (OAuth and
                                        keychain are never read). ...
  --restricted                          Restricted mode: removes the built-in
                                        tools that run commands or code ... and
                                        ignores user, project and local settings
                                        files (managed settings and --settings
                                        still apply ...)
  --setting-sources <sources>           Comma-separated list of setting sources
                                        to load (user, project, local).
  --settings <file-or-json>             Path to a settings JSON file or a JSON
                                        string to load additional settings from
  --max-budget-usd <amount>             Maximum dollar amount to spend on API
                                        calls (only works with --print)
```

### 4.1 Frozen availability contract (R-1)

`--tools` takes a **comma-separated list** of built-in tool names; the empty
string `""` disables every tool. This is the one form FR-959 emits; the
`--disallowedTools` fallback in the pre-judgement text is deleted.

### 4.2 Availability vs approval

`--tools` = which tools exist. `--allowedTools` = which existing tools run
without a permission prompt. Two controls, two `cli_flags` keys (FR-958 R-2).

### 4.3 (i) `--max-turns`

Not listed in `--help` on 2.1.255. Parser acceptance probe (§5, P2): the flag
is accepted — the run proceeds to the auth failure instead of a commander
"unknown option" error on stderr. Recorded as *accepted, undocumented in
`--help`*; the exact-version pin (FR-959 §4) is what protects this mapping.

### 4.4 `--bare` on this version

The `--help` text describes `--bare` as opt-in and says nothing about it
becoming the default for `-p`. The judgement's R-3 concern comes from the
online headless documentation; the version pin is the enforced boundary
either way.

## 5. (h) Print-mode JSON envelope, logged out (rc and stdout/stderr split)

All five probes ran from an empty temporary directory, logged out, with a
60 s timeout. Each returned **rc=1**, an **empty stderr**, and one JSON object
on **stdout** (pretty-printed here; the original is one line):

```
$ claude -p "reply with the single word pong" --output-format json
{
  "type": "result",
  "subtype": "success",
  "is_error": true,
  "result": "Not logged in · Please run /login",
  "session_id": "d60ac511-386f-4efd-b760-a4be4bdf1beb",
  "terminal_reason": "api_error",
  "api_error_status": null,
  "num_turns": 1,
  "duration_ms": 174,
  "duration_api_ms": 0,
  "total_cost_usd": 0,
  "stop_reason": "stop_sequence",
  "permission_denials": [],
  "usage": { ... },
  "modelUsage": {},
  "uuid": "39f9b2bf-adde-43ec-b3b7-a5d83fd8053c",
  ...
}
rc=1
stderr: (empty)
```

| Probe | Extra argv | Outcome |
|---|---|---|
| P1 | — | rc=1, envelope above |
| P2 | `--max-turns 1` | rc=1, same envelope shape (flag accepted) |
| P3 | `--tools ""` | rc=1, same envelope shape (flag accepted) |
| P4 | `--tools "Read,Grep" --allowedTools "Read,Grep"` | rc=1, same envelope shape |
| P5 | `--model opus --add-dir <tmpdir>` | rc=1, same envelope shape |

Observations that shape FR-959 §5 (result contract):

1. `subtype` is `"success"` **while** `is_error` is `true`. `subtype` carries
   no failure signal; `is_error` does. The typed envelope keys on `is_error`.
2. A failed run still has a real `session_id`. Session presence does not imply
   success.
3. In-run failures (here: missing auth) are reported on **stdout as JSON** with
   a non-zero exit and empty stderr — matching the headless documentation's
   0-versus-non-zero contract. No numeric subtype was observed beyond `1`.
4. `total_cost_usd` is present and `0` for a failed run; it is logged at DEBUG
   as notional and never surfaced in `CopilotResult`.

### 5.1 Logged-in status seen from inside the app's process tree

After the operator's login, the same binary run from the enforcing session
(a child of the desktop app) reports the same state — the credential store is
per user:

```
$ claude auth status          # bash tool, MSIX LocalCache path
{ ... "loggedIn": true, "authMethod": "claude.ai", "apiProvider": "firstParty", ... "subscriptionType": "team" }
rc=0
$ claude auth status --text
Login method: Claude Team account
Organization: <org>
Email: <redacted>
Anthropic base URL: https://api.anthropic.com
rc=0
```

## 6. Capture (a) — command the operator ran (kept for the next host)

On this host, from an ordinary PowerShell (the MSIX real path, not the
virtualized one):

```powershell
$claude = "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\2.1.255\claude.exe"
& $claude auth login          # interactive browser login on the subscription
& $claude auth status         # paste the JSON below this line, redact nothing but the home path
& $claude auth status --text
```

Done 2026-09-02: output recorded in §2.3; `CLAUDE_SUBSCRIPTION_AUTH_METHODS`
in `yamlgraph/node_factory/copilot_runtime_claude.py` is
`{"claude.ai", "oauth_token"}`.

## 7. Derived strip set (FR-959 §3, R-2)

From the observations above, the child environment for both the preflight and
the `-p` call is `os.environ` minus:

| Variable | Evidence |
|---|---|
| `ANTHROPIC_API_KEY` | §2.2 — `authMethod: api_key` |
| `ANTHROPIC_AUTH_TOKEN` | §2.5 — documented credential, not witnessable by auth status; stripped defensively |
| `ANTHROPIC_BASE_URL` | §2.6 — routing surface printed by `--text`, absent from JSON |
| `CLAUDE_CODE_USE_BEDROCK` | §2.4 — `apiProvider: bedrock` |
| `CLAUDE_CODE_USE_VERTEX` | §2.4 — `apiProvider: vertex` |
| `CLAUDE_CODE_USE_FOUNDRY` | §2.4 — `apiProvider: foundry` |

Kept: `CLAUDE_CODE_OAUTH_TOKEN` (§2.7 — subscription payer by vendor wording),
`PATH`, and the FR-363 OTel variables.

## 8. Limitations

- Capture (a) was produced by the operator, not by the enforcer (§2.3); the
  enforcer never ran `claude auth login`/`logout`.
- Settings precedence between two competing key values is not observable via
  auth status (§3.2); only the documentation claim exists.
- No successful `-p` run exists on this host; the success envelope's `result`
  and `session_id` types are asserted from the failure envelope's shape (both
  present, both strings) and will be re-witnessed by AC-14/AC-15.
- Probes were run under the Claude desktop app's own session environment; the
  variables it injects (`CLAUDECODE`, `CLAUDE_CODE_*` session plumbing) were
  present for every probe and did not alter `authMethod` (§2.1 shows `none`
  under them).
