# Feature Request: Diary Trap Census — Recurrence by Measurement, Not Memory

**Priority:** MEDIUM
**Type:** Feature
**Status:** Completed (enforced 2026-08-26 on worktree feat/fr-893; RED 18435eff, GREEN follows)
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

## Ideal Result

A maintainer runs one bounded command over the full diary corpus and,
minutes later, inspects committed artifacts under `docs/diary/census/`:
a recurrence table where every row carries canonical label, distinct-entry
count, first/last seen dates, and entry citations. Attaching a
graduation-candidate row to a `.chaplain/inbox` proposal is a copy-paste
act requiring no agent memory. The doctrine's own bars (2× → FR,
confirmed recurrence → Scripture) become queries over a committed table
instead of acts of recollection — and a trap's strike count survives
devices, sessions, and agents because it lives in the repo it governs.

## Raw-output read evidence (R-2, read 2026-08-26 before authority)

Five raw entries read end-to-end; each detail below is something a
generated summary could not fabricate:

1. `docs/diary/` holds **1271 entries, not the "300+" the brief assumed**
   — and at least four structural genres: reflections, inquisitor audits
   (✓/⚠ finding lists), daily digests, git-reports. Cost and rubric
   design must handle 4× the assumed volume and non-reflection formats.
2. `diary-2026-08-25-the-census-taker-reads-its-own-ledger.md:28-33`
   describes the msg-file trap WITHOUT the literal token "tmp/msg.txt
   trap": "a `&&`-chain aborted at a failed `git add`, so the later
   `printf > tmp/msg.txt` never executed — three subsequent commits
   reused a stale message file." Vocabulary drift is concrete, not
   hypothetical: exact-match counting would miss this canary instance.
