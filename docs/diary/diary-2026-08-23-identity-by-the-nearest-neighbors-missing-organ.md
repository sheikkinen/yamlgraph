# 2026-08-23 — Identity by the Nearest Neighbor's Missing Organ

## What happened

The origin-story arc closed with an external record (`ebc1c5d6`): every claim
about vibe coding, spec-driven development, and agent loops in
`docs/origin-story.md` is now anchored to a dated primary source. The research
pass upgraded the earlier reflection
(`diary-2026-08-23-the-spike-was-vibe-coding-before-the-word-reached-us.md`)
from narrative to checkable assertion — the same move the repo itself made in
January when FRs grew acceptance criteria. History without citations is a
vibe; the historian owes the same discipline the doctrine demands of code.

## Traps encountered

- **citation_from_memory**: The Kiro Wikipedia page 404'd twice. The
  continuation-bias reflex was to cite the launch date from training memory —
  a `plausible_wrong_answer` at the citation boundary, where the shape check
  (a URL, a date) passes trivially and the substance check is everything.
  Cure applied: hedge to "mid-2025" and cite the primary vendor site only.
  General form: *a reference fetched and read is evidence; a reference
  recalled is a hypothesis wearing a bibliography costume.* This is
  `read_raw_output_first` at the historiography boundary.
- **research_as_inventory**, avoided this time: the fetches produced link
  lists; the deliverable was the *differential* — what each neighbor has that
  we lack, and lacks that we have. The section earned its place only when it
  stated divergences, not descriptions.

## The insight that names the entry

The sharpest statement of what this system *is* came not from reading its own
code but from locating its nearest external twins and naming their missing
organ:

- **Spec Kit** has the whole artifact pipeline — but no independent judge
  (the author's agent approves its own artifacts) and no case law (rejected
  specs bind nothing).
- **Ralph** has the loop, the signs, even self-improving AGENT.md — but runs
  on faith ("believe in eventual consistency") instead of verdicts, and is
  greenfield-only by its author's own admission.

*Ralph writes signs; the Scripture writes signs and hires police.* Identity
is cheapest to articulate as the diff against the nearest neighbor — the
same reason `git diff` beats re-reading both files. Heuristic: when asked
"what is this system?", find the closest public analogue first and answer
with the delta.

## Proposals — where to go next

Ranked; each names its first consumer and firing trigger
(`would_you_use_this`), per the canon.

1. **Publish the differential** — "The Judged Fork of Spec-Driven
   Development": the origin story + external record is a complete,
   citation-anchored essay arguing the two organs SDD state-of-the-art lacks
   (independent judge, rejections as case law). First consumer: the external
   audience for the "build for agents first" thesis; the operator's public
   channel. Trigger: material complete as of `ebc1c5d6`. Route: the existing
   ebook pipeline (`examples/` ebook chapter graphs) — dogfooding, and a
   direct answer to `first_person_tool_horizon`.
2. **Governance-fidelity benchmark** (already seeded; FR-866 ramp emits
   half): METR measured *speed* and found illusion; nobody measures whether a
   governance doctrine *survives transplant* into a foreign repo. Metric:
   fraction of gates that hold, verdicts that render, and traps that fire
   after the ramp installs the doctrine elsewhere. First consumer: ramp
   pipeline verdicts. Trigger: FR-866 lands. This is the evidence layer for
   proposal 1 — claims about divergence become measurements.
3. **Memento precedent indexing**: the 39 recovered pre-doctrine FRs
   (`docs/memento/feature-requests/`) contain live precedent — FR-011's
   web-UI rejection, FR-040's rejection of LLM-as-judge quality gates —
   invisible to the prior-art gate because they live outside
   `feature-requests/`. Index them into the prior-art corpus so a proposal
   re-entering rejected territory dies by the original rationale (FR-737
   doctrine). First consumer: the Judge, on the next FR touching web-UI or
   LLM-quality-gate territory. Trigger: submitted to `.chaplain/inbox/` this
   session.
4. **Cheap comparative experiment**: run Spec Kit's `/speckit.constitution`
   phase against a Scripture-governed repo and diff the generated
   constitution against the actual one. One afternoon; produces the concrete
   exhibit for proposal 1 and a fitness check on our own written law
   (`does_the_platform_already_do_this`, inverted: does the platform's
   generator rediscover our law?).

Subtraction check (operator calibration): no retirement candidates from this
arc — history is additive by nature, and the external record supersedes no
internal artifact; the earlier diary entry remains the analysis the section
cites.

**Seed:** The external record dates every source; the internal record dates
every commit. When the governance-fidelity benchmark exists, the two records
can be joined: did our enforcement waves *lead* or *lag* the public incident
waves? A doctrine that consistently leads the ecosystem's published failures
is doing prediction, not reaction — and that would be the strongest public
claim of all. What table would prove it?
