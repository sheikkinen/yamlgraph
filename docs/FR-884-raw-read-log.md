# FR-884 Raw-Read Log (AC-02 / R-1 gate)

**Read:** 2026-08-25, all 10 sessions end-to-end as reconstructed turn skeletons
(full user text + response head per turn, replayed from the op-log store).
**Window:** 2026-06-26..2026-08-25 Europe/Helsinki. **Corpus:** 74 sessions,
~650M prompt tokens. **Strata:** 5 highest-token + 5 random.
**Privacy:** session pseudonyms only; no UUIDs, no titles, no transcript
excerpts, no customer identifiers. Raw skeletons remain in `tmp/` (gitignored).

| # | Stratum | Date bucket | Turns | Task-shape clue | Surprising detail (non-identifying) | Privacy class |
|---|---|---|---|---|---|---|
| S-H1 | high-token | 2026-07..08 | 472 | Operator command console for a customer voice project: judge/enforce/merge/deploy-watch/e2e-witness/forensics/board ops | Single-word turns ("poll", "merge", "check") each cost 200K–700K prompt tokens because context grows monotonically in a weeks-long session; ~30 merge turns and ~10 poll turns are near-pure context resend. The operator organically extracted two recurring shapes into scripts mid-session (an evidence gatherer and a case-study checker) — sole-route extraction already happens under pressure, unsystematically | CUSTOMER-SENSITIVE (skeleton stays local) |
| S-H2 | high-token | 2026-07 | 171 | Voice-project test-suite orchestration + bulk FR filing/judging + analysis docs | A 42-case LLM persona suite runs ~30+ min sequentially while the premium session polls it with "check status/results" turns; separately the session *manually evaluates the output of the recap graph* — a graph consuming a premium session to verify what a cheap judge could | CUSTOMER-SENSITIVE |
| S-H3 | high-token | 2026-07 | 135 | Framework FR ladder: ~20 alternating judge-N/enforce-N cycles in one session, plus 3 releases and classifier baseline runs | The dominant repeated unit is the judge→enforce pair; deterministic 30-run baseline batches were monitored by repeated "whats the status of baseline" turns at full-context price — watching a progress bar with a frontier model | INTERNAL (public-repo work) |
| S-H4 | high-token | 2026-07 | 146 | Demo spike arc → self-introspection arc that BUILT the very telemetry tooling FR-884 consumes | Contains the origin of `builders_never_call`: the operator states the agent has never delegated work to the framework it builds; FR-884's own lineage sits inside its sample. Also the cost-calibration arc (credits-per-operation) that produced the ledger tooling | INTERNAL |
| S-H5 | high-token | 2026-07..08 | 160 | FORK of S-H1 (identical first ~128 turns) | Forked sessions duplicate the entire shared prefix in the store — naive session-level token accounting double-counts fork prefixes; the high-token stratum contains near-duplicates. 2 of 10 sampled sessions were forks | CUSTOMER-SENSITIVE |
| S-R1 | random | 2026-08 | 21 | Research → plan doc → FR → sole-route judge → enforce for a chat-integration proof of concept | The sole judge route was correctly invoked from the interactive session; enforcement blocked mid-flow on human-only steps (external account registration) — some interactive work is irreducibly human-gated | INTERNAL |
| S-R2 | random | 2026-08 | 1 | Review a planning doc, append findings to the doc | A complete task in ONE turn: closed input (the doc), one judgement, one output shape — the purest graph-shaped session in the sample, running on the most expensive model | INTERNAL |
| S-R3 | random | 2026-07 | 30 | Dedicated judge session: ~29 of 30 turns are "judge NNN"/"rejudge NNN" over a content-pipeline FR ladder | An entire premium session doing nothing but serial judging — a map shape (judge each FR) executed by hand, predating systematic use of the pinned judge graph; includes two rejudge loops after author amendments | INTERNAL |
| S-R4 | random | 2026-08 | 5 | Iterative essay evaluation against a repo source doc (v1→v3 + tagline) | The agent detected that "v2" was byte-identical to v1 — an eval-against-source loop with a mechanizable diff pre-check in front of one judgement per version | INTERNAL |
| S-R5 | random | 2026-07 | 44 | FORK of S-H2 (identical first 43 turns) | Second fork in a 10-session sample — forking after long shared prefixes is a recurring workflow pattern, not an anomaly; any corpus analysis must dedupe by (session, turn-index) prefix | CUSTOMER-SENSITIVE |

## What the raw read establishes (input to the taxonomy)

1. **Micro-turn tax dominates the mega-sessions.** The most expensive shape is
   not complex reasoning but cheap questions asked in expensive places:
   poll/merge/check/status turns late in long sessions, each paying full
   context. Extraction target: a deploy/rollout watcher and a status board
   that answer OUTSIDE the premium session (script or pinned mini-model
   graph), not inside it.
2. **judge/enforce pairs are the atomic unit of the interactive workflow.**
   Judging is already governed (pinned graph); the raw read shows large
   historical interactive judging (S-H3, S-R3) that the sole route has since
   absorbed — validating the extraction model this FR generalizes.
3. **Extraction already happens organically under pressure** (S-H1 scripted
   two recurring evidence shapes mid-incident). FR-884's job is to make that
   systematic and ahead-of-need instead of mid-incident.
4. **Forks require prefix dedupe** before any token accounting (2/10 sampled).
5. **Single-judgement doc tasks** (S-R2, S-R4) are complete graph candidates
   as-is: closed inputs, one output, no session state.
