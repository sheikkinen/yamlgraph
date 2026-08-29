# Judgement: FR-896 Research Route Precedent Traceability — Committed-State Grounding Over Brief Echo

**Prior art:** the sole hook hit is FR-896 itself (the FR under judgement — self-reference, dispositioned by this verdict); substantive prior art (FR-890 route, FR-893 echo witness, FR-598/727/730 boundary cures, FR-737 disposition rule) is dispositioned in the "What is sound" section below.

**Verdict:** APPROVED WITH REVISIONS — the boundary-hardening direction is sound, but authority activates only after the FR separates invalid precedent from brief echo, removes the class-count/convergence contradiction, narrows the provenance claim, and pins governed graph/prompt edits to the authoring route.

**Reviewed against:** `feature-requests/FR-896-research-route-precedent-traceability.md`; `feature-requests/FR-896.research.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`; `feature-requests/FR-893-diary-trap-census.md`; `feature-requests/FR-893.research.md`; `feature-requests/FR-893-diary-trap-census.judgement.md`; `feature-requests/FR-598-l7-affect-throughline-kill-the-novel.md`; `feature-requests/FR-727-icpc2-process-discipline-combined-codes.md`; `feature-requests/FR-730-icpc2-chapter-inflation-discipline.md`; `feature-requests/FR-737-graveyard-hook-prior-art-on-fr-creation.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/feature-request/SKILL.md`; `feature-requests/TEMPLATE.md`. `tmp/research-echo-run.log` is cited by the FR but was not consumed because the judge input-closure rule permits only committed artifacts (`.github/skills/judge-fr/doctrine.md:18-24`); the committed research record was consumed instead.

## What is sound

