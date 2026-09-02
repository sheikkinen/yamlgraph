# FR-959 Evidence — Live witness: `backend: claude` two-node resume (AC-14, AC-15)

**Date:** 2026-09-02, 17:59Z
**Host:** Windows 11 Home 10.0.26200; Git Bash inside the Claude desktop app's process tree (the enforcing session)
**Binary:** `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\2.1.255\claude.exe`, prepended to `PATH` as `/c/Users/<user>/AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/Claude/claude-code/2.1.255` (the `C:/…` spelling splits on its colon in an MSYS `PATH`; first attempt failed with "claude binary not found" for that reason)
**CLI version:** `2.1.255 (Claude Code)` (checked by the preflight itself, logged below)
**Auth as reported by the FR-959 preflight:** `claude.ai` (browser login, Claude Team subscription — evidence `FR-959-claude-auth-probe.md` §2.3)
**Harness:** `tests/integration/test_fr959_claude_backend_live.py` — a disposable two-node graph written to pytest's `tmp_path`; `examples/demos/session-continuation/**` untouched (`git status` clean for that path before and after; judgement R-6/C-7)
**Code under test:** branch `feat/fr-959-claude-backend`, GREEN commit `838ca888` plus the capture-(a) pin (this commit)
**Temp graph sha256:** `ca2f664531c4f2c919269217f8eddeb347baff8686a12e383d2ea8efc5d1b743` (identical in both runs — same fixture bytes)

## Command

```bash
CLDIR="/c/Users/<user>/AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/Claude/claude-code/2.1.255"
PATH="$CLDIR:$PATH" YAMLGRAPH_LIVE_CLAUDE=1 PYTHONUTF8=1 \
  .venv/Scripts/python.exe -m pytest tests/integration/test_fr959_claude_backend_live.py -q --no-cov -s --tb=short
```

Run 2 (AC-15) is the same command with `ANTHROPIC_API_KEY=sk-invalid-on-purpose` exported in front.

## Run 1 — AC-14, clean shell (log `tmp/fr959-live-ac14.log`, local)

```
started=2026-09-02T17:59:35.430780+00:00 ended=2026-09-02T17:59:44.320001+00:00
[first]  Claude Code 2.1.255 authenticated via claude.ai; executing with timeout=120s
[second] Claude Code 2.1.255 authenticated via claude.ai; executing with timeout=120s
env ANTHROPIC_API_KEY present in parent=True          # see note 1
argv[1]=['claude', '--version']
argv[2]=['claude', 'auth', 'status']
argv[3]=['claude', '-p', 'User: Reply with the single word pong and nothing else.', '--output-format', 'json', '--tools', '']
argv[4]=['claude', '--version']
argv[5]=['claude', 'auth', 'status']
argv[6]=['claude', '-p', 'User: Reply with the single word you replied with before, nothing else.', '--output-format', 'json', '--resume', 'bd19ca7c-42d3-4ac5-ac09-d7f0adb83a4f', '--tools', '']
first.session_id=bd19ca7c-42d3-4ac5-ac09-d7f0adb83a4f first.output='pong'
second.session_id=bd19ca7c-42d3-4ac5-ac09-d7f0adb83a4f second.output='pong'
1 passed in 8.96s
```

(`argv[0]` is yamlgraph's own `git describe` for the run log; not a Claude call.)

## Run 2 — AC-15, `ANTHROPIC_API_KEY=sk-invalid-on-purpose` exported (log `tmp/fr959-live-ac15.log`, local)

```
started=2026-09-02T17:59:47.144113+00:00 ended=2026-09-02T17:59:55.964696+00:00
[first]  Claude Code 2.1.255 authenticated via claude.ai; executing with timeout=120s
[second] Claude Code 2.1.255 authenticated via claude.ai; executing with timeout=120s
env ANTHROPIC_API_KEY present in parent=True
argv[3]=['claude', '-p', 'User: Reply with the single word pong and nothing else.', '--output-format', 'json', '--tools', '']
argv[6]=['claude', '-p', 'User: Reply with the single word you replied with before, nothing else.', '--output-format', 'json', '--resume', 'ad2fee9f-a15d-4f78-b28a-81dcc2ff1c6c', '--tools', '']
first.session_id=ad2fee9f-a15d-4f78-b28a-81dcc2ff1c6c first.output='pong'
second.session_id=ad2fee9f-a15d-4f78-b28a-81dcc2ff1c6c second.output='pong'
1 passed in 8.89s
```

## What the runs prove

| Criterion | Evidence |
|---|---|
| AC-14: real `session_id` resumed byte-for-byte | run 1 `argv[6]` carries `--resume bd19ca7c-…` = `first.session_id`; run 2 likewise with `ad2fee9f-…`. Two different sessions across runs (no reuse, no fixture value). |
| AC-14: `tools: []` → `--tools ""` on the live binary | both agent argvs; the CLI accepted it and answered. |
| AC-06 live: version + auth before **every** `-p` | `argv[1..2]` and `argv[4..5]` — two probes per node, two nodes, two runs. |
| AC-15 (API-key half): an invalid key in the parent never reaches the child | run 2 succeeded with `sk-invalid-on-purpose` exported; the preflight reported `claude.ai`, not `api_key`. An invalid key that had reached the child would have been used (evidence §2.2: key precedence) and rejected. |
| AC-07 live corollary | note 1: the parent held a real `ANTHROPIC_API_KEY` in **both** runs, so run 1 is also a strip witness. |
| C-7: committed demo untouched | harness writes only under `tmp_path`. |

**Note 1.** `env ANTHROPIC_API_KEY present in parent=True` in run 1 despite a
clean shell: `yamlgraph.config` loads the repository `.env` at import (the
FR-798 dotenv boundary), which provisions the repo's Anthropic key into
`os.environ`. So on this host every graph run has an API key in the parent
process, and the child still authenticated as `claude.ai`. This is the
strongest form of the strip witness the FR asked for.

## Limitations

- **AC-15 logged-out half not performed live.** The enforcer may not run
  `claude auth logout` on the operator's account. The refusal path is
  witnessed by (a) the raw logged-out `auth status` capture (`FR-959-claude-auth-probe.md`
  §2.1, exit 1, `authMethod: none`) and the logged-out print-mode envelope
  (§5), and (b) the unit fixtures built from those captures
  (`tests/unit/test_fr959_claude_backend.py::TestPreflight::test_auth_refusals_fail_before_agent_prompt`).
  To close it live, the operator runs, from PowerShell, `claude auth logout`,
  the harness command above (expected: `RuntimeError … authMethod='none'`
  before any `-p`, `1 failed`), then `claude auth login`. **Owed** (PR #563
  review P2: the acceptance criterion is explicitly live; the raw capture and
  the unit fixture do not discharge it). The enforcing session can run the
  harness and commit the redacted result the moment the operator reports
  being logged out.
- The `.env`-provisioned key means "no `ANTHROPIC_API_KEY` in the parent"
  (AC-14's literal wording) was not achievable on this host; the stronger
  condition (key present, still stripped) holds instead.
- Output heads are the full one-word replies; nothing was truncated. Session
  transcripts live under `~/.claude/projects/` on the host and were not
  committed.
- Cost: four one-word turns on the operator's Claude Team subscription;
  `total_cost_usd` logged at DEBUG as notional, not captured here.
