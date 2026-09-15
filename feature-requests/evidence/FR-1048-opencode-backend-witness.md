# FR-1048 opencode backend — live witness (AC-16/AC-17)

**Prior art:** `FR-1048-opencode-cli-probe.md` — the probe record this witness
completes (the "did the frozen contract hold live" half). FR-959's witness
chain — `FR-959-claude-backend-witness.md`, `FR-960-claude-judge-witness.md`,
`FR-960-run-Bprime-claude-draft-FR-961.md` — is the Claude backend's analogue
(same "live AC witness" role, a different CLI). `FR-1005-research-route-run-failures.md`
is a "witness" noun match only (research-route failure records). None is a
duplicate: this file records the live opencode run, which no prior record
captures.

Recorded 2026-09-15 from the authoring host, `/usr/local/bin/opencode`
1.18.31, provider `inception/mercury-2.5`. Run via the gated disposable
harness `tests/integration/test_fr1048_opencode_backend_live.py`
(`YAMLGRAPH_LIVE_OPENCODE=1`). No committed graph or prompt was modified or
executed.

## Command

```
YAMLGRAPH_LIVE_OPENCODE=1 .venv/bin/pytest tests/integration/test_fr1048_opencode_backend_live.py -s --no-cov
```

## AC-16: two-node nonce recall

```
=== FR-1048 live witness ===
started=2026-09-15T17:57:01.241029+00:00 ended=2026-09-15T17:57:13.495933+00:00
temp graph sha256=b54966edb64042695672c83725798b9c071c3b9457f0a43b94f6434308a1fb3c
resolved model=inception/mercury-2.5
argv[0]=['opencode', '--version']
argv[1]=['opencode', 'run', 'User: Reply with the single word pong. Also remember this nonce: NONCE-7419.', '--format', 'json', '--model', 'inception/mercury-2.5']
argv[2]=['opencode', '--version']
argv[3]=['opencode', 'run', 'User: Reply with the single nonce I gave you earlier (NONCE-7419).', '--format', 'json', '--model', 'inception/mercury-2.5', '--session', 'ses_f59c8e90fffevQkdOSqlIBP8RA']
first.session_id=ses_f59c8e90fffevQkdOSqlIBP8RA first.output='\n\npong'
second.session_id=ses_f59c8e90fffevQkdOSqlIBP8RA second.output='\n\nNONCE-7419'
```

Observations:

- One `opencode --version` probe immediately before each agent call (argv[0],
  argv[2]), no cache.
- Frozen argv order (prompt first): `opencode run <prompt> --format json
  --model <resolved>` and the trailing `--session <resolved>`.
- Both streams report the **same** non-empty session id
  `ses_f59c8e90fffevQkdOSqlIBP8RA`; the second argv carries it byte-for-byte.
- The second output recalls the first node's nonce (`NONCE-7419`) — real
  session continuation, not argv construction alone.

## AC-17: invalid session refuses

`test_invalid_session_refuses` passes: `_execute_opencode` with
`resume: "ses_nonexistent123"` raises `RuntimeError` whose message contains
`Session not found` (from opencode stderr) **and** the attempted id
(`attempted --session 'ses_nonexistent123'`). No `CopilotResult` is
constructed and no state is updated.

## Limitations

- `test_two_node_resume_recalls_nonce` and `test_invalid_session_refuses` are
  gated and were run live once each on the pinned version; they are not part
  of the default (offline) unit run.
- The witness bills the resolved provider for two tiny turns.
