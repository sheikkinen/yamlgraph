# Problem brief: diary trap recurrence is detected by memory, not measurement

**Prior art:** dispositioned in the FR this brief produces (closed-input
brief per FR-890 R-2).

## Problem statement

The diary corpus (docs/diary/, 300+ entries) is the repository's incident
record: each entry names cognitive traps, heuristics, and seeds. The
governing process says a heuristic that appears twice becomes an FR and a
confirmed recurrence graduates to Scripture — but recurrence COUNTING is
manual and memory-based: a trap graduates only if whoever hits it happens
to remember its earlier occurrences. The philosopher daemon that scanned
for recurring markers is dead (CAP-113 lineage); the Scripture's own seeds
list has carried "diary graduation pipeline" as unbuilt for months. The
corpus is append-only and growing; every ungraduated recurring trap is a
defect class the doctrine already paid for but cannot bill. There is no
current mechanism that reads every entry and reports which traps recur,
at what frequency, across which time spans — so graduation candidates are
sampled by recollection rather than censused, and the sampling is biased
toward recent and personally-witnessed traps.

## Classification

judgement/analysis/generation

## Constraints

- The corpus is large (300+ markdown entries, heterogeneous structure:
  named traps, prose insights, Seed: markers) and grows weekly; per-entry
  processing cost must be trivially cheap so the census can re-run on
  cadence.
- Output must be actionable in the existing graduation flow: recurrence
  candidates with citations (entry filenames), suitable for a
  .chaplain/inbox proposal; the graduation bar is 2 occurrences → FR,
  confirmed recurrence → Scripture.
- Evidence discipline: every claimed recurrence must cite the entries it
  occurred in; disagreement/uncertainty must be visible, not averaged
  away; abstention on unparseable entries preferred over guessing
  (gate_checks_shape_not_substance).
- Existing instruments: the philosopher graph (.chaplain/graphs/
  philosopher — copilot-based marker scan, linear), diary_index demo,
  and the just-enforced corpus_census pipeline (FR-892, PR #479 — merge
  pending; any consumer of it depends on that merge or its branch).
- The repository is public: census outputs must not surface customer
  facts quoted inside diary entries.
- Known-truth validation exists: at least two traps with ≥3 witnessed
  recurrences THIS WEEK (a stale commit-message-file trap; line-pinned
  gate references bouncing commits) must surface in any honest census —
  a run that misses them is invalid (hidden-canary discipline).

## Witnessed incidents

- 2026-08-26: the stale tmp/msg.txt trap hit its 4th strike; the count
  is tracked in one agent's machine-local memory notes, invisible to
  other devices and agents — the recurrence record does not live in the
  repo it governs.
- 2026-08-26: line-pinned gate references (noqa confessions, hedging
  allowlist) bounced three commits in one day across two FRs; the
  pattern is named only inside individual diary entries, never counted.
- 2026-08-26: three heading-consumption editing errors in one session,
  self-reported in a diary entry; no mechanism would ever aggregate
  this into a graduation candidate.
- Scripture seeds list: "diary_graduation_pipeline — mechanical pipeline:
  diary entry with 3+ recurrences across projects → auto-proposal to
  .chaplain/inbox/" — present as an unbuilt seed; the philosopher's
  distill/challenge gate exists but its scan stage samples markers
  rather than censusing the corpus.
