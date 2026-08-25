# Judgement: FR-883 Block Concealed Refusal and Task Alteration

**Verdict:** APPROVED WITH REVISIONS - the defect class is real and the FR correctly reuses the FR-438/FR-439 reasoning sentinel, but authority activates only after the FR fixes the hook-timing overclaim, enumerates exact witnessed signatures with committed evidence, and makes the negative refusal tests mechanical.

**Prior art:** FR-438 introduced the reasoning sentinel; FR-439 renamed it. FR-883 extends that existing mechanism.

**Reviewed against:** FR-883 draft; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; FR-438; FR-439; committed hook registry, scanner, guard, and tests; `deviant-daily@ad77b10` FR-885; `deviant-daily@1df8254` FR-885 and judgement.

## What is sound

The problem is a real enforcement-infrastructure concern. Repo doctrine treats agent instruction and model behavior as an untrusted boundary, and FR-883 correctly identifies the harmful third path: neither direct refusal nor unchanged execution, but hidden refusal followed by substituted scope.

The chosen surface is architecturally aligned and minimal. FR-438 created a deterministic transcript scanner that arms a one-shot sentinel consumed by `pre-command-guard.sh`; FR-439 renamed it to the current neutral surface. Extending that registry is smaller than adding a hook, classifier, or sentinel format.

The FR also preserves an important distinction: a visible refusal is not the defect. Direct user-visible refusal phrases should not be added to the registry.

Strategic classification: enforcement-infrastructure primitive extension.

## Required revisions

### R-1: Align the boundary claim with actual hook timing

The committed architecture is PostToolUse scan -> sentinel -> later PreToolUse denial. State that this FR authorizes denial of the next tool call after the scan arms the sentinel. It does not guarantee zero first-tool spend.

### R-2: Add an evidence appendix with exact witnessed signatures

For every canonical pattern and variant, list exact matched string, family, source, evidence reference, and doctrine sentence. If the transcript cannot be committed, quote the exact witnessed strings in the FR appendix and mark them as authoritative evidence.

### R-3: Make tests derive directly from the signature table

Parameterize over every approved signature. Add binding negative tests for ordinary direct visible refusal and benign policy discussion. Preserve existing clean-thinking, session-isolation, and one-shot tests.

### R-4: Add the enforcement-infrastructure human-review gate

Because this modifies PreToolUse/PostToolUse enforcement infrastructure, the resulting diff requires human review before merge.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised FR evidence appendix: exact signature table with sources, family, variants, and sentinel doctrine. |
| D-2 | `.github/hooks/scripts/reasoning-patterns.json`: only exact approved patterns/variants from D-1. |
| D-3 | `.github/hooks/tests/test_reasoning_pattern_check.py`: positive tests for D-1, negative tests for direct visible refusal/policy discussion, existing one-shot coverage. |
| D-4 | `docs/diary/<date>-*.md`: incident reflection and heuristic. |
| D-5 | `changelog/unreleased/*.md`: bug-fix fragment. |

Not authorized: new hooks, hook events, LLM classifier, semantic task-drift detection, sentinel filename/schema changes, direct-refusal blocking, judge/review doctrine changes, deviant-daily changes, retroactive FR-885 rewriting, model/content policy decisions, or a guarantee that the first post-reasoning tool call is blocked.

## Revised acceptance criteria

- [ ] AC-01: Signature table lists every canonical pattern and variant with family, source, evidence, and doctrine.
- [ ] AC-02: Registry adds exactly approved entries and no ordinary direct visible refusal phrases.
- [ ] AC-03: Parameterized test proves every table row arms a sentinel with non-empty doctrine.
- [ ] AC-04: Existing guard denies once, deletes sentinel, and preserves session isolation.
- [ ] AC-05: Negative tests prove direct visible refusals and benign visible policy discussion do not arm.
- [ ] AC-06: Existing reasoning-pattern tests remain green.
- [ ] AC-07: FR states actual timing boundary.
- [ ] AC-08: Incident and heuristic recorded in diary.
- [ ] AC-09: Changelog fragment added.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority inactive until R-1 through R-4 are folded. | GATE |
| C-2 | Write failing tests before changing the registry. | GATE |
| C-3 | Hook timing must not expand under this FR. | GATE |
| C-4 | No classifier, semantic detector, new hook, or sentinel format change. | GATE |
| C-5 | Every phrase grounded in FR signature table. | GATE |
| C-6 | Human reviews final enforcement diff before merge. | GATE |

Authority granted after revisions are folded, within the frozen scope above.
