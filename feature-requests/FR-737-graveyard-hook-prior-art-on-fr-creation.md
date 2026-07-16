# Feature Request: FR-737 Graveyard Hook — Prior-Art Retrieval on FR Creation

**Priority:** MEDIUM
**Type:** Enhancement (enforcement infrastructure)
**Status:** Completed
**Effort:** 0.5 day
**Judged:** 2026-07-15 — the proposed ranking FAILED its own
counterfactual when measured; repaired by pin before any code exists
**Requested:** 2026-07-15
**Completed:** 2026-07-16
**Spawned by:** the FR-070 resurrection (2026-07-15): a committed plan doc
recommended a Pyodide "playground" while FR-070 (`yamlgraph serve` web
playground, REJECTED 2026-02-21, graduated doctrine "No UI, ever") sat
unqueried in `feature-requests/`. Surfaced only by the user's vague
recollection — two Red Hat passes, both human-triggered. Diary:
`docs/diary/diary-2026-07-15-the-vague-memory-that-beat-the-archive.md`.

## Summary

Add a prior-art check to the existing PostToolUse hook
(`.github/hooks/scripts/checks/fr-checks.sh`): when a **new** FR file is
created, extract nouns from its filename, grep the FR corpus —
**including rejected FRs** — and emit ranked hits into the hook output.
Retrieval delivered to the acting agent's context without requiring
suspicion, which was the entire failure mode. Plus one Scripture line
making disposition of surfaced prior art a Judge obligation.

## Problem

The FR archive is query-blind long-term memory: retrieval requires
suspecting a precedent exists. The context window dominates (availability
bias in machine form), so proposals are checked against *recent* context,
never against the decision record. The strongest precedents — REJECTED
FRs — are the least likely to be re-read and the most expensive to
violate: FR-070's doctrine survived four months and two costume changes
(local server → WASM) without ever being loaded into a context window.

Placement matters: the chaplain pipeline is NOT the real process (it has
not run in weeks; the real process is plan-judge-enforce in parallel
interactive sessions). The hooks are the only mechanical surface that
fires in every session, on every agent, chaplain included — enforcement
must attach to what runs, not to what is documented as running.

## Proposed Solution

### 1. `build_prior_art()` in fr-checks.sh

- **Trigger:** edit-tool events on `feature-requests/*.md` where the file
  is newly created (not present in `git ls-files` — status edits and
  judgement folds must not re-nag).
- **Noun extraction (mechanical, no LLM — hooks stay fast and offline):**
  strip the `FR-XXX-`/`NC-XXX-` prefix and `.md`, split on hyphens, drop
  a small stopword list (fix, add, support, node, graph, yaml, demo…).
- **Corpus grep:** case-insensitive, whole-word-ish match of each noun
  across `feature-requests/*.md` (including `REJECTED-*` and bodies with
  `Status: Rejected`), excluding the newly created file itself (F3:
  in the counterfactual the new FR outranked its own precedent).
- **Ranking (F1, judged pin — the proposal's distinct-noun count FAILED
  its own counterfactual when simulated on the 720-file corpus):**
  score = Σ 1/corpus_freq(noun) over matched nouns — inverse corpus
  frequency, so one rare noun (pyodide: 1 file, playground: 2) outranks
  any pile of generic ones (spike: 47). Cap at 5 files.
- **Noise floor (F2, judged pin; threshold corrected by addendum A1):**
  emit a candidate only if it matches ≥1 RARE noun — rare = corpus
  frequency **≤ 20 files (≈3% of the 720-file corpus)**; when no
  filename noun is that rare, emit NOTHING — silence over alarm fatigue
  (255/720 files match ≥1 noun for an ordinary filename; a hook that
  always emits trains agents to ignore it). The original 10% floor
  (≤72 files) admitted `spike` (47) — F1's own generic-drowning
  exemplar — so every `spike-*.md` filename would have emitted five
  tied 1/47 hits.
- **Output (advisory, non-blocking):**

  ```
  ⚠ prior art for FR-737 (nouns: pyodide, lint, playground):
    070-gui-web-playground.md  [REJECTED]  matches: playground
    FR-723-graph-export-...md  [Completed] matches: lint
  Disposition required at judgement (Scripture: Judge step).
  ```

  Status tag read from the file's `**Status:**` line. Non-blocking by
  design: a common-noun match must not deny an edit — the hook's job is
  retrieval, judgement stays with the session
  (`gate_checks_shape_not_substance` cuts both ways).

### 2. Scripture amendment (one line, Judge paragraph)

> Prior art surfaced at FR creation — including rejections — must be
> dispositioned in the FR or its judgement before authority is granted;
> a rejected FR is precedent, and a proposal that re-enters its territory
> must distinguish itself or die by the same rationale.

### 3. Hook test

