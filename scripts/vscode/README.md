# scripts/vscode — introspection spikes on VS Code agent-session stores

**Status: experimental spikes** (2026-07-16, user-directed research).
Multi-angle overview of what the agents in this workspace have been
doing: where session data lives, what it costs, what was worked on,
and how parallel the work actually is.

## The stores (discovered by exploration, 2026-07-16)

| Store | Path (under `~/Library/Application Support/Code/User/`) | Contains |
|---|---|---|
| Chat sessions | `workspaceStorage/<hash>/chatSessions/*.jsonl` | Full request log: timestamps, modelId, promptTokens/outputTokens, tool calls, titles. **The ledger.** (1.3 GB for this workspace alone) |
| Debug logs | `workspaceStorage/<hash>/GitHub.copilot-chat/debug-logs/<session>/` | `main.jsonl` = start/end markers only; `models.json` = **the price sheet** (per-1M token prices incl. cache tiers) |
| Chronicle | `globalStorage/github.copilot-chat/session-store.db` | SQLite: session summaries, agent names, files touched, refs. **The narrative.** No cost columns |
| Editing sessions | `workspaceStorage/<hash>/chatEditingSessions/` | Edit checkpoints/snapshots |

## The spikes

| Script | Angle | Question it answers |
|---|---|---|
| `stores.py` | Habitat | Where does session data live, how big, which workspaces, what's active now? |
| `ledger.py --by-model` | Metabolism | Requests/tokens per period (today / this month / previous month / all-time) and per model, all workspaces; **estimated credits** from the per-model price sheets (1 cr = $0.01, calibrated 2026-07-16). No balance history is persisted locally (verified) — the UI's credit figure is fetched live, so absolute credits need one calibration anchor; relative attribution is solid |
| `portrait.py` | Memory | What was worked on: chronicle summaries + session titles + most-touched files + measured session parallelism per day |
| `now.py` | Situation board | Live sessions (titles, models, recency) × git state per implicated repo (branch, STAGED files, recent commits with FR/NC refs) × FRs in motion × interleave-hazard flags. The session-start briefing, reception rung 2 |

## First-run findings (2026-07-16)

- **Habitat**: 2.23 GB across 15 workspaces; yamlgraph is 1.7 GB / 281
  sessions / 8 active-in-24h — 64% of everything this machine's agents
  have ever done. The largest single session: "Plot Modeller", 50.4 MB.
- **Metabolism**: 6,461 requests all-time; **billed** prompt volume ≈
  7.3B tokens (each tool-call round re-bills the full context —
  anchor-2 proved `promptTokens` records only the last round). Two
  calibration anchors 2026-07-16: 2702.9 cr = $27.09 (1 cr = $0.01)
  and an 820.5 cr turn whose pure-cache pricing hit 814 → agent turns
  run ≈98% cached. Best-case estimates: this month ≈ $2.4K, all-time
  ≈ $6.2K. Cache reads at $1/M are the entire economics.
- **Memory**: the chronicle DB indexes debug-logs (2-line markers), so
  its narrative tables are empty even after reindex — the real
  narrative lives in chatSessions titles. `emission ≠ reception` has a
  sibling: *indexed ≠ informative* — an index over a vacuous source is
  itself vacuous.
- **Parallelism, measured**: peak 6 same-hour sessions on 2026-07-14 —
  the precise day Scripture logged "four interleave incidents in one
  day" (one_session_one_repo, third strike). The hazard curve and the
  incident record now corroborate each other from independent sources.

## Known limits (spike honesty)

- `promptTokens` conflates cache reads with fresh input — billed ~10×
  apart; cost figures are bounds, not invoices. Calibrate against one
  known anchor from the billing UI if precision matters.
- chatSessions parsing is regex-over-JSONL, not schema parsing: the
  files are large single-line JSON events; a schema parser is the
  escalation path if a spike graduates.
- The authoritative credit ledger is GitHub's billing side; these
  scripts do *attribution* (which arcs burned what), which the
  dashboard cannot.
