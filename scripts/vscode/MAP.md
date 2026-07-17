# MAP — Copilot introspection territory (for subsequent development)

**As of 2026-07-16.** The metacognitive investigation's chart: what is
explored, what is probed, what is dark; the seams, the join keys, the
instruments and their calibration state; ranked directions. Update
this file when territory changes state (dark → probed → instrumented).

## Territory by state

### Instrumented (tool exists, tested, calibrated)

| Territory | Instrument | State |
|---|---|---|
| Request log / cost estimate (chatSessions) | `ledger.py` | Calibrated 2 anchors; validated ratio 1.01–1.02 on 3 complete sessions |
| Exact per-call usage, live sessions (OTel tap) | `tap.py` | Volume exact; cost = ×98%-cache blend; titles joined; 21 tests |
| Compaction (the guillotine) | `tap.py --altimeter` + `compactions.jsonl` | 2 valid witnesses, ceiling 746,876–750,382 (±0.5%); ETA locked until witness 3; zero-post phantoms excluded |
| Live sessions × git × plan (situation board) | `now.py [--tap]` | Rung-2 delivery witnessed; plan-state pointer |
| Plan state (FR pipeline) | `fr_board.py` + gates.yaml | Own-repo committed board + drift lint; cross-repo = ephemeral view (F7) |
| Habitat / concurrency | `stores.py`, `portrait.py` | Spike-grade; concurrency corroborated the interleave incident record |

### Probed (schema known, no instrument)

| Territory | What's known | Value hypothesis |
|---|---|---|
| `state.vscdb` → `chat.ChatSessionStore.index` | Session index incl. **`copilotcli:/` sessions** + timing (created/lastRequestStarted/Ended) | CLI sessions join the cost model; per-session wall-clock timing without the tap |
| `state.vscdb` → `memento/chat-todo-list` | **Instrumented: `todos.py`** — 191 slots, 21 non-empty, 18 orphaned open intentions; verdicts CLEAN CLOSE / DIED OPEN / LIVE OPEN with title join | Forensics live: the Vertex migration case (work moved sessions, record never reconciled); NC-365 shipped while its orphan reads not-started; 3× dead sessions orphaning "diary reflection" — Distill is the most-abandoned step, measured |
| `state.vscdb` → `chat.terminalSessions`, `chat.customModes` | Terminal-session map; custom mode definitions | Low |
| Chronicle `session-store.db` | Full schema: sessions/turns/session_files/session_refs/checkpoints + FTS | Narrative empty (indexes vacuous debug-logs) — *indexed ≠ informative*; reindex-from-chatSessions is the fix if narrative wanted |
| Transcripts (`transcripts/*.jsonl`) | Verbatim assistant messages, 35 MB | Sentinel retro-scan seed (doctrine-phrase rate over time); summarizer-loss study input |
| Session memory (`memory-tool/memories/<b64(uuid)>/`) | Dir name = base64(session UUID), verified | Join memory ↔ cost ↔ transcript: "what did this session learn and what did it cost" |
| Built-in agents (`ask/plan/explore-agent/`) | Contain `*.agent.md` definitions | Read once for prompt-contract insight |
| `workspace-chunks.db` (Files/FileChunks) | semantic_search chunk index | Low; curiosity only |
| `History/` (4,857 entries) | VS Code local file history | Recovery resource, not analytics |

### Dark (known to exist, never opened)

- `toolEmbeddingsCache.bin`, `commandEmbeddings.json` (binary/opaque)
- `codebase-external.sqlite`, `local-index.1.db`
- `chatEditingSessions/` internals (checkpoint format)
- `copilot_quota_snapshots` on the wire — **the only true actual-cost
  source**; not exported at `LOG_LEVEL=debug` (strike 1 recorded)

## Join keys (the relational spine)

- **Session UUID** → chatSessions stem, transcripts, chat-session-resources,
  debug-logs, chatEditingSessions, session memory (base64), tap `session.id`,
  todo-list keys, ChatSessionStore.index entries. *Universal.*
- **Workspace hash** ↔ folder path via `workspace.json`.
- **traceId** → joins tap events within a session (AC-00).
- Full tree: see README "Data model" section.

