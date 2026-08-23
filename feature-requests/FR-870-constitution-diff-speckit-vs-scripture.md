# Feature Request: Constitution Diff — What Does a State-of-the-Art Generator Rediscover of the Scripture?

**Priority:** LOW
**Type:** Enhancement (research experiment, docs deliverable)
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-08-23
**First consumer / first event:** the "Judged Fork of Spec-Driven Development"
essay (origin-story proposal 1, diary 2026-08-23) needs its concrete exhibit;
first event is the essay's claim "the incident-paid part of the law cannot be
generated" being written with evidence instead of assertion.

## Summary

Run GitHub Spec Kit's `/speckit.constitution` phase against this repository
and diff the generated constitution against the actual written law
(`.github/copilot-instructions.md`). Classify every clause of the Scripture
as REDISCOVERED (the generator produces an equivalent), GENERIC-MISSED
(standard practice the generator produces but we lack), or INCIDENT-PAID
(present only because a production failure graduated it — unreachable by
generation). Publish the classified diff as a docs artifact.

## Value Statement

The origin story's central differential claim — that the Scripture's value is
its incident-paid content, not its generic content — becomes a measured
exhibit instead of a rhetorical one.

## Problem

`docs/origin-story.md` ("The External Record", commit ebc1c5d6) claims two
organs missing from spec-driven state of the art: the independent judge and
incident-derived case law. The case-law claim is currently unfalsifiable
prose. If a fresh `/speckit.constitution` run over this codebase rediscovers
most of the Scripture, the claim is weakened and the essay (proposal 1) must
be softened; if it rediscovers only the generic layer (module size limits,
TDD, type hints) and none of the traps/cures/questions canon, the claim is
proven at the clause level. Either outcome is information; only running the
experiment produces it.

This is `does_the_platform_already_do_this` inverted: not "does the platform
already do what we built?" but "can the platform's generator reproduce what
we learned?"

## Ideal Result

A single committed document, `docs/constitution-diff.md`, containing (a) the
verbatim constitution Spec Kit generated for this repo, (b) a clause-level
classification table of the Scripture (REDISCOVERED / GENERIC-MISSED /
INCIDENT-PAID, with the graduating diary/FR cited for each INCIDENT-PAID
clause), and (c) a three-sentence conclusion stating the measured fraction —
ready to be cited by the essay and by `docs/origin-story.md` as the exhibit
for the case-law divergence.

## Proposed Solution

Minimal path back from the ideal:

1. **Sanitize** (R-1): the run happens in a scratch copy from which the
   answer key has been removed. If the generator can read the Scripture, the
   experiment measures leakage, not rediscovery.
   - **Deny-list** (removed before the run): `.github/copilot-instructions.md`,
     `.github/skills/`, `.github/hooks/`, `CLAUDE.md`, `AGENTS.md`,
     `feature-requests/`, `docs/diary/`, `docs/origin-story.md`,
     `docs/memento/`, `docs/confessions.md`, any prior
     `docs/constitution-diff.md`, `tmp/`, `*.judgement.md`.
   - **Allow-list** (the corpus): `yamlgraph/`, `tests/`, `examples/`,
     `scripts/`, `.github/workflows/`, `pyproject.toml`,
     `.pre-commit-config.yaml`, `.importlinter`, `README.md`,
     `ARCHITECTURE.md`, `reference/`, `capabilities/`.
   - **Declared borderline**: `.pre-commit-config.yaml`, `.importlinter`, and
     workflow gates are mechanized law — they stay in the corpus (they are
     what the law *produced*), and any rediscovery traceable to their text is
     flagged as enforcement-fingerprint rediscovery in the analysis.
   - `docs/constitution-diff.md` records the input manifest and the
     sanitation commands/log.
