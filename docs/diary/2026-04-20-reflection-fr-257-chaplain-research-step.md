# Reflection: FR-257 Chaplain Research Step

**Date:** 2026-04-20
**FR:** FR-257
**Branch:** feat/fr-257-chaplain-research-step

## What Was Done

Inserted a Research node between Plan and Judge in `.chaplain/graphs/copilot/graph.yaml`. The research step searches the codebase for existing abstractions, checks the diary for precedent, counts usage evidence, and classifies the proposal (framework primitive / contrib / pattern documentation / reject). The research brief is appended to the FR draft before Judge evaluation. The Judge prompt was updated with Criterion 7: strategic classification. Prompt at `.chaplain/graphs/copilot/prompts/research.yaml`.

## Cognitive Trap: Judge Validates Execution, Not Intent

The Judge was evaluating FR plans for internal consistency and implementation clarity — but not asking "Is this the right abstraction for the framework?" An FR could pass the Judge (well-specified, clear acceptance criteria, feasible) while being strategically wrong (duplicates an existing pattern, belongs in contrib rather than core, or should be documentation rather than code).

The research step addresses the `unchallenged_premise` trap from the Knowledge Graph: "Judge validates execution, not intent → need Red Hat: 'Is the pain real?'" The research brief provides the codebase evidence needed to challenge the premise before execution begins.

## Heuristic

**Research before judge, not after**: Strategic classification (primitive/contrib/pattern/reject) requires codebase evidence that the Judge cannot generate from the FR text alone. The research step is the Red Hat: it asks "does this already exist?" and "does this belong here?" before the Judge asks "is this well-specified?" Reversing the order (Judge first, research second) wastes implementation cycles on strategically misclassified proposals.

## Seed

The research step currently searches `.chaplain/graphs/copilot/` and `docs/diary/` — the Chaplain's own context. Could it also search open GitHub Issues and recent PRs? A proposal that duplicates a closed PR from 3 months ago would be caught immediately. Combined with FR-243's remote inbox, this would give the Chaplain full situational awareness: local codebase + diary + remote history.