The problem is real and within the activated FR-890 research-evidence regime. FR-890 created the route to produce committed alternatives with precedent citations, disagreement, and `is_this_a_graph` answers before plan authority (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:31-39`, `:123-145`), and the local judge doctrine now requires a committed research record with genuine solution classes, precedent lines, disagreement preserved, and an `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:118-130`). FR-896 carries that record (`feature-requests/FR-896-research-route-precedent-traceability.md:8-13`), and the record preserves five persona rows, precedents, and graph answers (`feature-requests/FR-896.research.md:11-17`).

The evidence identifies a real boundary defect rather than a style preference. FR-896 shows that personas currently receive only the author's brief plus limited graph-shape context, so convergence can be an echo of seeded brief language rather than independent discovery (`feature-requests/FR-896-research-route-precedent-traceability.md:17-28`). The committed research record records the live failure: four personas converged on one boundary rule while the class gate counted five distinct classes, and the os-infra row explicitly admitted its candidate was already a committed requirement from the brief (`feature-requests/FR-896.research.md:1`, `:13`). FR-893 is the earlier witness: its research row echoed the problem framing and still satisfied the then-current gate (`feature-requests/FR-893.research.md:13-17`), and its judgement counted the research record as substantive under that old contract (`feature-requests/FR-893-diary-trap-census.judgement.md:11-15`).

The architecture direction is aligned: normalize at the boundary, then let the Judge assess substance. FR-890's implementation already uses a deterministic stdlib preflight and schema checker before trusting a research artifact (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:239-243`) and fail-closed librarian checks for error strings and missing URLs (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:284-287`). FR-896's reducer-level reconciliation follows the Scripture's `two_strike_split` rule to treat model output as a claim reconciled against source of truth at the boundary (`.github/copilot-instructions.md:115-117`) and the `gate_checks_shape_not_substance` warning against URL-shaped compliance with no cross-reference validation (`.github/copilot-instructions.md:88`).

The prior art is dispositioned enough to proceed after revision. FR-727 supplies the demote-never-drop precedent for taxonomy junk drawers (`feature-requests/FR-727-icpc2-process-discipline-combined-codes.md:35-44`, `:86-90`); FR-730 supplies the "gate the defect class, do not worship aggregate class counts" precedent (`feature-requests/FR-730-icpc2-chapter-inflation-discipline.md:59-65`); FR-598 supplies the raw-output-first and prose-bloat lineage (`feature-requests/FR-598-l7-affect-throughline-kill-the-novel.md:46-52`, `:100-110`); and FR-737 supplies the rule that surfaced prior art must be dispositioned before authority (`feature-requests/FR-737-graveyard-hook-prior-art-on-fr-creation.md:86-91`). FR-896's Alternatives section folds or rejects each research-row direction rather than merely listing it (`feature-requests/FR-896-research-route-precedent-traceability.md:225-235`).

Strategic classification: **contrib/process-route hardening**, not a new framework primitive. The FR has a broad recurring consumer class -- every future FR author using `scripts/research.sh` -- but it hardens the existing FR-890 route rather than adding a general framework abstraction. The multiple surfaces are one concern, not a SPLIT: they all protect the same research-record trust boundary before the artifact is written (`feature-requests/FR-896-research-route-precedent-traceability.md:93-168`).

## Required revisions

### R-1: Separate invalid precedent from brief echo

Replace the AC-02 rule that demotes a nonexistent FR/CAP/path to `brief-echo` (`feature-requests/FR-896-research-route-precedent-traceability.md:174-176`). A missing or unverifiable identifier is not evidence that the row echoes the brief; it is an invalid precedent claim. Fold this rule mechanically:

- A non-librarian row with an existing committed identifier (`FR-\d+`, `CAP-\d+`, repo-relative path, or Scripture trap/cure key) passes precedent validation.
- A non-librarian row with no committed identifier and an explicit `brief-echo` marker is retained, visibly flagged, and excluded from class/convergence scoring.
- A non-librarian row that names a nonexistent committed identifier, malformed path, or nonexistent Scripture key fails artifact verification with a named violation. It must not be silently reclassified as echo.

This revision preserves the FR's own ideal that every precedent cell is either independently traceable or visibly echo (`feature-requests/FR-896-research-route-precedent-traceability.md:80-91`) and keeps "demote-never-drop" for true echo rows only (`feature-requests/FR-896-research-route-precedent-traceability.md:108-111`).

### R-2: Replace the class gate with a convergence-safe gate

Remove the proposed `>= 3 distinct classes among non-echo rows` gate or rewrite it so a genuine same-class convergence cannot fail the artifact. The current text contradicts itself: it says the old 4-6 class gate punishes convergence (`feature-requests/FR-896-research-route-precedent-traceability.md:54-61`) and promises the replacement is "never failed for converging" (`feature-requests/FR-896-research-route-precedent-traceability.md:136-138`), but a four-row convergence on one closed enum class can still fail a `>= 3 distinct classes` requirement.

Fold this as: the reducer validates `solution_class` against the closed enum, annotates repeated classes as `convergent xN`, and gates on at least three non-echo traceable findings plus preserved dissent/duplicate/external rows where present. Distinct-class count may be reported as advisory context for the Judge, but it must not be a blocking artifact gate. Add fixtures proving (a) three same-class non-echo rows pass and are annotated, (b) cosmetic relabeling outside the enum fails Pydantic validation, and (c) class diversity is reported without overwriting disagreement.

### R-3: Narrow the provenance claim to integrity unless a trusted source is added

Revise the Value Statement and run-provenance section so the committed `feature-requests/research-runs.jsonl` stamp is not presented as proof that an actual `scripts/research.sh` run occurred. The proposed log is committed by the same actor who commits the research record (`feature-requests/FR-896-research-route-precedent-traceability.md:159-168`), so it can prove internal consistency -- brief hash, artifact hash, graph path, UTC, and code git SHA match the committed artifacts -- but it cannot mechanically distinguish a fabricated-but-self-consistent record from a real run without an external trusted trace, signature, or equivalent authority.

Fold this as the smaller claim: the verifier distinguishes an unbacked or internally inconsistent promoted record from a record whose header, table body, committed brief, and `research-runs.jsonl` line recompute to the same hashes. Add `code_git_sha` to the log line, matching the repo's `artifact_carries_code_identity` seed (`.github/copilot-instructions.md:171`), and remove or qualify the stronger "mechanically distinguishable from a fabricated one" claim (`feature-requests/FR-896-research-route-precedent-traceability.md:32-35`, `:74-78`).

### R-4: Pin governed graph and prompt edits to the authoring route

Add a deliverable and acceptance criterion requiring any material changes to `examples/demos/research-route/**/graph.yaml` or `prompts/*.yaml` to be produced through `scripts/author.sh` and verified by `tmp/draft-authoring-report.md`. FR-896 changes persona inputs, prompt/schema constraints, the librarian role, graph-shape collection, and smoke behavior (`feature-requests/FR-896-research-route-precedent-traceability.md:117-151`, `:198-207`), which likely touches governed graph/prompt artifacts. Repo doctrine makes the artifact class -- not task phrasing -- the trigger, and forbids unsentineled manual graph/prompt writes (`.github/copilot-instructions.md:15`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/research_preflight.py` artifact verification: shared librarian predicate, URL/tool-result reconciliation, precedent validation, echo handling, closed enum checks, convergence annotation, and field-length rejection |
| D-2 | Research-route reducer/schema surfaces that define `PersonaFinding`, `solution_class`, `verdict`, `rationale`, max field lengths, and non-echo/convergence gate semantics |
| D-3 | Research-route persona supply surfaces: deterministic committed-context assembler, CAP one-liners, `ARCHITECTURE.md` headings, Scripture trap/cure names, and widened graph-shape inventory for `examples/demos/`, `graphs/`, and `.chaplain/graphs/` |
| D-4 | Research-route librarian prompt/schema surfaces that pin the librarian to external precedent reporting, not repo-local proposal generation |
| D-5 | `scripts/research.sh` provenance-integrity stamp and committed `feature-requests/research-runs.jsonl` verifier support |
| D-6 | Regression fixtures/tests for librarian URL reconciliation, invalid precedent failure, true echo demotion, convergence-safe gate behavior, max-length rejection, shared `web-librarian` predicate behavior, provenance recomputation, and self-referential rerun evidence |
| D-7 | FR-896 implementation-status update, changelog fragment, and diary reflection |

Not authorized: any judge-doctrine edit; any CI, pre-commit, or hook denial gate; any new judge, author, or review invocation path; fuzzy/semantic echo detection; multi-citation librarian expansion; persona seat changes; auto-running research on FR creation; revival of `.chaplain/` runtime behavior; deleting FR-890 fixtures without replacement witnesses; treating `tmp/` logs as judge evidence; or manually editing governed graph/prompt artifacts outside the authoring route.

## Revised acceptance criteria

- [ ] AC-01: Reducer rejects a librarian row whose URL is absent from `librarian_tool_results`; fixture witnesses both present and absent URL cases.
- [ ] AC-02: Reducer and artifact verifier use one shared librarian predicate; a `web-librarian`-labeled fixture row is treated identically by both.
- [ ] AC-03: Non-librarian precedent validation distinguishes three cases: existing committed identifier passes; explicit brief echo is retained as `verdict: echo` and excluded from scoring; nonexistent or malformed committed identifiers fail artifact verification with a named violation.
- [ ] AC-04: Echo rows remain in the artifact, visibly flagged, and do not count toward non-echo/convergence gate metrics.
- [ ] AC-05: All five personas receive a deterministic, bounded, author-independent committed-context block assembled without an LLM; tests witness CAP one-liners, `ARCHITECTURE.md` headings, and Scripture trap/cure names present in persona input, and `collect_graph_shapes` covers `examples/demos/`, `graphs/`, and `.chaplain/graphs/`.
- [ ] AC-06: `solution_class` and `verdict` are closed enums; free-text values fail Pydantic validation; only the reducer can set `verdict: echo`; repeated classes are annotated `convergent xN`; a fixture with three same-class non-echo traceable findings passes the artifact gate.
- [ ] AC-07: Every finding field that can carry model-authored prose has `max_length=400` in the prompt schema and runtime `PersonaFinding`; an over-length fixture is rejected by the reducer with a named violation and is not truncated.
- [ ] AC-08: `scripts/research.sh` appends one JSON line to committed `feature-requests/research-runs.jsonl` with brief SHA-256, artifact/table-body SHA-256, code git SHA, UTC timestamp, and graph path; verifier recomputes hashes from the committed brief/table and distinguishes matching, missing, and mismatched records. Documentation says this proves provenance integrity, not unforgeable execution.
- [ ] AC-09: The librarian schema/prompt pin the role to external precedent reporting; the 2026-08-28 solution-shaped librarian output, replayed as a fixture, is rejected or reshaped into an external-method precedent row with bounded rationale.
- [ ] AC-10: The self-referential brief (`research-briefs/research-route-grounding-echo.md`) is rerun through the upgraded route; the resulting implementation record cites an artifact where the os-infra-style verbatim echo row is flagged `brief-echo` and the four-way same-class convergence is annotated as convergent rather than failed or cosmetically split.
- [ ] AC-11: `scripts/research_preflight.py --verify-artifact` implements the new gate semantics; existing FR-890 fixtures are updated, and none are deleted without replacement witnesses for the same behavior.
- [ ] AC-12: If graph or prompt artifacts are materially changed, the changes are produced through `scripts/author.sh`; `tmp/draft-authoring-report.md` records the governed artifacts, graph lint, smoke result, and any honest validation limitation.
- [ ] AC-13: Changelog fragment, FR implementation-status update, requirement-tagged tests where applicable, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-4 are folded into FR-896. | GATE |
| C-2 | Invalid or unverifiable committed identifiers must fail artifact verification; only true explicit brief-echo rows may be demoted and preserved. | GATE |
| C-3 | Distinct class count must not be a blocking gate that rejects same-class convergence; class diversity is advisory context after enum validation. | GATE |
| C-4 | Provenance checks may claim hash/integrity consistency only; do not claim unforgeable execution proof unless a trusted external source is added in a separately judged FR. | GATE |
| C-5 | Any governed graph/prompt edits must go through `scripts/author.sh`; if that route fails, repair the route rather than writing governed artifacts manually. | GATE |
| C-6 | Reducer, preflight, artifact verification, and provenance checks must be deterministic and LLM-free. | GATE |
| C-7 | `tmp/` logs may be operational diagnostics but must not be required judge evidence or committed provenance. | GATE |
| C-8 | Do not edit judge/review doctrine, hooks, CI, or PR policy under this FR. | GATE |

Authority granted: after the required revisions are folded into FR-896, the enforcer may harden the existing FR-890 research route's reducer, verifier, persona context supply, librarian role contract, field/schema constraints, convergence reporting, provenance-integrity stamp, fixtures, and documentation within the frozen scope above.
