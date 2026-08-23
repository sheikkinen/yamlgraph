# Feature Request: Constitution Diff — What Does a State-of-the-Art Generator Rediscover of the Scripture?

**Priority:** LOW
**Type:** Enhancement (research experiment, docs deliverable)
**Status:** Proposed
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

1. **Install and run** Spec Kit in an isolated scratch copy (never the live
   worktree — `one_session_one_repo`; Spec Kit writes `memory/`, `.specify/`
   scaffolding that must not enter this repo):
   ```bash
   git worktree add /tmp/yg-speckit HEAD
   cd /tmp/yg-speckit
   uvx --from git+https://github.com/github/spec-kit.git specify init --here
   # then run /speckit.constitution in an agent session with a neutral prompt:
   # "Derive the governing principles for this project from its codebase,
   #  tests, and CI configuration."
   ```
2. **Capture** the generated `memory/constitution.md` verbatim into
   `docs/constitution-diff.md` (section a). Record tool version, model, date.
3. **Classify** by hand (this is judgement work, not tooling work): walk the
   Scripture's normative units — the 10 Commandments, each trap, each cure,
   each question, each generative method, each process rule, each Convention
   — and tag each REDISCOVERED / INCIDENT-PAID; walk the generated
   constitution for clauses we lack and tag GENERIC-MISSED. INCIDENT-PAID
   requires a citation (diary entry or FR) proving the clause graduated from
   a failure.
4. **Conclude** with the fractions and one honest sentence about what the
   result does to the essay's claim.
5. **Cross-link**: one line added to `docs/origin-story.md` "External Record"
   pointing at the exhibit.

Explicitly NOT in scope: no adoption of Spec Kit, no tooling, no script, no
automation of the classification, no re-running on other repos, no changes to
the Scripture itself (any GENERIC-MISSED clause worth adopting becomes its
own future proposal via the normal pipeline).

## Acceptance Criteria

- [ ] `docs/constitution-diff.md` exists with sections (a) verbatim generated
      constitution + provenance (tool version, model, date, prompt used),
      (b) classification table covering every normative unit of the
      Scripture, (c) measured fractions and conclusion
- [ ] Every INCIDENT-PAID row cites the graduating diary entry or FR
- [ ] Zero Spec Kit scaffolding files (`memory/`, `.specify/`, `.speckit*`)
      committed to this repo (experiment ran in a scratch worktree)
- [ ] `docs/origin-story.md` External Record links the exhibit (one line)
- [ ] Scratch worktree removed after capture (`git worktree prune` clean)

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

## Judgement (date)

**Verdict:** _pending_
