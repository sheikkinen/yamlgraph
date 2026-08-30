# Judgement: FR-931 Upgrade the judge and review sole-route model pin to gpt-5.6-sol

**Verdict:** APPROVED WITH REVISIONS - authority activates only after R-1 is folded into the FR and this draft judgement receives the required human review for enforcement-infrastructure changes.

**Prior art:** the only filename hit is the parent FR itself; its prior-art record is dispositioned in the FR body and confirmed here — FR-758 / CAP-211 own the sole-route wrapper and adapter contract this FR edits, FR-266 owns the model resolution chain it relies on, and FR-928 holds the same literal as an in-flight invariant (C-5 below). No prior or REJECTED FR proposes changing the judge/review model pin.

**Reviewed against:** `feature-requests/FR-931-judge-review-model-pin-gpt56sol.md`; `feature-requests/FR-931.research.md`; `feature-requests/research-briefs/fr931-model-pin-brief.md`; `feature-requests/FR-900-evidence.md`; `docs/analysis-fr888-post-mortem-2026-08-25.md`; `docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md`; `capabilities/CAP-211-sole-route-judge-review.yaml`; `feature-requests/FR-928-cloud-judge-github-actions.md`; `feature-requests/FR-758-judge-review-traceability-reconstruction.md`; `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/review-pr/adapters/graph.yaml`; `scripts/judge.sh`; `scripts/review.sh`; `scripts/aggregate_changelog.py`; `.github/workflows/commitlint.yml`; `scripts/check_changelog_req.py`; `tests/unit/test_fr758_judge_review_wrappers.py`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The scope is clear and minimal: the FR asks for one literal model-pin edit in each of two adapter graphs, plus a witness test and recorded route evidence (`feature-requests/FR-931-judge-review-model-pin-gpt56sol.md:27-35`, `:88-101`). The current adapter surfaces match that claim: both copilot nodes define `cli_flags.model: gpt-5.5` in the single judge/review node (`.github/skills/judge-fr/adapters/graph.yaml:22-23`, `.github/skills/review-pr/adapters/graph.yaml:22-23`).

The problem is real enough for authority. CAP-211 identifies `scripts/judge.sh` and `scripts/review.sh` plus their adapter graphs as the sole operational routes and says completion is verified by artifact contract, never exit code (`capabilities/CAP-211-sole-route-judge-review.yaml:6-18`, `:20-35`). The diary citation substantiates the drift hazard: unpinned copilot nodes inherit ambient CLI defaults and shift cost without a diff (`docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md:60-65`). The cost claim is grounded in the committed price sheet: `gpt-5.6-sol` has default input/output prices 200/1000 and 272k max prompt tokens, while `gpt-5.5` is listed at 500/3000 (`feature-requests/FR-900-evidence.md:63-78`, `:118-120`).

The research gate is satisfied in substance. The FR points to a committed research record and brief (`feature-requests/FR-931-judge-review-model-pin-gpt56sol.md:13-16`); the brief states the governing constraints, including preserving sole routes, keeping the model in YAML, avoiding ambient defaults, and recording deliberate divergence (`feature-requests/research-briefs/fr931-model-pin-brief.md:51-75`). The promoted alternatives preserve disagreement and disposition five solution classes, including shared YAML, defaults relocation, availability gates, deletion, and modelpin replay (`feature-requests/FR-931.research.md:9-13`; `feature-requests/FR-931-judge-review-model-pin-gpt56sol.md:183-199`). The FR also dispositions adjacent prior art, including FR-758/CAP-211, FR-266, and FR-928 (`feature-requests/FR-931-judge-review-model-pin-gpt56sol.md:18-24`, `:208-217`).

The implementation approach aligns with existing architecture instead of inventing a new route. It keeps model selection in `cli_flags.model`, the highest-priority point in the existing resolution chain as stated by the FR (`feature-requests/FR-931-judge-review-model-pin-gpt56sol.md:191`), and preserves the wrapper contracts already implemented by `scripts/judge.sh` and `scripts/review.sh` (`scripts/judge.sh:45-62`, `scripts/review.sh:47-63`). It explicitly excludes the authoring adapter (`feature-requests/FR-931-judge-review-model-pin-gpt56sol.md:138-143`), avoiding an orthogonal third route.

Measurability and testability are mostly strong. AC-01/AC-02 define direct YAML assertions for presence, equality, and exact value of the pin (`feature-requests/FR-931-judge-review-model-pin-gpt56sol.md:148-154`); AC-04 constrains adapter diffs to one changed line each (`:158-159`); AC-06/AC-07 require real route artifacts and include substance checks, not just exit codes (`:162-171`). The test style is feasible because existing unit tests already use repository-root `Path` helpers and PyYAML parsing patterns (`tests/unit/test_fr758_judge_review_wrappers.py:13-20`; `scripts/aggregate_changelog.py:23-24`, `:63-85`).

Strategic classification: this is not a framework primitive. It is a narrow governance-configuration change on existing sole-route infrastructure, with a small regression witness to make that configuration deliberate. That is the correct classification for a two-adapter model pin.

## Required revisions

