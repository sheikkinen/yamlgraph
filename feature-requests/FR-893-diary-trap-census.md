# Feature Request: Diary Trap Census — Recurrence by Measurement, Not Memory

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-26
**First consumer / first event:** the next Scripture graduation — instead
of a recollected pattern, the proposer attaches the census ledger row
(trap, count, entry citations) to the .chaplain/inbox proposal; first
event is the RW-2 acceptance run whose known-truth traps must surface.
**Research:** [FR-893.research.md](FR-893.research.md)

**Prior art:** FR-892 (corpus_census pipeline — this FR is its first
post-proof real consumer; the census is a manifest pair + rubric, zero
new graph YAML by design). FR-254 (diary-index — committed extraction of
trap/heuristic markers; the census's vocabulary source). The philosopher
graph (.chaplain/graphs/philosopher — marker sampling + distill/challenge
gate; this census feeds its candidates rather than replacing its
judgement). FR-593 (vocabulary canonicalization lineage — trap names
drift; exact-match counting undercounts). Scripture seed
`diary_graduation_pipeline` (the unbuilt mechanism this implements in
census form). CAP-113 (dead daemon precedent — this is cadence-run,
blocking, no daemon).

## Summary

A diary census configuration for the FR-892 pipeline: discovery manifest
(glob docs/diary/*.md), extraction manifest (read entry), rubric asking
one judgement per entry — the named traps/heuristics present, normalized
to short canonical labels, with evidence spans and abstention — plus an
LLM-free recurrence aggregator that groups by canonical label, counts
across entries, emits a graduation-candidate table (label, count, entry
citations) and, for candidates at the bar (≥3), a draft .chaplain/inbox
proposal. The run is gated by the hidden-canary discipline: two
known-truth traps from 2026-08-26 must surface or the run is invalid.

Dissents adopted from the research record: the os-infra insight becomes
the committed artifact rule — the census ledger + candidate table are
COMMITTED (docs/diary/census/), so recurrence state lives in the repo it
governs, not in any agent's machine-local memory. The subtractionist
discipline bounds automation: the census only PROPOSES with citations;
graduation judgement remains with the chaplain/human flow (no
auto-graduation).

## Value Statement

Graduation candidates stop depending on who happens to remember prior
occurrences: every recurring trap in 300+ entries is counted, cited, and
proposable — the doctrine's own 2×/3× bars become measurable.

## Problem

See the closed brief
([diary-trap-recurrence-census.md](research-briefs/diary-trap-recurrence-census.md)):
recurrence counting is memory-based and machine-local (tmp/msg.txt trap's
4th strike tracked only in one agent's local memory notes); the
philosopher's scan samples markers; the graduation seed has been unbuilt
for months; three recurring traps witnessed THIS WEEK are uncounted
anywhere in the repo.

## Proposed Solution

Per the research table (5 classes; 3-persona convergence on the census
shape; both dissents folded as constraints, not builds):

1. **Adapters** (examples/demos/corpus_census/adapters/, python-runtime
   manifests per FR-892 convention): `diary_discover` (glob
   docs/diary/diary-*.md, bounded, sorted), `diary_extract` (read entry,
   cap chars). Zero new graph YAML.
2. **Rubric prompt** (data, not code): per entry, output the list of
   named traps/heuristics with canonical snake_case labels (the
   diary-index vocabulary as the normalization hint — FR-593 lineage:
   the model normalizes label variants; exact-match is the known
   failure), one evidence span each, abstain when an entry names none.
3. **Recurrence aggregator** (LLM-free, sibling of the census reducer):
   consumes the census JSONL ledger; groups by canonical label; emits
   `docs/diary/census/recurrence-YYYY-MM-DD.md` (label, count, entry
   citations, first/last seen) + a draft inbox proposal file per
   candidate at ≥3 count. Fail-closed: a label without citations is
   rejected; the canary check runs here.
4. **Canary gate (RW-2 acceptance)**: the run is valid only if the
   stale-commit-message-file trap and the line-pinned-gate trap surface
   with plausible counts; absence fails the aggregator loudly (the
   census's own hidden-canary discipline, FR-890 lineage).
5. **Cadence**: manual/scripted re-run (scripts/diary_census.sh thin
   wrapper); NO daemon (CAP-113).

## Acceptance Criteria

- [ ] AC-01: RED first — failing test for the recurrence aggregator contract (grouping, citation requirement, canary gate).
- [ ] AC-02: Diary adapters + manifests bind to the unchanged corpus_census graph; the census runs over the full docs/diary/ corpus on a cheap pinned model.
- [ ] AC-03: The aggregator is LLM-free; deterministic tests witness grouping, count thresholds, citation preservation, label-without-citation rejection, and abstention rows passing through uncounted.
- [ ] AC-04: Canary gate: a fixture ledger missing the known-truth traps fails the aggregator; the real run surfaces both 2026-08-26 traps with ≥3 citations each — recorded in the FR.
- [ ] AC-05: Committed artifacts: census ledger + recurrence table under docs/diary/census/ (in-repo recurrence state, os-infra dissent adopted); at least one real graduation-candidate draft written to .chaplain/inbox/ with entry citations.
- [ ] AC-06: The run record notes cost and duration (cadence feasibility evidence).
- [ ] AC-07: Changelog fragment, FR status update, diary reflection.

## Out of Scope

- Auto-graduation or Scripture edits (judgement stays human/chaplain —
  subtractionist dissent adopted as a boundary).
- Rebuilding the philosopher daemon or changing its graph.
- Cross-project diary sweeps (ninchat_voice etc. — follow-up once
  in-repo census proves out).
- Migrating diary-index or any FR-892 C-5-protected graph.

## Alternatives Considered

See [FR-893.research.md](FR-893.research.md): append-only shell-pipeline
log (os-infra — its in-repo-state insight adopted, its grep/awk counting
rejected: trap names drift, semantic labeling needed); diary-index +
deterministic map composition (yamlgraph-native — close cousin; rejected
in favor of the already-proven census pipeline, same shape fewer parts);
retire-the-seed manual proposals (subtractionist — adopted as the
automation boundary, rejected as the whole answer because the witnessed
bias is structural, not disciplinary); staged index-first mining
(librarian, external precedent URL — the cheap-scan-then-deep-read
optimization deferred until cost evidence demands it).

## Related

- FR-892 (pipeline + slot binding, PR #479 — **dependency: this FR
  enforces only after #479 merges or on its branch**)
- docs/mercury-census/findings.md (RW-2 in the acceptance-test table)
- Scripture: `diary_graduation_pipeline` seed, `graduation` process,
  hidden-canary mechanism (canary-recall inbox proposal)
