# Feature Request: FR-738 Prior-Art Disposition Gate — the floor under the hook

**Priority:** MEDIUM
**Type:** Enhancement (enforcement infrastructure)
**Status:** Judged
**Effort:** 0.5 day
**Requested:** 2026-07-16
**Judged:** 2026-07-16 — scope frozen; the gate's own blind spot found before enforce: the motivating incident lives in a repo this gate never sees
**Parent:** FR-737 (field review U-1..U-4, first firing 2026-07-16)
**Spawned by:** FR-737's first field firing (NC-393, ninchat_voice): the
hook emitted `feedback`, the audit log recorded it, the **human** saw the
warning — and the authoring agent's tool result carried nothing. NC-393
was filed, committed, and pushed with no disposition: the exact failure
mode the hook exists to prevent, performed under its nose. Emission is
not reception; PostToolUse delivery to the agent surface is unverified.
Diary: `docs/diary/2026-07-16-emission-is-not-reception.md`.

**Prior art:** FR-737 (parent — this FR implements its U-1 backstop,
pre-named there as "the natural F7 follow-up candidate"); FR-077
(changelog commit enforcement — the precedent for advisory-then-block
layering at pre-commit); FR-070 (the original resurrection both FRs
exist to prevent). Hook hits FR-590/603/609/734 are incidental
body-prose matches on `prior`/`disposition`/`gate` — the exact U-2
noise class this FR fixes, demonstrated live on its own creation.
Disposition: extends the parent's mechanism to the boundary its field
review identified; no rejected FR touches this territory.

## Summary

Three fixes from the U-1..U-3 field review, one scope:

1. **U-1 (the floor):** re-run `prior_art.py` at **pre-commit** for
   newly added FR files; **fail the commit** when hits exist and the FR
   lacks a `**Prior art:**` disposition line. The check moves to a
   boundary that cannot be unseen (`enforcement_at_merge_boundary`).
2. **U-2 (ranking):** weight title/Summary-section matches above stray
   body-prose mentions; break same-noun ties by match count.
3. **U-3 (display):** `.judgement.md` companions resolve status from
   their parent FR or are excluded from candidates (the parent matches
   anyway when relevant) — `[?]` spends attention on a non-answer.

The PostToolUse hook stays as-is: fast advisory *when* the channel
works; pre-commit is the floor *whether or not* it does.

## Problem

The disposition requirement is currently enforced only by luck: the
Scripture obligation binds the judge, but the retrieval that makes the
obligation actionable travels a channel that demonstrably dropped its
first real payload. A gate that depends on an unverified delivery
channel is `detection_without_enforcement` wearing a hook costume.
Secondary: the first firing showed signal ranked 3/4 (title-relevance
buried under body-prose incidence) and `[?]` status tags on judgement
companions — both cheap, both evidence-backed.

## Proposed Solution

### 1. Pre-commit gate (U-1)

New pre-commit hook entry (local `.pre-commit-config.yaml`, script
`.github/hooks/scripts/checks/prior_art_gate.sh` or python entry):

- Scope: files **added** in the index under `feature-requests/*.md`
  (`git diff --cached --diff-filter=A --name-only`) — the same
  new-file-only semantics as the parent, at the commit boundary.
- For each: run `prior_art.py`. If it emits hits AND the staged file
  contains no `**Prior art:**` line → **fail** with the hit block and
  the required line format. Hits + disposition line → pass. No hits →
  pass (the A1 floor already guarantees silence is meaningful).
- The disposition line is free-form after the marker — the gate checks
  presence of the marker in a file that provably saw its hits; substance
  stays with the judge (Scripture obligation unchanged). A 1-byte
  disposition is `gate_checks_shape_not_substance` — accepted
  consciously: the gate's job is to make *unseen* impossible, not to
  grade the seeing.

### 2. Ranking refinement (U-2)

In `prior_art.py`: a match in the filename, H1 title line, or
`## Summary` section counts with weight 2; body-prose matches weight 1.
Score becomes Σ weight(noun,file)/freq(noun). Same-score ties break by
total match count, then name. The A1 floor and F3 self-exclusion are
untouched.

### 3. Judgement-companion status (U-3)

`read_status`: for `*.judgement.md`, read the parent FR's status
(`<name minus .judgement>.md`); if no parent, exclude the file from
candidates entirely.

### Out of scope (purge list)

- Repairing PostToolUse delivery to the agent surface (own
  investigation if it recurs; the floor makes it non-urgent — boundary
  relocation over channel repair).
- Semantic similarity, body/title noun *extraction* (F4 stands: nouns
  come from the filename).
