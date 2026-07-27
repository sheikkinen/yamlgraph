# The skill became the law: process weight selected by affordance, not by risk

**Date:** 2026-07-27
**Context:** Operator observation after the FR-759–762 arc: since the
`review-pr` skill was added, agents automatically switched to git
worktrees, PRs, and the full review pipeline for *everything* — while
direct bugfixes to main were 10x faster. Both datapoints are from this
week: FR-760, a one-line `pyproject.toml` dependency declaration, took
4 review rounds, force-pushes, and a board-corruption battle across a
day. The `docs(otel)` fix and the FR-763 proposal went direct to main,
gated by the same full-pytest pre-commit hook, in minutes each.

## What actually happened

No doctrine change mandated PRs for all work. The repo's own hooks say
the opposite — branch creation in the main worktree is *blocked* with
"Single-developer workflow: commit to main." What changed was the
existence of an artifact: a skill describing how to review PRs. Agents
read the skill's presence as a norm. An available rite became a
mandatory one — nobody decided this; it emerged from pattern-matching
on "what tools exist" rather than "what does this change risk."

This is `does_the_tool_fit_or_merely_exist` inverted: not an unused
generic affordance, but an *over-used* one. The skill was written for
the plan-judge-enforce-review pipeline's terminal gate; agent default-
mode compliance generalized it to "how changes are made now." The
instruction boundary strikes again — a skill description enters the
context with the same typographical authority as the Scripture, and
the model cannot tell a capability from a commandment without an
explicit routing rule.

## The damning number

From the sixteen-not-approveds forensic: **~30% of all blocking review
findings were caused by the heavy process itself** — worktree
contamination swept into diffs, the fr-board `repo` column corrupted by
the worktree's directory name, generator stdout committed from the
wrong context, stacked-PR rebase churn after squash merges rewrote
SHAs. Direct-to-main has zero exposure to every one of those defect
classes. The pipeline manufactured a third of its own workload, then
charged the enforcer for it, one round-trip at a time.

Where the process earned its cost: FR-761/762's scanner semantics.
Those findings (try/except bypass, name-only pending gaps, dotted
namespaces) were real, adversarial-surface defects in *enforcement
infrastructure* — exactly the category the review doctrine names as
requiring hostile review. The review graph paid for itself there and
nowhere else.

## The heuristic

**Process weight must be selected by change risk, not by artifact
existence.** A concrete routing rule this repo already half-encodes:

- **Direct to main** (pre-commit full-pytest gate is the reviewer):
  docs, diary entries, FR proposals, generated-artifact regeneration,
  single-file bugfixes carrying their condemning test.
- **Worktree + PR + review graph**: enforcement infrastructure (CI,
  hooks, scanners, gates), core semantics (executor, graph_loader,
  state), multi-file features under a judged FR — the surfaces where
  the reviewer's adversarial stance has positive expected value.

The dividing line is the same one the Scripture already draws for
agent output: *is this an adversarial-input surface?* If yes, review.
If no, the hook suite — which runs the full test suite on every
commit — already provides the witness. FR-760 (one dependency line)
was on the wrong side of the line for a day.

**Corollary for skill authors:** every skill that describes a heavy
process must state its own anti-scope — the changes it must NOT be
used for — or agents will generalize it to everything. A skill without
an anti-scope is a behavioral attractor with no escape velocity.

## Seed

Can the pre-command hook that already blocks branch creation in the
main worktree be extended into a *router* — classifying a pending
change (paths touched × diff size × enforcement-surface contact) and
emitting the required process tier, so the direct-vs-pipeline decision
is mechanical repo policy instead of per-agent vibes?