2. **Run** Spec Kit in the sanitized scratch worktree only
   (`one_session_one_repo`; scaffolding must not enter this repo), pinned
   and non-interactive (R-2):
   ```bash
   git worktree add /tmp/yg-speckit HEAD
   cd /tmp/yg-speckit && <apply deny-list removals, log them>
   uvx --from git+https://github.com/github/spec-kit.git@v1.0.0 \
     specify init --here --force --non-interactive --integration copilot
   # then run /speckit.constitution in an agent session with the neutral prompt:
   # "Derive the governing principles for this project from its codebase,
   #  tests, and CI configuration."
   ```
   Record Specify CLI version, Spec Kit commit SHA, model/provider, date,
   and the exact prompt.
3. **Capture** the generated `.specify/memory/constitution.md` verbatim into
   `docs/constitution-diff.md` (section a), with the provenance block.
4. **Manifest** (R-4): before classifying, build a source-unit manifest of
   the Scripture — included sections (10 Commandments, traps, cures,
   questions, generative methods, process rules, boundaries, Conventions,
   Sermon, Rite of Correction), excluded sections with a one-sentence reason
   each (e.g. seeds = backlog, not law; Agents' prayer = liturgy restating
   listed cures), stable unit IDs, total count, and a count reconciliation
   proving every included unit appears exactly once in the table.
5. **Classify** by hand (judgement work, not tooling work) into two
   reconciled inventories (R-3), with evidence standards (R-5):
   - **Scripture-unit table** — every included unit gets exactly one label:
     `REDISCOVERED` (must quote the equivalent generated clause),
     `SOURCE_ONLY_INCIDENT_PAID` (must cite the graduating diary entry, FR,
     or in-text witness), or `SOURCE_ONLY_UNTRACED_GENERIC` (no incident
     citation — never counted in the incident-paid numerator).
   - **Generated-only table** — every generated clause absent from the
     Scripture gets exactly one label: `GENERATOR_ONLY_GENERIC_MISSED`
     (worth a future proposal) or `GENERATOR_ONLY_REJECTED` (with reason).
6. **Conclude** with measured fractions (numerator, denominator, label
   family stated; source-side and generator-side rates kept separate) and
   ≤3 sentences stating whether the result strengthens, weakens, or
   invalidates the origin-story claim.
7. **Cleanup evidence** (R-6): include `git --no-pager diff --name-only`,
   `git worktree list`, and `git worktree prune --dry-run` outputs proving
   only authorized docs files changed and no scratch worktree remains.
8. **Cross-link**: one line added to `docs/origin-story.md` "External Record"
   pointing at the exhibit, claiming no more than the measured result.

Explicitly NOT in scope: no adoption of Spec Kit, no tooling, no script, no
automation of the classification, no re-running on other repos, no changes to
the Scripture itself (any GENERIC-MISSED clause worth adopting becomes its
own future proposal via the normal pipeline).

## Acceptance Criteria

As revised by the judgement (authoritative list in
`FR-870-constitution-diff-speckit-vs-scripture.judgement.md`):

- [x] AC-01: FR revised to fold R-1 through R-6 (this revision)
- [ ] AC-02: Spec Kit run occurs only in a sanitized scratch worktree, with
      the deny-listed doctrine/history inputs removed first
- [ ] AC-03: `docs/constitution-diff.md` records full provenance: date,
      operator/agent, model/provider, Spec Kit version/commit, init command,
      constitution prompt, generated path, sanitized input manifest
- [ ] AC-04: generated constitution included verbatim before any analysis
- [ ] AC-05: source-unit manifest with included/excluded sections, stable
      unit IDs, total count, count reconciliation
- [ ] AC-06: every included source unit appears exactly once with one
      exhaustive source-side label
- [ ] AC-07: every `REDISCOVERED` row quotes/cites the equivalent generated
      clause
- [ ] AC-08: every `SOURCE_ONLY_INCIDENT_PAID` row cites a graduating diary
      entry, FR, or source-text witness; uncited rows never count as
      incident-paid
- [ ] AC-09: every generated-only clause appears in a separate table with one
      exhaustive generator-side label
