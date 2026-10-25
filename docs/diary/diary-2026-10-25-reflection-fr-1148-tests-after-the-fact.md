# Reflection: FR-1148 — tests after the fact

**Date:** 2026-10-25
**FR:** FR-1148 (thinking_budget 0 turns Anthropic thinking off), the owed tests and docs

## What happened

The rule went to `main` by direct push before its tests. The tests owed by the judgement — the request payload
rather than the `thinking` attribute, every model pinned, Probe A's fourteen ids — came three PRs later, after the
size-gate fix and the module split. They could only be witnesses: they assert what already ships, and no commit
shows them failing first.

A witness that has never failed proves less than a RED test. The cheap substitute was a mutation: change one
outcome of the rule in the working tree, run the new file, see which tests fail, revert. Two failed, both on the
mutated model; the other nineteen did not move, which also shows they do not all test the same thing.

The docs had the opposite problem: two of the five sites were already updated by the direct push, three were not,
and the capability text still described only `≥ 1024`. A partial doc update looks finished from any one site.

## Root cause

Skipping the gates on the code push did not skip the work; it moved it later, and later the order (test first)
cannot be recovered. Every downstream PR inherited a debt it had to name.

## Heuristic

**When tests arrive after the code, mutate the code once and record which tests fail.** It is the nearest thing to
a RED commit that history still allows, and it costs one command.

## Corrective actions

- Payload-level tests for AC-01..AC-06, every Anthropic test pinned (AC-07), the mutation result in the FR.
- REQ-YG-083, CAP-28 modules, the reference sites and the `create_llm` docstring state the `0` contract.

**Seed:** Should the changelog or diary gate ask, for a `test` PR that covers an earlier `fix`, for the mutation
witness — so "tests after the fact" carries proof that they can fail?
