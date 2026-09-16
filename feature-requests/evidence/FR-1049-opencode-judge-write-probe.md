# FR-1049 opencode judge write-probe — raw capture (pinned version 1.18.31)

**Prior art:** `FR-1048-opencode-cli-probe.md` — the same CLI, pinned to the
same `1.18.31`; its §11 proved `read` auto-completes in headless mode, this
capture proves `write` does too. `FR-960-claude-judge-witness.md` — the judge
variant's file-write contract, on a different CLI (Claude's `--allowedTools`
approval). `FR-959-claude-auth-probe.md` / `FR-959-claude-backend-witness.md` —
the Claude backend's CLI probes. None is a duplicate: no prior record proves
the opencode headless `write` tool completes without a permission flag — the
one fact that decides whether the opencode judge can write its own draft.

Raw capture recorded 2026-09-16 on the authoring host, `/usr/local/bin/opencode`.
Redaction: none required — session ids, token counts, and a temp path only; no
credentials.

## §1 Headless `write` tool call auto-completes (no `--auto`, no permission config)

Working directory: a fresh, disposable temp dir containing nothing. The prompt
asks opencode to create a file; the stream shows the `write` tool completing,
and the file exists afterwards. This is the exact contract the judge needs —
write the draft to `{{ artifact_path }}` (inside the run's working directory)
"using file tools directly".

Command:

```
opencode run --format json --model inception/mercury-2.5 'Create a file named probe.txt containing exactly the single line: hello-judge-write'
```

Complete stdout, unedited:

```json
{"type":"step_start","timestamp":1789526852945,"sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","part":{"id":"prt_0a81cc54c00149y5XeN5BgEnDs","messageID":"msg_0a81cb9f3001C86bdPvNo0ZktY","sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","type":"step-start"}}
{"type":"tool_use","timestamp":1789526853078,"sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","part":{"type":"tool","tool":"write","callID":"call_fbc701b346bb4bd09a9a53f9","state":{"status":"completed","input":{"content":"hello-judge-write\n","filePath":"/private/var/folders/dx/cygn8k4d4xd4fhnmrqs7z3vh0000gn/T/opencode/oc-write-probe/probe.txt"},"output":"Wrote file successfully.","metadata":{"diagnostics":{},"filepath":"/private/var/folders/dx/cygn8k4d4xd4fhnmrqs7z3vh0000gn/T/opencode/oc-write-probe/probe.txt","exists":false,"truncated":false},"title":"private/var/folders/dx/cygn8k4d4xd4fhnmrqs7z3vh0000gn/T/opencode/oc-write-probe/probe.txt","time":{"start":1789526853056,"end":1789526853076}},"id":"prt_0a81cc54e001uRx9XaUVlQRpEb","sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","messageID":"msg_0a81cb9f3001C86bdPvNo0ZktY"}}
{"type":"step_finish","timestamp":1789526853344,"sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","part":{"id":"prt_0a81cc6d3001gEp2jOncy6Rdsc","reason":"tool-calls","messageID":"msg_0a81cb9f3001C86bdPvNo0ZktY","sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","type":"step-finish","tokens":{"total":7558,"input":7445,"output":27,"reasoning":86,"cache":{"write":0,"read":0}},"cost":0.00031475}}
{"type":"step_start","timestamp":1789526853956,"sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","part":{"id":"prt_0a81cc92d001SYlLV3uBrRKZRt","messageID":"msg_0a81cc6dd001DHKSFGeijWay9v","sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","type":"step-start"}}
{"type":"text","timestamp":1789526853956,"sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","part":{"id":"prt_0a81cc931001SMl4Bpe1dOEvS7","messageID":"msg_0a81cc6dd001DHKSFGeijWay9v","sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","type":"text","text":"\n\nFile `probe.txt` created with the content `hello-judge-write`.","time":{"start":1789526853937,"end":1789526853940}}}
{"type":"step_finish","timestamp":1789526853956,"sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","part":{"id":"prt_0a81cc937001mlBTWn0CHmlYOj","reason":"stop","messageID":"msg_0a81cc6dd001DHKSFGeijWay9v","sessionID":"ses_f57e348b4ffedWGlKbNMa3NaRr","type":"step-finish","tokens":{"total":7532,"input":7482,"output":19,"reasoning":31,"cache":{"write":0,"read":0}},"cost":0.00030678}}
```

exit=0, stderr=<empty>.

File written, verified on disk:

```
$ ls -la oc-write-probe
-rw-r--r--  1 sheikki  staff  18 ... probe.txt
$ cat oc-write-probe/probe.txt
hello-judge-write
```

## §2 Observations (the load-bearing facts for FR-1049)

1. **The `write` tool auto-completes in headless mode with no permission
   flag.** No `--auto`, no `opencode.json` permission entry, no interactive
   approval. The `tool_use` event reports `state.status: "completed"` and
   `output: "Wrote file successfully."`, and the file exists with the exact
   content. This is opencode's default: write within the run's working
   directory is auto-approved.
2. **The event shape matches FR-1048's frozen vocabulary exactly:**
   `step_start → tool_use → step_finish(tool-calls) → step_start → text →
   step_finish(stop)`. The FR-1048 state machine parses this stream with
   `tool_use` neutral and `stop` terminal — no backend change is needed.
3. **The judge needs no permission flag mapping.** Copilot CLI needed
   `allow_all_tools` (NC-414); Claude needed `--tools`/`--allowedTools`
   (FR-960). opencode needs neither: FR-1048's `OpenCodeCliFlags` already
   maps only `model` and `resume`, and that is sufficient — the judge node's
   `cli_flags` is just a pinned `model`. This is the whole FR in one fact.
4. **Workspace-scoped, not path-scoped.** The auto-approval was for a write
   inside the run's working directory. The judge's `{{ artifact_path }}`
   (`$WORKDIR/tmp/draft-judgement-…`) is inside the working directory the
   wrapper runs in, so it falls under the same auto-approved surface. A write
   outside the working directory is untested and is not what the judge needs.
5. **Payer is the provider key.** `--model inception/mercury-2.5` is the only
   explicit payer signal; the JSONL carries no server-reported model id
   (FR-1048 §8), so the model is witnessed by the `--model` argv, not by
   reading the stream back.

## §3 Limitations

- One capture, one model, one host, the pinned `1.18.31`. A second capture is
  required to widen the supported-version set, as with FR-1048's probe.
- `write` auto-approval is witnessed for a write inside the run's working
  directory only; writes elsewhere, `bash`, `edit`, and `patch` are untested
  and are explicitly out of the judge's contract (no Bash for the judge —
  the FR-960 rationale).
