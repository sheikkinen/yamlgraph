# Sixteen Not-Approveds: forensic of the FR-759–762 review-enforcement cycle

**Date:** 2026-07-27
**Context:** The dependency-governance arc (FR-759 OTel boundary, FR-760
langchain-core, FR-761 reproducible governance, FR-762 example taxonomy)
ran as a distributed pipeline: one agent planned, judged verdicts were
rendered through the adapter, Sonnet enforced, the review graph reviewed,
a human merged. The review-enforcement loop appeared to cycle forever:
4 PRs × 4 review rounds = 16 "Not approved" verdicts, zero approvals.
The human broke the loop by merging after the final fixes without a
fifth round. This entry is the post-mortem of *why it cycled*, from the
PR comment record and the code.

## The classification

Every blocking finding across all 16 rounds, sorted:

- **~45% genuine spec-vs-code drift.** UUIDv4 where the FR froze UUIDv7;
  "declared in any extra" where the FR froze an ownership model; a
  `try/except` top-level import that evaded the strict core gate;
  name-only `PENDING_GAPS` acting as a global whitelist; dotted
  `langgraph.checkpoint.redis` collapsed to `langgraph`; substring
  `nodes:` matching admitting prompt directories as example roots.
  All real. All P1-worthy. None ever re-opened after being fixed.
- **~30% environment contamination.** `git add -A` in a worktree that
  had sibling-FR files copied over; the fr-board `repo` column corrupted
  to `fr-760`/`fr-759` because the generator picked up the *worktree
  directory name*; generator stdout committed into module-map; a demo
  trace regenerated before the code it evidenced. None of these were
  implementation defects — they were the shared-workspace phenomenon
  (`one_session_one_repo`) leaking into PR diffs.
- **~15% serial review revelation.** Every review round stopped at the
  first blocking finding: *"Validations not run — merge already
  blocked."* With ~3 defect strata per PR, one-per-round guarantees
  ≥3 rounds. The cycle count was a property of the reviewer's
  stopping rule, not of the enforcer's error rate.
- **~10% plan/judgement defects.** FR-762's judgement forbade hook
  changes (gate C-5) while its acceptance criteria required a blocking
  gate — a contradiction the judge should have refused to freeze. Scope
  freezes (D-1..D-5 lists) never anticipated that mandatory pre-commit
  hooks force regenerating shared artifacts (`docs/fr-board.md`) into
  every PR touching `feature-requests/`.

## Answers to the four questions

**Was the plan too vague?** The opposite. The FRs froze unusually
precise constants, and that precision is what *generated* findings —
the reviewer could mechanically detect drift. The plan's real defects
were contradictions (hook-gate paradox) and blind spots (generated
artifacts), not vagueness. A vaguer plan would have produced fewer
review rounds and a worse codebase: the findings were the spec working.

**Was the enforcer not capable enough?** Capability was adequate;
*precision to frozen constants* was not. It implemented the plausible
neighbor of the spec — `UUID` for `UUIDv7`, "any extra" for "owning
extra." This is `plausible_wrong_answer` operating at the instruction
boundary: output passes shape check, violates the frozen value. The
strongest counter-evidence to "not capable": every cited defect was
fixed correctly in one round with RED/GREEN pairs, and no finding was
ever re-opened. The enforcer's second failure mode was git hygiene in
a contaminated shared repo, not code.

**Was the reviewer nagging?** Mostly no — a gate evadable by
`try/except` is not a gate; the scanner-bypass findings alone justify
the review graph's existence. Two legitimate complaints: PR 462 round 4
demanding the necessary-and-correct `fr_board.py` fix be split out was
scope-purity formalism (the human rightly merged over it), and the
stop-at-first-blocker policy was the primary cycle amplifier.

**Is the codebase sound now?** Gates green on merged main:
`direct_import_scan --strict` 0/0, `req_coverage` 375/375, fr-board
check clean; all final-round findings were fixed pre-merge. Two
residuals found by this forensic itself: (1) `example_taxonomy_scan.py`
walks the raw filesystem and counts **gitignored** directories
(`examples/yamlgraph_gen/outputs/*`) as example roots — false "stale"
failures on any dev machine with local generator outputs, CI-green only
because clean checkouts lack them (→ FR-763); (2) the scanner's
`PENDING_GAPS` FR-760 entries are moot now that langchain-core is
declared — dead weight by its own "entry dies with FR-760" comment.

## The trap

**`composition_bug`, pipeline edition.** Each component was defensible
alone: a precise plan, a competent enforcer, a rigorous reviewer, a
scope-frozen judgement. The policy connecting them guaranteed ~4 rounds
per PR: precise-but-contradictory plan × enforcer loose on frozen
constants × contaminated shared workspace × one-blocker-per-round
reviewer. Nobody was broken; the *connection* was. The Scripture already
names this for code (`composition_bug`); this is its process-pipeline
instance — trace the full verdict chain end-to-end before blaming any
role.

A second observation worth naming: **the loop had no convergence
criterion.** The review doctrine emits binary verdicts with no
"approved with advisory notes" state, so any nonzero finding — including
a stale PR body — produced another full cycle. Termination came from
outside the loop (human merge authority). An automated pipeline with a
binary gate and a breadth-limited reviewer is a slow oscillator by
construction.

## Heuristics

- **Review breadth bounds cycle count.** A reviewer that stops at the
  first blocker converts N defect strata into N round-trips. Enumerate
  *all* blocking findings per round; the enforcer can fix them in one
  pass. The cost of continued validation after the first blocker is
  minutes; the cost of a hidden stratum is a full cycle.
- **Frozen constants need value-level witnesses at enforcement time,
  not just review time.** Every finding of the `UUIDv7-as-UUID` class
  was detectable by a test the *plan* could have demanded: when an FR
  freezes a value tighter than its type, the acceptance criteria must
  name the value-level assertion (`uuid.UUID(x).version == 7`), so the
  enforcer writes it in RED before implementing.
- **Generated artifacts are scope, whether the judgement says so or
  not.** Any judgement freezing a deliverables list in a repo whose
  hooks regenerate shared artifacts must either include those artifacts
  or exempt them explicitly — otherwise every PR is born out-of-scope.

## Seed

Can the review-enforce loop carry a convergence budget — e.g. the
reviewer must enumerate all blockers per round, and if round N+1 finds
a blocker in a file untouched since round N, that finding is charged to
the *reviewer's* breadth, not the enforcer's competence — making the
oscillation cost visible to the process that causes it?