- Blocking semantics in the PostToolUse hook itself.
- Plan-doc (`docs/plan-*.md`) triggers — still one strike
  (`two_strike_split`).

## Acceptance Criteria

- [ ] AC-01 RED — gate tests: staged new FR with hits and no
      `**Prior art:**` line fails with the hit block; same file with
      the line passes; staged new FR with no hits passes silently;
      modified (not added) FR never gates.
- [ ] AC-02 RED — ranking: a title-line match outranks a body-prose
      match of the same noun; same-noun tie breaks by match count.
      Replay the NC-393 fixture shape: the title-relevant hit ranks
      first.
- [ ] AC-03 RED — status: a `.judgement.md` companion shows the parent
      FR's status; an orphan judgement file is not a candidate.
- [ ] AC-04 — the FR-737 AC-02 counterfactual still passes (FR-070 in
      top 5 with `[REJECTED]`) — ranking change must not lose the
      motivating witness.
- [ ] AC-05 — pre-commit config entry; hooks README updated (advisory
      vs floor layering documented); changelog fragment; diary. This FR
      itself carries a `**Prior art:**` line — the gate's own format,
      eaten as dogfood.

## Alternatives Considered

- **Fix the PostToolUse delivery channel instead:** the right repair
  *eventually*, but the gate must not wait on an investigation into a
  surface we don't control; the floor works regardless of the channel's
  health.
- **CI-only gate (no pre-commit):** catches it later and in a context
  where the author may be gone; pre-commit is the cheapest boundary
  that cannot be unseen. CI can mirror it later if bypass becomes a
  pattern.
- **Require dispositions for ALL FR edits:** re-nags on every status
  fold; new-file-only matches the parent's judged trigger semantics.

## Related

- FR-737 (parent; U-1..U-4 field review in its Usage Comments section)
- `.github/hooks/scripts/checks/prior_art.py`, `.pre-commit-config.yaml`
- `docs/diary/diary-2026-07-16-emission-is-not-reception.md`

## Judgement (2026-07-16)

**Verdict: APPROVED — with 5 findings.** The sharpest one is the gate's
own `workspace_is_not_boundary` violation, caught by checking where the
motivating incident actually lives.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **Nested-repo blind spot**: NC-393 — the incident this FR exists to prevent — was committed in `projects/ninchat_voice`, a SEPARATE git repo with its own `.pre-commit-config.yaml`. A gate in yamlgraph's config never sees those commits. The floor, as proposed, does not cover its own origin story — compliance theatre relative to the motivating incident (`workspace_is_not_boundary`: the editor shows one tree; the commit boundaries are two) | Scope stays yamlgraph-repo (one concern, one repo, one commit stream). **Binding follow-up at enforce:** a mirror entry in ninchat's own pre-commit config (it can invoke the yamlgraph script by relative path — verified: `../..` resolves from the nested repo) filed as an NC-side FR; FR-738's completion note must state the boundary honestly. The PostToolUse advisory already covers both repos (session-scoped, not repo-scoped) — the asymmetry is the finding |
| F2 | The gate must judge what is being COMMITTED, not what is on disk — an author can edit after `git add` | Read the staged blob (`git show :0:path`) for both the hit check input and the `**Prior art:**` marker detection. One test witnesses the divergence case (staged lacks marker, working tree has it → FAIL) |
| F3 | U-2's weight rule needs a mechanical definition | Weight 2 iff the noun matches the candidate's **filename**, **first H1 line**, or **`## Summary` section text**; else 1. Corpus `freq` stays match-anywhere (frequency measures commonness; weight measures placement). Score = Σ weight/freq; ties by total match count, then name. AC-04 prediction recorded: FR-070 *improves* (filename match → weight 2) — if it degrades instead, the implementation misread this pin |
| F4 | The gate is skippable via `SKIP=<hook-id>` like every local hook | Accepted — consistent with daily repo practice (`SKIP=pytest`); `automation_inherits_doctrine` forbids `--no-verify`, not the named-skip escape. CI mirror stays deferred per Alternatives until bypass becomes a pattern; hook logs are the audit trail. No new denial infrastructure |
| F5 | U-3 offered two mechanisms ("resolve from parent OR exclude") — pick one | **Resolve from parent** when the parent FR exists (keeps signal, fixes `[?]`); exclude only orphan judgement files. Pinned |

**Scope frozen.** Purge list stands (no channel repair, no plan-doc
triggers, no CI gate yet, no semantic search). Enforce order: AC-01/02/03
RED (gate + ranking + status tests, staged-blob divergence case included)
→ GREEN → AC-04 counterfactual re-run → pre-commit entry + README →
NC-side mirror FR filed → paperwork. The FR's own `**Prior art:**` line
is the format fixture.
