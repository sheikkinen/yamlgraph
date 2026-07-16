# FR-740: FR Pipeline Board — generated priority view + structural interrupts

**Status:** Completed
**Type:** Feature (process tooling — LLM-free)
**Effort:** 1 day (board + lint) + template/convention edits
**Requested:** 2026-07-16
**Judged:** 2026-07-16 — the completeness gate as specced would force a
700-row board (status census measured); active-set scoping, gates.yaml,
and the missing template section bound below
**Completed:** 2026-07-16 — all rungs; AC-06 read recorded below
**Spawned by:** diaries 2026-07-16 *the-unasked-question* (ninchat_voice) +
*the-human-skims* (yamlgraph) — two named traps, one mechanism
**Prior art:** NC-372 (generate + drift-gate a view — the pattern donor),
NC-393 (two-way freshness lint), `scripts/vscode/now.py` (sessions × repos ×
FRs-in-motion — the live-state sibling; this FR is the *plan-state* board),
plan-fr-queue-2026-07-15.md (the hand-authored board this replaces — its
headers lagged NC-357 by six days, NC-370/NC-392 by days). Disposition:
extends now.py's family, consumes the queue doc's data, replaces only its
hand-merged inventory sections; prose strategy sections stay human.

## Problem — measured, two traps

1. **"What's next?" merges four sources by hand every time:** FR status
   headers (which lag — NC-357 six days, NC-370/392 recurrent), git-log
   motion, the P-gates table, and lane/serialization facts held in memory.
   Every merge goes stale within hours in a 6-session workspace (measured
   concurrency, 2026-07-14).
2. **`unasked_question_is_an_unowned_gate` + `prose_is_free_interrupts_are_expensive`:**
   eight product decisions sat parked for days, each answerable in under a
   minute once asked with options. Asking was ambient work owned by no
   queue slot; the agents' default spends human attention on prose to skim
   while starving decision points.

## Proposed Solution

### 1. `scripts/fr_board.py` — the reduce (stdlib + yaml, no LLM, no keys)

Inputs (all existing ground truth, nothing hand-authored):
- FR status headers (`feature-requests/*.md`, `**Status:**` line) — both
  this repo and, via `--project <path>`, project repos (ninchat_voice)
- `git log` motion: RED/GREEN/fold/judgement commits per FR ref
- The gates table (parsed from the queue doc's `| P# |` rows, or a
  dedicated `gates.yaml` if parsing proves brittle — enforce decides,
  names the choice)
- Lane facts: files-touched per FR (from commit stats) → contention flags

Outputs:
- **Priority table:** ready-to-enforce / in-flight / gated-on-whom, with
  ask-by dates on gated rows
- **Mermaid DAG:** FR dependencies + lane annotations (the NC-372 view
  discipline: labels by reference, generated-file header)
- `--check` mode: regenerate-and-diff drift gate

### 2. Two-way freshness lint (NC-393 pattern, pre-commit)

- board→repo: every board row's FR file exists with the stated status
  prefix (staleness)
- repo→board: every `FR-*/NC-*` file with a `**Status:**` header appears
  on the board (completeness — a board that silently omits an FR reverts
  to tribal knowledge one FR at a time)

### 3. Owned gates with pre-drafted questions (convention, enforced by the board)

A gated board row REQUIRES: owner, ask-by date, and **the unblocking
question pre-drafted as options** (options + evidence + recommended
default). Parking an FR means drafting its question — asking becomes
copy-paste cheap. The lint fails a gated row missing its question block.

### 4. Judge template: interrupts as standard output (one template edit)

`feature-requests/TEMPLATE.md` judgement section gains a terminal heading:
**"Questions for the human (as options, or 'none')"** — the interrupt
becomes a judgement output, not an agent initiative. The absent-vs-none
distinction is deliberate: "none" is a statement, absence is an omission.

## Acceptance Criteria

- [ ] AC-01 RED — unit: fixture FR corpus (statuses, gates, motion) →
      board table + DAG exact; malformed status header recorded as a
      parse failure row, never dropped.
- [ ] AC-02 Two-way lint: scratch board row naming a nonexistent FR fails;
      scratch FR file absent from the board fails; untouched repo passes;
      wired pre-commit.
- [ ] AC-03 Gated-row contract: a gated row without owner/ask-by/question
      block fails the lint (the unowned-gate trap made structurally
      impossible).
