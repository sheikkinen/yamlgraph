# Reflection: FR-219 Dependency Rationale Audit

**Date:** 2026-04-09
**FR:** FR-219
**Trap:** infrastructure-self-exempt — the noqa confession pattern enforces documentation for suppression decisions, but no equivalent gate existed for dependency additions.

## Cognitive Process

The threat model surfaced by FR-218 (unprompted dependency injection as an agent attack vector) made the gap obvious: we audit code imports structurally but accept new packages without documented rationale. The noqa confession pattern (`docs/confessions.md` + `scripts/noqa_coverage.py`) is a proven registry-audit pair. FR-219 applies the same pattern to `pyproject.toml`.

## Insight

Every enforcement gate that applies to code should also apply to the infrastructure that supports code. When a pattern works (registry + audit + CI gate), replicate it at every boundary where undocumented decisions accumulate.

## Heuristic

> Registry + audit script + pre-commit hook = documented boundary. If you can't name why a package is there, you can't defend it in a security review.

**Seed:** Could the same pattern extend to environment variables? A `docs/env-rationale.yaml` audited by a pre-commit hook that checks `.env.example` and `os.environ` calls would close the "why does this need this secret?" gap.
