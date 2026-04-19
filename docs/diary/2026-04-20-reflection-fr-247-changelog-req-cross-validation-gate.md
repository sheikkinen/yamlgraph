# Reflection: FR-247 Changelog REQ Cross-Validation Gate

**Date:** 2026-04-20
**FR:** FR-247
**Branch:** feat/fr-247-changelog-req-cross-validation-gate

## What Was Done

Implemented `scripts/check_changelog_req.py` — a mechanical validator that parses YAML front-matter `req:` fields from `changelog/unreleased/*.md`, then looks up each REQ-YG-XXX in the capability registry (`capabilities/CAP-*.yaml`) to confirm it exists. Phantom REQs (those not in any CAP file) are rejected with a clear error. Fragments without a `req:` field are silently skipped. Single-REQ CAPs pass mechanically; multi-REQ CAPs are passed to an LLM graph (`graphs/enforcement/changelog-req-check.yaml`, Haiku, temperature 0) for semantic matching. Wired as a pre-commit hook and CI job.

FR-242 added `test_changelog_req_cross_wiring.py` which caught cross-wired REQ IDs in changelog fragments after rename operations — this FR formalizes that check into a standalone tool with a proper gate.

## Cognitive Trap: Detection Without Enforcement

The FR-242 test already caught phantom REQs in test runs, but there was no gate at the pre-commit or CI level that explicitly blocked the `req:` mismatch before a commit landed. The inquisitor audit pattern (FR-242: add test → FR-247: add gate) is the canonical graduation path: test proves the constraint, gate enforces it at the boundary.

The recurring pattern: **audit_as_ritual** → a check that finds problems but doesn't block them drifts into a ritual. The gate makes the ritual boring (boring = judgement was good).

## Heuristic

**Every detector needs a gate**: A test that catches cross-wired REQs is necessary but not sufficient. Pair every detection mechanism with a pre-commit hook or CI block at the merge boundary. If detection exists without enforcement, it will eventually be ignored under deadline pressure.

## Seed

The `check_changelog_req.py` mechanical phase validates phantom REQs. Could it also validate the *direction* — that the REQ cited in the changelog fragment actually matches the capability described in the change diff? That would catch cases where a developer copy-pastes a REQ ID that exists but belongs to a different feature. Semantic matching (currently deferred to the LLM graph for multi-REQ CAPs) would need to be extended to the single-REQ case.
