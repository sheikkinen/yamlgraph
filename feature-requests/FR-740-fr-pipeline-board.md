# FR-740: FR Pipeline Board — generated priority view + structural interrupts

**Status:** Proposed
**Type:** Feature (process tooling — LLM-free)
**Effort:** 1 day (board + lint) + template/convention edits
**Requested:** 2026-07-16
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
