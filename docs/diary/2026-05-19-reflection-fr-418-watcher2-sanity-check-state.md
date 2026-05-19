# Reflection: FR-418 Fallback Confession Gate — Watcher2 Sanity Check

**Date:** 2026-05-19
**FR:** FR-418 — fallback-token confession gate for production Python
**Reviewer:** watcher2 post-validate sanity checker

## Trap

`detection_without_enforcement` — `hedging_check.py` existed and ran in pre-commit, but only caught one of two documented AST patterns, covered only `yamlgraph/`, and had no lexical surface scan. The script's own docstring promised Pattern 2 detection that was not implemented. The gate was advisory decoration, not a real guard.

## What Happened

Issue #418 exposed three compounding gaps:
1. The ALLOWLIST was typed as `set[str]` with no confession reference — passing the gate required no documentation at all.
2. Lexical `fallback` tokens in identifiers, comments, and docstrings were completely invisible to the detector.
3. `scripts/` directory was out of scope, so `extract_copilot_events_lib.py` and `req_coverage.py` accumulated 7 unguarded fallback references.

Implementation added FB001 lexical scanning (identifiers, docstrings, comments via `tokenize`), changed `ALLOWLIST` to `dict[str, str]` (`file:line → CONF-XXX`), validated allowlist entries against `docs/confessions.md`, expanded pre-commit scope to include `scripts/`, added Pattern 2 (`X = expr or fallback`) detection, and back-filled 43 confessions (CONF-212 through CONF-254).

## Root Cause

The gate checked shape (file exists, ALLOWLIST key present) but not substance (confession entry valid, code surface correct). This is the `gate_checks_shape_not_substance` trap: a `set[str]` ALLOWLIST means any string satisfies the exception without any linked documentation.

## What Worked

- **TDD discipline held**: 7 RED tests were written first, mapped to AC-01–AC-06, before any production change. All 7 pass GREEN after implementation.
- **Boundary normalization at entry**: allowlist validation runs once at scan time (`_validate_allowlist_for_scan`), not scattered through detection logic.
- **Confession reuse**: `docs/confessions.md` was extended rather than creating a parallel registry — constraint AC-04 satisfied without scope creep.
- **Requirement traceability complete**: REQ-YG-408 added to `ARCHITECTURE.md`, CAP-16 capability YAML updated, changelog fragment written with req field, test class marked `@pytest.mark.req("REQ-YG-408")`.

## Proportionality Assessment

824 lines changed across 9 files. The bulk is confession back-fill (258 lines in `docs/confessions.md`) and `hedging_check.py` extension (+175 lines net). Scope matches FR: no runtime behavior changes, no new scripts, no new registries. AC-08 compliance adds expected cross-cutting churn to `ARCHITECTURE.md` and `CAP-16`. **Proportional.**

## Seed:

When a confession gate validates `file:line → CONF-XXX` mappings at lint time, what prevents line numbers from drifting silently as files change? Should confessions reference a stable symbol (function name or AST path) rather than a volatile line number, and what would a migration from line-anchored to symbol-anchored confessions look like?