- `now.py` counts live sessions per **workspace**, not per repo — a
  session in the yamlgraph workspace working purely inside
  `projects/ninchat_voice` still counts against every nested repo.
  Refining to repo-level requires scanning session content for paths;
  escalation path if the overcount produces false hazard flags twice
  (`two_strike_split`).

## OTel tap experiment (2026-07-16, in progress)

The UI's per-operation credit figure arrives on the wire: every
`response.completed` carries `copilot_quota_snapshots` (found in the
extension bundle), and telemetry.json declares the cache-split fields
(`promptcachetokencount`, `promptcachecreation5m/1htokencount`) that
would turn ledger.py's estimate into an invoice. The extension honors
a `COPILOT_OTEL_*` env family; `debug-logs/*/main.jsonl` is that
exporter at default verbosity.

- `otel-tap-on.sh [out.jsonl]` — launchctl env: file exporter + HTTP
  instrumentation + debug level (CAPTURE_CONTENT deliberately off).
  Requires full VS Code restart (Cmd+Q).
- `otel-tap-off.sh` — unset everything.
- Verification: one chat turn, then read the span file for HTTP spans
  with quota/cache fields. Success → exact-mode ledger; failure →
  escalate log level / CAPTURE_CONTENT (two-strike), else the tap
  idea dies honestly.

### Verdict (2026-07-16): PARTIAL SUCCESS — volume exact, cost split absent

Verified with a live 4-turn conversation after restart. The tap writes
OTel LogRecords (KeyValue-list attributes) with three event families:

- `gen_ai.client.inference.operation.details` — **every** inference
  call, with exact `gen_ai.usage.input_tokens`/`output_tokens`, model,
  finish reasons. Anchor-2 confirmed at source: each agent turn billed
  ~740K input, growing ~1–3K/turn. Side-model utility calls
  (gpt-4o-mini titling, 253–2,613 tok) surface here — invisible in
  chatSessions.
- `copilot_chat.agent.turn` — per-turn rollup with `turn.index`.
- `copilot_chat.tool.call` / `session.start` — tool names, session id.

NOT captured at debug level: `copilot_quota_snapshots` (consumed
internally by ChatQuotaService) and the `promptcache*` split. Strike 1
recorded; escalation `COPILOT_OTEL_LOG_LEVEL=trace` available, then
CAPTURE_CONTENT (privacy — user decision).

Consequence: `tap.py` reads the file and reports exact per-model
volume; cost = exact volume × two-anchor calibration (98% cache) with
the all-fresh ceiling printed alongside. This supersedes ledger.py's
rounds×last-round approximation for post-tap data.

### FR-739 (enforced 2026-07-16): attribution, altimeter, delivery

- **AC-00** `tap.py` attributes events via `session.start.traceId →
  session.id` (agent.turn events carry no session.id; the merged
  stream manufactures phantom compactions — 11 where truth was 1).
- **AC-01** `tap.py --altimeter`: per-session context level, slope,
  witnessed peaks. Compactions (>50% drop) are recorded to
  `compactions.jsonl` (the calibration set); turns-to-ceiling ETA
  unlocks at ≥3 witnesses — the ceiling is never hardcoded.
- **AC-02/03** `now.py --tap`: ground-truth liveness + altimeter in
  the session-start briefing (rung-2 delivery). Witnessed 2026-07-16:
  the authoring agent received its own post-compaction level (158K)
  in a tool result. PreToolUse injection is the recorded escalation
  if rung-2 receipt fails twice.
- **AC-04** `ledger.py --tap`: seam-stamped per-session reconciliation
  (estimate vs exact, overlap only). First run: neighbor session
  ratio 1.01 (rounds× validated); own in-flight session 0.27
  (chatSessions lags the active turn — expected, documented).
- **AC-05** rotation enforced on read past 100 MB (archive + truncate;
  truncation keeps the exporter's append fd valid).

**Disarm criterion:** run `otel-tap-off.sh` (and delete the tmp file)
when either (a) quota/cache fields become available via a supported
API, making the tap redundant, or (b) the calibration set has ≥3
witnesses and no open cost/awareness question needs per-call data.
Until then the tap is a **meter** with a rotation rule, not an
unbounded experiment.