`.github/hooks/tests/`: fixture event creating an FR whose filename nouns
hit a known rejected FR (070's "playground" is the natural fixture) →
assert output contains the warning block and the `[REJECTED]` tag; a
status-only edit to an existing FR → assert silence.

### Out of scope (purge list)

- LLM-driven semantic similarity (grep first; escalate only if noun
  matching proves insufficient in practice — `two_strike_split` applies
  to the hook itself).
- Chaplain-stage integration (fires via the same file boundary if the
  chaplain ever runs — nothing to add).
- Sweeping REJECTED rationales for un-Scriptured doctrine (separate seed,
  separate proposal).
- Blocking/denial semantics.

## Acceptance Criteria

- [ ] AC-01 RED — hook tests: new-FR event with rejected-FR noun overlap
      emits the prior-art block with status tags; existing-FR edit emits
      nothing; noun extraction drops prefixes and stopwords; a filename
      with only common nouns (all above the A1 floor) emits nothing
      (F2); a `spike`-only filename emits nothing (A1 witness); the new
      file itself is never a candidate (F3).
- [ ] AC-02 GREEN — `build_prior_art()` implemented with IDF ranking
      (F1); counterfactual witness: replaying today's incident (a file
      named `*-pyodide-playground.md`) surfaces
      `070-gui-web-playground.md` with `[REJECTED]` **in the top 5 by
      IDF score** (measured at judgement: #2).
- [ ] AC-03 — Scripture Judge-paragraph line added (copilot-instructions.md).
- [ ] AC-04 — hooks README updated (new check documented, output format).
- [ ] AC-05 — changelog fragment; diary reflection. No REQ/CAP:
      confirmed at judgement (F5) — follow `test_fr_checks.py`'s own
      convention (unmarked; the broader hook-test precedent is mixed,
      3 files do carry marks).

## Alternatives Considered

- **Judge-step instruction alone:** decays (`two_strike_split`); invites
  one-sentence compliance ("graveyard searched, empty") — an empty grep
  is a claim needing a positive control (NC-383 lesson).
- **Chaplain research-stage integration:** polishing a stopped machine;
  rejected on observed-process grounds (the correction that shaped this
  FR).
- **Example graph for precedent search:** wrong genre — internal process
  tooling, not a user-facing pattern; and the spent-example lesson
  (cwe-classifier, same day) argues against building instruments without
  consumers.
- **Semantic/embedding search:** heavier, needs a model at hook time;
  noun-grep found FR-070 in one call — start mechanical.

## Related

- FR-070 (the motivating resurrection), FR-729 (generate-or-gate claims)
- `.github/hooks/scripts/checks/fr-checks.sh`, `.github/hooks/README.md`
- `docs/diary/diary-2026-07-15-the-vague-memory-that-beat-the-archive.md`
- `/memories/repo/check-graveyard-before-proposing.md` (session-side cure,
  this FR is its mechanization)

## Judgement (2026-07-15)

**Verdict: APPROVED — with the central mechanism corrected by
measurement before a line of code exists** (read_raw_output_first
applied to the hook's own design: the ranking was simulated against
the real 720-file corpus).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **The proposed ranking fails AC-02's own counterfactual.** Measured: `spike-pyodide-playground.md` → 49 files match ≥1 noun; `070-gui-web-playground.md` scores 1 (playground), TIES with ~45 generic `spike`-only matches (spike occurs in 47/720 files) and falls outside the top-5 cap. Distinct-noun count lets common nouns drown the rare one — the exact availability bias the hook exists to fight, rebuilt inside the hook | Rank by **inverse corpus frequency**: score = Σ 1/freq(noun) over matched nouns. Measured result: 070 surfaces at #2 on the counterfactual; a generic filename (off-catalog-claim-handling) yields its TRUE prior art (722/730/733) as top-5 |
| F2 | **Noise floor needed**: 255/720 files match ≥1 noun for an ordinary filename; a hook that always emits 5 files trains agents to ignore it (alarm fatigue = `audit_as_ritual` at machine speed) | Emit a candidate only if it matches ≥1 RARE noun (corpus frequency ≤ 10% of files); if no filename noun is that rare, **emit nothing** — silence over noise. Verified: pyodide(1), playground(2), catalog(8), webllm, icpc2 all qualify; error/handling/process do not |
| F3 | **Self-hit pollution**: in the counterfactual the top hit was FR-737 itself (its body cites pyodide/playground) — the newly created file and same-territory citations outranked the precedent | The newly created file is excluded from candidates. Other body-level citers stay: they point at the same territory, which is signal |
| F4 | Filename-only noun extraction is thin but MEASURED sufficient for the motivating class | Keep filename-only (purge list stands); title-line extraction is the recorded escalation path if a real miss occurs (`two_strike_split` applies to the hook) |
| F5 | AC-05's "no REQ/CAP" precedent claim is MIXED in reality: 3 of the hook-test files carry `mark.req`; `test_fr_checks.py` itself is unmarked | Confirmed as proposed: follow the target file's own convention (unmarked). Hooks are process infrastructure |
| F6 | Scripture line: the obligation must not depend on the hook | Approved for the Judge paragraph, worded as a standing obligation — the hook is a retrieval aid; disposition is required whether or not the hook fired |

**Purge list (unchanged + additions):** LLM/semantic similarity,
chaplain-stage integration, REJECTED-rationale sweeps, blocking
semantics, title/body noun extraction (F4), any per-noun weighting
beyond 1/freq.

## Judgement Addendum (2026-07-15): A1 — the F2 floor contradicted F1's exemplar

Author's reread after the fold: F2 defined rare as ≤ 10% of files
(≤ 72/720), but F1's designated generic-drowning noun `spike` sits at
47/720 = 6.5% — **rare by the F2 floor**. Consequence: every
`spike-*.md` filename (a common naming pattern) passes the emission gate
on `spike` alone and emits five tied 1/47-score hits — precisely the
alarm-fatigue class F2 exists to prevent. The judgement's own verified
qualifying list (pyodide 1, playground 2, catalog 8) sits an order of
magnitude below the floor it was meant to calibrate.

**Binding correction:** rare = corpus frequency **≤ 20 files** (absolute
count; ≈3% today, and it tightens as the corpus grows, which is the
correct direction for a "rare" notion). Verified against the F1/F2
measurements: pyodide(1), playground(2), catalog(8) qualify; spike(47),
error, handling, process do not. AC-01 gains the witness: a spike-only
filename emits nothing.

## Implementation (2026-07-16)

RED 2d67b0d1 (7 tests: 3 condemning positive paths, 4 vacuous negative
paths — split declared at RED time); GREEN this commit. All ACs
discharged:

- `prior_art.py` alongside the checks (bash stays thin): filename-noun
  extraction, one-pass corpus scan, IDF scoring, A1 floor (constant
  `RARE_MAX_FILES = 20`), self-exclusion, top-5 with status tags
  (REJECTED uppercased, filename-prefix REJECTED- recognized).
- fr-checks.sh calls it only for files absent from `git ls-files`
  (tracked edits and judgement folds never re-nag; non-repo temp dirs
  count as new, which is what makes the hook tests hermetic).
- AC-02 counterfactual, measured live on a copytree of the real corpus:
  FR-070 at #2 — exactly the judgement's predicted position; #1 is
  FR-737 itself (body-citer, kept by F3's ruling — same-territory
  citation is signal, and the mechanizing FR is now the loudest pointer
  into its own territory).
- Scripture Judge paragraph gains the F6 standing obligation; hooks
  README documents the check; changelog fragment; diary.
- 72/72 hook tests green (full `.github/hooks/tests/` suite).

One test-side fix during GREEN: the IDF-order assertion's line matcher
caught the header line (contains `.md`); tightened to candidate-line
indent. Zero implementation churn against the judged pins.

## Usage Comments (2026-07-16, first field use — NC-393 creation, ninchat_voice)

First real-world firing: `NC-393-telemetry-map.md` triggered
`⚠ prior art … (nouns: telemetry, map)` with four hits. Feedback from
the agent-author it fired at:

**U-1 (critical) — the warning reached the human, not the agent.** The
hook emitted `decision: feedback / issues-found` (audit
2026-07-16T05:17:28), the user saw the warning — and the authoring
agent's `create_file` result contained nothing. NC-393 was filed,
committed, and pushed with NO disposition: the exact failure mode the
hook exists to prevent, performed under the hook's nose. An unseen
advisory is no advisory. Until PostToolUse feedback provably reaches
the agent surface in use, the disposition requirement is enforced only
by luck. Cheapest hard backstop: re-run `prior_art.py` in pre-commit
for NEW FR files and fail when hits exist but the FR lacks a
`**Prior art:**` disposition line — same check, moved to a boundary
that cannot be unseen. (Filed as the natural F7 follow-up candidate.)

**U-2 — signal 1/4, and the ranking didn't surface it.** The genuinely
relevant hit (NC-361's judgement — discusses telemetry channels in the
same territory NC-393 maps) ranked third; NC-186/NC-241/NV-238 match
"telemetry" incidentally in body prose. Within a same-noun tie the
order appears corpus-incidental. Two cheap improvements: weight
title/Summary-section matches above stray body mentions, and break
same-noun ties by match count. The floor did its job ("map" produced
zero noise) — the residual noise is *where* in the document the noun
sits, not how rare it is.

**U-3 — `[?]` status on judgement files.** Two hits are `.judgement.md`
companions with no Status header, displayed as `[?]`. Either resolve
status from the parent FR or exclude judgement companions from the hit
list (their parent FR will match anyway when relevant) — `[?]` spends
the reader's attention on a non-answer.

**U-4 — what worked.** Cross-project corpus (fired correctly inside
`projects/ninchat_voice/`); five-line format is skimmable in flow;
status tags triage at a glance; the Scripture cite makes the required
action unambiguous. The human loop worked end-to-end: the user saw the
warning, asked for this review, and NC-393's disposition was added
retroactively — the hook caught a real omission on its first firing,
just via the wrong reader.