## Seams (where instruments attach)

1. **`COPILOT_OTEL_*` env** — two consumers already: this tap (editor
   sessions) + FR-362 process mining (CLI, per-node via
   `YAMLGRAPH_OTEL_DIR`). Escalation ladder: debug (current) → trace
   (strike 2, unspent) → CAPTURE_CONTENT (privacy, human decision).
2. **SQLite read-only** (`file:...?mode=ro`) — state.vscdb, chronicle,
   chunks. Never write; these are VS Code's live stores.
3. **JSONL regex-over-lines** — chatSessions/transcripts/tap. Schema
   parser is the recorded escalation if a spike graduates further.
4. **Events → agent push (PROVEN 2026-07-16):** a watcher started
   with `mode=async` notifies the agent automatically on exit/output —
   witnessed live: a 20s altimeter watcher delivered the authoring
   session's own context level (468,568) into its next turn. True
   push, rung 2, zero infrastructure. Sibling seams: PreToolUse
   sentinel files (rung 1, per-session-id targeting — the FR-438
   arm-then-deliver pattern generalizes from reasoning flags to event
   envelopes) and SessionStart (FR-743: probe + fail-open briefing
   SHIPPED 2026-07-17; bundle grep found SessionStart 76 refs plus two
   undocumented events — UserPromptSubmit 43, **SessionEnd 28 = the
   diary-debt moment**, both registered in the probe; firing verdict
   pends the first fresh session). No seam pushes between tool calls;
   delivery is at tool-call boundaries or session start.

## Calibration facts (do not re-derive)

- 1 credit = $0.01; prices in models.json are credits/1M.
- Agent turns ≈98% cached (anchor-2: 820.5 cr vs 814 pure-cache).
- `promptTokens` = LAST round only; billed ≈ rounds × recorded.
- Compaction ceiling ~750K (2 witnesses, 0.5% apart); post-compaction
  floor 56–61K; growth ~1–3K/turn.
- A zero-token turn is NOT a compaction (phantom-witness incident).
- Estimate-vs-exact ratio <1 on LIVE sessions = self-measurement lag.

## Ranked development directions

1. **Flush advisory at ~650K** (86% of witnessed floor) in now.py —
   the one signal protecting agent memory; calibration exists, seed
   named in two diaries. Cheap; FR-739 territory (amendment).
2. **Third UI anchor** — one manual reading of the UI credit figure vs
   tap total for the same window. If within ~2%, calibration is
   invoice-grade and strike 2 dies unneeded. Cheapest possible step.
3. **CLI sessions into the ledger** — `copilotcli:/` entries in
   ChatSessionStore.index are costed nowhere today; chaplain/watcher
   runs are invisible spend. Probe first: do CLI sessions write
   chatSessions files?
4. **Session memory × cost join** — decode b64 dirs, one table:
   session, title, cost, memory notes written. The "what did learning
   cost" view; also the compaction-flush audit trail.
5. **Trace-level tap (strike 2)** — only if anchor 3 disagrees >2%.
6. **Sentinel retro-scan of transcripts** — doctrine-phrase rate
   before/after sentinel arming (deterrence vs denial curve).
7. **Summarizer-loss study** — pre-compaction transcript vs summary;
   needs its own investigation FR (`investigation_before_fix`);
   raw material already accumulating in tap + calibration records.
8. **Chronicle re-target** — point its indexer at chatSessions instead
   of vacuous debug-logs, only if FTS-over-narrative is ever wanted.

## Meta (what the investigation learned about investigating)

- Every store answered fastest to `read_raw_output_first` — one raw
  record read beat every schema guess (attributes dict-not-list,
  base64 dirs, phantom witness).
- The reception hierarchy governs tooling too: every instrument needed
  an explicit reader/rung/moment before it changed behavior
  (`a_view_without_a_reader_is_a_write_only_database`).
- Lanes: observe freely (spike/chore), integrate under judgement (FR),
  fix as amendment. This map is an observation artifact; instruments
  it proposes graduate to FRs at their integration moment.