- [ ] AC-10: measured fractions state numerator, denominator, label family;
      source-side and generator-only rates separated
- [ ] AC-11: conclusion ≤3 sentences, explicitly strengthens/weakens/
      invalidates the origin-story claim
- [ ] AC-12: `docs/origin-story.md` External Record links the exhibit in one
      line, claiming no more than the measured result
- [ ] AC-13: zero Spec Kit scaffolding files (`.specify/`, `memory/`,
      `.speckit*`, integration command files) committed to the live repo
- [ ] AC-14: cleanup evidence included (diff --name-only, worktree list,
      prune --dry-run) proving only authorized files changed and no scratch
      worktree remains

No test-suite changes: the deliverable is a docs artifact; no production code
is touched (doc-only FRs carry no REQ tag — precedent: origin-story arc).

## Alternatives Considered

- **Cite Spec Kit's template constitution instead of running it**: cheaper,
  but measures the template, not what a generator derives from *this*
  codebase — the claim under test is about derivability, so the run is the
  experiment.
- **Automate the classification with an LLM judge**: rejected — the
  classification IS the judgement work, and memento FR-040's precedent
  (rejecting LLM-as-judge quality gates without verification) applies; a
  hand classification of ~60 units is under two hours.
- **Run against a foreign repo instead**: that is FR-866 ramp territory
  (governance transplant); this FR measures generation, not transplant. Kept
  disjoint deliberately.
- **Do nothing**: the essay ships with an unfalsifiable claim — exactly the
  hedging Commandment 6 forbids.

## Related

- `docs/origin-story.md` — "The External Record" (ebc1c5d6): the claim under
  test
- `docs/diary/diary-2026-08-23-identity-by-the-nearest-neighbors-missing-organ.md`
  — proposal 4 (this FR), proposal 1 (the consuming essay)
- [github/spec-kit](https://github.com/github/spec-kit) — `/speckit.constitution`,
  announced 2025-09-02, 1.0.0 2026-08-21
- `docs/memento/feature-requests/040-*` — precedent against unverified
  LLM-as-judge classification
- FR-866 (ramp) — adjacent but disjoint: transplant fidelity vs generation
  fidelity

## Judgement (2026-08-23)

**Verdict:** APPROVED WITH REVISIONS — full judgement in
[FR-870-constitution-diff-speckit-vs-scripture.judgement.md](FR-870-constitution-diff-speckit-vs-scripture.judgement.md)
(model gpt-5.5, via `scripts/judge.sh`, input closure honored).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Scratch copy contains the answer key — leakage, not rediscovery | Sanitized corpus with explicit deny/allow lists + input manifest (folded above) |
| R-2 | Invocation unpinned, wrong constitution path | Pin v1.0.0, `--here --force --non-interactive --integration copilot`, capture `.specify/memory/constitution.md` (folded) |
| R-3 | Three-label taxonomy mixes source-side and generator-only meanings | Two reconciled inventories with mutually exclusive, exhaustive labels (folded) |
| R-4 | "Every normative unit" uncountable — plausible table could omit families | Source-unit manifest with IDs, counts, reconciliation (folded) |
| R-5 | No evidence standard for REDISCOVERED; uncited units could inflate incident-paid | Quote/cite requirements per label; uncited units excluded from numerator (folded) |
| R-6 | Cleanup criteria not mechanically checkable | Concrete command outputs required as evidence (folded) |

**Purge list:** none — no code surface.

**Scope frozen:** D-1 revised FR (done), D-2 sanitized Spec Kit run, D-3
`docs/constitution-diff.md`, D-4 one-line origin-story cross-link, D-5 FR
status update. Not authorized: Scripture/doctrine/hooks/CI/runtime changes,
Spec Kit adoption, classifier automation, other repos, claims from
contaminated input. Gates C-1..C-7 per judgement file.

### Questions for the human (as options, or 'none')

None — the judgement raised no human questions; output advisory until
human-reviewed.