- [ ] AC-04 Cross-repo: `--project projects/ninchat_voice` renders the NC
      queue on the same board; the hand-authored inventory sections of
      plan-fr-queue are retired (prose strategy sections remain, pointing
      at the board).
- [ ] AC-05 Template edit landed; the next real judgement uses the
      questions-or-none section (witnessed by citation).
- [ ] AC-06 Real-data read (read_raw_output_first): the first generated
      board is READ against the live queue; discrepancies vs the
      hand-authored table recorded in this FR before the lint arms.

## Out of scope (purge list)

- LLM anything (priority is mechanical: gates + dependencies + lanes).
- Session liveness (now.py owns it; the board links, does not duplicate).
- Auto-asking (the board carries drafted questions; a human or agent
  still fires them — no unattended interrupts).
- HTML/interactive views.

## Questions for the human (as options, or 'none')

None — P-gates for this FR's own scope were resolved by the filing
decision (yamlgraph-level, ratified 2026-07-16).

## Judgement (2026-07-16)

**Verdict: APPROVED — with the board's blast radius measured before a
line of code exists.** Status census over the live corpus: **723 FR
files**, statuses 252 Implemented / 115 Enforced / 57 Judged / 54
Approved / 43 Proposed / 28 Completed / 21 `✅` / 13 Rejected / 12 In
Progress / 11 in a `**Status**:` bold-variant format / 10 Superseded /
6 Draft + tail. TEMPLATE.md headings enumerated: **no Judgement
section exists** to amend.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **Repo→board completeness over 723 files = a 700-row board.** A board nobody scrolls is tribal knowledge with a generated header — the alarm-fatigue class (FR-737 F2) at board scale. The queue's subject is FRs *in motion* | Board and completeness lint scope to the **active set**: Proposed / Judged / Approved / In Progress / Draft / gated rows. Terminal statuses (Implemented, Enforced, Completed, ✅, Rejected, Superseded) excluded from the default view and from the completeness gate; `--all` renders the full census for archaeology |
| F2 | **Status is a heterogeneous free-text boundary**, not an enum: two bold formats (`**Status:**` / `**Status**:`, 11 files), emoji statuses, multiword variants ("Mechanism ENFORCED", "Sign-off RECORDED") | Normalize at the boundary: accept both bold variants; small canonicalization map for known families; unknown → parse-failure row with verbatim text preserved (AC-01 already pins never-dropped). No repo-wide header migration — the board adapts to the corpus, not the corpus to the board |
| F3 | `.judgement.md` companions lack Status headers (measured: 1 of N has one) — the repo→board lint would flag every companion as missing | Companions excluded from completeness / inherit parent status — the FR-738 U-3 resolution, reused verbatim |
| F4 | "Gates table parsed from the queue doc's `\| P# \|` rows, or gates.yaml — enforce decides" **defers a decision that belongs to Judgement.** Regex-parsing a hand-authored markdown table is exactly the fragile boundary the one_law warns about; config is truth (Commandment 3) | **gates.yaml, bound now.** Owner, ask-by, and the pre-drafted question block live as YAML fields (AC-03's contract becomes schema validation, not prose-grep). Queue-doc gate rows migrate once, at enforce |
| F5 | **AC-05 amends a template section that does not exist.** TEMPLATE.md has no Judgement section; judgements are ad-hoc `## Judgement (date)` headings in practice | AC-05 lands as two edits: (a) TEMPLATE.md gains a Judgement skeleton ending with the questions-or-none heading; (b) one sentence in the Sermon's **Judge** paragraph — the obligation must not depend on the template (FR-737 F6 precedent). This judgement itself practices the convention (terminal section below) |
| F6 | Cross-repo lint (`--project`) fails structurally where the sibling repo is absent (CI runners, other machines) — a lint that errors on environment is a bypass invitation | Missing project path ⇒ skip that repo with a printed notice, pass. The lint is a local pre-commit aid (now.py's family), never a CI gate on sibling-repo state |

**Purge additions:** repo-wide status-header migration; a rigid status
enum (canonicalization map + verbatim display only); CI enforcement of
cross-repo rows (F6).

**Scope frozen:** AC-01 (fixture → board, parse-failure rows) → AC-02
(two-way lint, active-set scoped per F1) → AC-03 (gated-row contract as
gates.yaml schema per F4) → AC-04 (cross-repo, skip-if-absent per F6)
→ AC-05 (template skeleton + Sermon sentence per F5) → AC-06 (raw read
of the first board against the live queue before the lint arms).

### Questions for the human (as options, or 'none')

None — all six findings resolved with corpus measurements; no
authority gaps found.

## Implementation (2026-07-16)

RED (10 witnesses, fixture corpus) → GREEN same session.
`scripts/fr_board.py` (collect_rows / active_rows / validate_gates /
render_board / check_board), `feature-requests/gates.yaml` (P1–P8
migrated from the queue doc, all answered), TEMPLATE.md judgement
skeleton + Sermon sentence (F5), pre-commit hook `fr-board-check`
(drift + gates schema). Tests: `pytest scripts/tests/ -q` — 10/10.

**AC-06 raw read of the first real board (yamlgraph +
ninchat_voice):**
- First generation: 401 rows, **198 PARSE-FAILURE** — alarm fatigue
  reborn at board scale. Census of failure families (CLOSED 9,
  Granted 5, Re-judged/Amended 13, `**ENFORCED**` bold-value 9,
  ❌/✓ 5, Enforcing 3) → canon map extended ONLY for measured
  families; genuinely ambiguous statuses (Sign-off RECORDED,
  Partially, Conditionally, Reopened, 22× missing header) stay
  visible as parse-failure rows. Second generation: 374 rows.
- **13 duplicate FR/NC IDs discovered** (FR-179/186/203/204/291/466/
  573, NC-112/211/233/243/293/300 — two different files each): the
  ID-allocation race (`cap-req-id-allocation-race`) made visible by
  the board's first render. Cleanup is its own chore, not this FR.
- Queue-doc agreement: NC-354/355/356 render Proposed — matching the
  queue doc's own staleness complaint verbatim; the board and the
  hand-authored table agree on the lag the board exists to expose.
- Status-lag exhibits on the active board: FR-179 (append-only
  changelog, shipped long ago) still reads In Progress; FR-735/736
  read In Progress with Completed bodies.
- check passes (rc=0) on the fresh board; hook wired with files
  filter on feature-requests/, fr_board.py, and the board itself.

**Deviations:** canon map grew beyond the judgement's initial census
(F2 anticipated this: "the board adapts to the corpus") — every
addition is backed by the AC-06 measurement above, none speculative.

**Deviation recorded late (integration reflection, same day):** two
proposed inputs — `git log` motion (RED/GREEN commits per FR ref) and
lane facts (files-touched contention) — were NOT implemented. Not
purged at enforce, just silently absent: an `intent_drift` instance
caught by the reflection, not by the process. Disposition now
explicit: **deferred, not dropped** — the AC-06 read showed the
board's proven value is status truth (parse failures, duplicate IDs,
lag); motion and lanes join when a consumer exists (the flush-advisory
or a session-start briefing that ranks by recency). Also found: the
board had **no reader but its own generator** — write-side integration
(pre-commit) shipped without read-side delivery, emission≠reception at
workflow scale. Fixed same day: `now.py` prints the plan-state pointer
with row count; the session-introspection skill routes "what's next?"
to the board before hand-derivation.

## Judgement Addendum (2026-07-16): F7 — the committed board crossed a repo boundary

Human review after completion: "feature-requests under projects are
grey area." Correct, and worse than grey — two defects:

| # | Finding | Resolution (binding, applied) |
|---|---------|-------------------------------|
| F7 | The committed board embedded `projects/ninchat_voice` rows: (a) **provenance** — yamlgraph history asserting foreign-repo state no yamlgraph commit controls (`workspace_is_not_boundary`); (b) **nondeterministic lint** — the drift check regenerated from ninchat's *current working tree*, so a stale or absent ninchat checkout on any other machine bounces innocent yamlgraph commits; F6's skip-with-notice amplifies this (skip changes content → guaranteed diff) | **Each repo owns its board.** The committed board and the `--check` lint are own-repo only; `--project` becomes the EPHEMERAL cross-repo stdout view (now.py's family — rendered, read, never committed or checked). Hook drops `--project`. AC-04 reinterpreted: cross-repo rendering works, on the terminal; ninchat gets its own board+hook via the NC-394 mirror pattern when picked up |