### R-1: Make the changelog fragment type mechanically valid

Replace AC-09's `type: chore (or feat)` wording with a valid changelog fragment type for this repository, preferably `type: feat`. The current criterion is internally unsafe because `scripts/aggregate_changelog.py` documents and enforces only `feat`, `fix`, and `removal` fragment types (`scripts/aggregate_changelog.py:12-14`, `:35-38`, `:73-80`), while AC-09 currently permits `chore` (`feature-requests/FR-931-judge-review-model-pin-gpt56sol.md:175-178`). A `chore` fragment would satisfy the FR text while failing changelog aggregation.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/unit/test_fr931_sole_route_model_pin.py` |
| D-2 | `.github/skills/judge-fr/adapters/graph.yaml` |
| D-3 | `.github/skills/review-pr/adapters/graph.yaml` |
| D-4 | `capabilities/CAP-211-sole-route-judge-review.yaml` |
| D-5 | one `changelog/unreleased/*.md` fragment |
| D-6 | `feature-requests/FR-931-judge-review-model-pin-gpt56sol.md` implementation record |
| D-7 | one `docs/diary/diary-*.md` reflection |
| D-8 | local evidence artifacts/log paths from the required judge and review route runs, quoted in D-6 |

Not authorized: changes to `.github/skills/graph-authoring/adapters/graph.yaml`; changes to judge/review doctrine or prompts; changes to `scripts/judge.sh` or `scripts/review.sh`; changes to model-resolution semantics; shared model-pin config, YAML anchors/includes, `defaults.model` relocation, availability probe nodes, or modelpin integration; hook/CI enforcement changes; auto-folding, auto-committing, auto-commenting, or merging behavior.

## Revised acceptance criteria

- [ ] AC-01: `tests/unit/test_fr931_sole_route_model_pin.py` exists, is tagged `@pytest.mark.req("REQ-YG-632")`, and asserts that both `.github/skills/judge-fr/adapters/graph.yaml` and `.github/skills/review-pr/adapters/graph.yaml` define a non-empty `cli_flags.model` on their single copilot node.
- [ ] AC-02: the same test asserts both pins are equal to each other and equal to `gpt-5.6-sol`.
- [ ] AC-03: git history shows the test committed RED, failing against `gpt-5.5`, before the adapter edit that turns it GREEN.
- [ ] AC-04: the two adapter files differ from `main` in exactly one line each; `git diff --numstat main -- .github/skills/judge-fr/adapters/graph.yaml .github/skills/review-pr/adapters/graph.yaml` reports `1 1` for each file.
- [ ] AC-05: both adapter graphs lint cleanly under the existing graph linter after the pin change.
- [ ] AC-06: a real `scripts/judge.sh tests/fixtures/fr890/FR-998-fixture-missing-research.md` run under the new pin produces a non-empty `tmp/draft-judgement.md` containing a `**Verdict:**` line, and the verdict withholds authority because the fixture lacks the `**Research:**` field; the log path and verdict line are quoted in the FR implementation record.
- [ ] AC-07: a real `scripts/review.sh <this-pr> feature-requests/FR-931-judge-review-model-pin-gpt56sol.md` run under the new pin produces `tmp/draft-review.md` whose line one is `**Merge verdict:**`; the log path and verdict line are quoted in the FR implementation record.
- [ ] AC-08: `capabilities/CAP-211-sole-route-judge-review.yaml` gains `REQ-YG-632`, naming both adapter graphs and `tests/unit/test_fr931_sole_route_model_pin.py`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-09: one changelog fragment is added under `changelog/unreleased/` with valid front matter `type: feat`, `scope: judge`, and `req: REQ-YG-632`, recording the pin change and its price delta.
- [ ] AC-10: `.github/skills/graph-authoring/adapters/graph.yaml` remains unchanged by this FR.
- [ ] AC-11: a diary reflection is committed under `docs/diary/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Human review of this draft judgement is required before implementation, because the change edits judge/review enforcement infrastructure and the judge doctrine demands human review as a gate for that class of change (`.github/skills/judge-fr/doctrine.md:98-100`). | GATE |
| C-2 | R-1 must be folded into the FR before implementation begins; otherwise AC-09 authorizes an artifact that the changelog parser rejects. | GATE |
| C-3 | The enforcer must preserve the existing sole-route wrappers and artifact contracts; if a real route run fails, do not weaken the contract or replace artifact verification with exit-code success. Return to judgement with the failed artifact/log evidence. | GATE |
| C-4 | The enforcer must not change the authoring adapter, model-resolution chain, judge/review doctrine, prompts, hooks, CI workflows, or wrapper behavior under this FR. Any need to touch those surfaces is a new FR or a SPLIT return. | GATE |
| C-5 | If FR-928 or another in-flight change has modified the same adapter invariant before enforcement, rebase and preserve the invariant as "both routes read the same current adapter pin"; do not merge two literal-pin stories that contradict each other. | GATE |

Authority granted: after R-1 is folded and human review accepts this draft, implement only the two judge/review adapter pin edits, the explicit-pin witness test, the CAP requirement, the valid changelog fragment, the FR implementation evidence, and the diary reflection described above.