3. `diary-2026-08-26-reflection-fr-892-…:33-36` names the line-pinned
   gate trap AS an instance of an existing Scripture trap
   (`gate_checks_shape_not_substance` — "the gate checks WHERE, not
   WHAT"): recurrence labels have instance-of relations to Scripture
   entries; the rubric must capture the specific label, not collapse to
   the parent.
4. `2026-03-09-inquisitor-audit-64.md` already PROPOSED this FR's
   mechanism five months ago: "any finding flagged ≥3 times without a
   fix should auto-escalate to an FR" and seeded `audit_dedup.py` — the
   census must also mine audit-genre entries, and this FR dispositions
   that seed.
5. `2025-04-23-reflection-fr-273-…` uses an older header dialect
   (`# Reflection — FR-273`, `## Trap encountered`) — marker extraction
   cannot key on today's header conventions. Mechanical priors: 772/1271
   entries carry `Seed:`; only 11 mention `msg.txt` by string — the
   distinct-entry canary bar of ≥3 is realistic but not slack.

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
   consumes the census JSONL ledger; groups by canonical label; **count
   unit = distinct diary entries (R-4)** — multiple evidence spans within
   one entry are preserved in the ledger but count once; emits
   `docs/diary/census/recurrence-YYYY-MM-DD.md` (label, distinct-entry
   count, entry citations, first/last seen) + a draft inbox proposal per
   candidate at ≥3 distinct entries. Fail-closed: a label without
   citations is rejected; the canary check runs here.
   **Public-safe artifact contract (R-3):** committed artifacts
   (recurrence table, inbox drafts) contain ONLY canonical label, count,
   entry paths, line ranges/headings, first/last seen, abstention counts,
   and short non-sensitive rationale; raw evidence spans stay in the
   uncommitted run ledger (tmp/) referenced by path — no diary prose is
   quoted into committed census artifacts (deterministic by construction:
   the committed writer has no span column).
4. **Canary gate (RW-2 acceptance)**: the run is valid only if the
   stale-commit-message-file trap and the line-pinned-gate trap surface
   with ≥3 distinct-entry citations each (R-4 unit); absence fails the
   aggregator loudly (the census's own hidden-canary discipline, FR-890
   lineage).
5. **Cadence**: manual/scripted re-run (scripts/diary_census.sh thin
   wrapper); NO daemon (CAP-113).

## Acceptance Criteria (revised per judgement — supersede the original set)

- [ ] AC-01: RED first — failing tests: grouping by canonical label, citation preservation, threshold filtering, label-without-citation rejection, abstention rows excluded from counts, canary failure.
- [ ] AC-02: FR carries `## Ideal Result` and `## Raw-output read evidence` (≥5 cited samples incl. both canary families) before enforcement — DONE above.
- [ ] AC-03: Diary manifests bind to the unchanged FR-892 corpus_census graph; the full committed corpus (1271 entries) runs on a cheap pinned model with only manifests + rubric/config.
- [ ] AC-04: Rubric output schema requires canonical label, evidence span, item ref/source index, confidence, abstention marker+reason; diary-index vocabulary as normalization hints; abstention when no named trap present.
- [ ] AC-05: Aggregator LLM-free; deterministic tests prove grouping, distinct-entry counting, citation preservation, first/last seen, label-without-citation rejection, public-safe output (no span column in committed artifacts), abstentions uncounted.
- [ ] AC-06: Canary gate fails loudly on a fixture ledger missing either family; the real run surfaces both 2026-08-26 traps at ≥3 distinct entries; observed counts recorded in the FR.
- [ ] AC-07: Committed artifacts under docs/diary/census/: public-safe recurrence table + run evidence with model, prompt version, cost, duration, corpus bounds, git SHA.
- [ ] AC-08: ≥1 real graduation-candidate draft written to .chaplain/inbox/ only after the canary gate passes, with label, count, citations, and an explicit graduation-stays-human statement.
- [ ] AC-09: Changelog fragment, REQ tagging on new tests, FR status update, diary reflection.

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

- FR-892 (pipeline + slot binding) — **enforcement gate (R-5/C-2): FR-892
  is MERGED to main (#479, 06d1dfe4); enforcement branches from main and
  verifies corpus_census + slot binding present before running**
- docs/mercury-census/findings.md (RW-2 in the acceptance-test table)
- Scripture: `diary_graduation_pipeline` seed, `graduation` process,
  hidden-canary mechanism (canary-recall inbox proposal); disposition of
  inquisitor-audit-64's `audit_dedup.py` seed (raw-read sample 4)

## Implementation Record (2026-08-26)

Enforced on worktree `feat/fr-893` from merged main (C-2 verified). TDD:
RED 18435eff (10 aggregator witnesses), GREEN follows. REQ-YG-624
(CAP-249 extended to FR-892, FR-893).

**Deliverables:**

- D-1/D-2: `diary_adapters.py` + manifests (python-runtime, FR-892
  convention); discovery is month×decade batchable (`source
  "docs/diary:<needle>"`) because the corpus (1271 entries) exceeds the
  graph's 200-item map cap — three months alone exceed it (312/242/250).
- D-3: rubric as a `--var` (zero prompt YAML, C-3): comma-separated
  canonical snake_case labels in the judgement field; abstain when the
  entry names no trap. Genre handling verified: git-reports and digests
  abstain with reasoned justifications.
- D-4: `diary_recurrence.py` — LLM-free aggregator: distinct-entry
  counting (R-4), public-safe table (no evidence-span column by
  construction, R-3), Scripture-key exclusion (graduated labels are
  measured, never re-proposed), inbox emission threshold separate from
  the table threshold (the chaplain consumes inbox on pickup — flood is
  operational).
- D-5: **canary gate fired for real**: the first full-corpus aggregation
  FAILED — exact-label canaries found 0 entries because the vocabulary
  drift predicted by raw-read sample 2 is total (`tmp_msg_txt`,
  `stale_tmp_msg_file`, `tmp_msg_file_loss` — never the literal). Gate
  upgraded to family-substring matching ('|' alternatives). Observed:
  msg family = exactly 3 distinct entries (at the bar); line-pin family
  ≈6 across 4 label variants.
- D-6: 2 inbox drafts committed (protocol_archaeology, invisible
  _decisions — 12 entries each) with a genre caveat: both are
  world-digest themes, not first-person incident traps; judge weighs.
  3 alias drafts pruned manually (silent_fallback ×2 = Commandment 6;
  boundary_normalization = the_one_law) — synonym resolution recorded
  as future work, not built (C-6 discipline).
- D-7: `scripts/diary_census.sh` — 24 batches, 1266/1271 entries
  censused (5 files lack date-matching names), 144 abstentions,
  1700 distinct labels, **duration 1560s (~26 min), model
  claude-haiku-4-5, est. cost ≈ $1**; run metadata embedded in the
  committed table (git SHA 18435eff).
- D-8: 12 deterministic witnesses incl. family-canary drift test and
  Scripture-exclusion test; changelog fragment; this record; diary
  reflection.

**Decisions / deviations:**

- Canary spec upgraded from exact label to family alternation — the
  judgement's own word "family" (R-4/AC-06) made this a clarification,
  not a scope change; witnessed by test_canary_family_matches_drifted_labels.
- Inbox emission bar set to 10 (table bar stays 3): 33 threshold-3
  candidates would flood the consumed-on-pickup inbox. Recorded as
  operational-hazard deviation; the full candidate list is in the
  committed table.
- Headline census finding (beyond the FR's goal): the top ungraduated
  recurrence signals are ALIASES of graduated doctrine (silent_fallback
  family 34+ entries under 4+ names) — vocabulary consolidation, not new
  graduation, is the corpus's loudest request. Seeded in the diary.

## Post-merge reconciliation vs reference/patterns/corpus-map-reduce.md (2026-08-27)

The FR-894 reference (concurrent lane) codified the pattern this FR
instantiates; cross-checking exposed two implementation gaps against its
freeze/arithmetic invariants, recorded here as candidate follow-ups (not
built — no authority under this FR):

- **Per-item content hashes absent**: the ledger records item_ref + run
  git SHA, but not a content hash per entry — rows are not tied to item
  content identity across runs (reference freeze stage; invariant 5
  "hashes"; `artifact_carries_code_identity` seed).
- **Cost/call totals not computed in code**: duration and cost were
  recorded via manual `--meta`; primary/reduction call counts should be
  computed by the wrapper (reference cost contract).

Contribution in the other direction: this FR's canary-gate firing (exact
labels → 0 hits under total vocabulary drift) graduated into the
reference as its 8th required invariant (withheld known-truth, family
matching) — coverage arithmetic alone cannot prove semantic validity.
