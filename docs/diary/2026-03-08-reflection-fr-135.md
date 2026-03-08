# Reflection: FR-135 Examples Value Audit

**Date:** 2026-03-08
**FR:** FR-135
**Commit:** 775a35b

## Context

FR-135 addressed documentation debt in `examples/README.md`. The examples directory had grown organically — 30 demos and 19 top-level examples — but the README only listed a fraction. New contributors couldn't discover what existed; maintainers couldn't assess coverage gaps.

## Changes

- Rewrote `examples/README.md` with complete inventory
- Split Demos Index into three categories: Learning (26), Utility (3), FR Validation (1)
- Added Inclusion Criteria section documenting the quality bar (README + runnable artifact + feature statement)
- Created missing `examples/diary_digest/README.md`
- Moved stale demos (`commit-delta-gate`, `session-test`) to `purgatory/`
- Added 7 tests in `test_examples_readme_audit.py` (REQ-YG-147, CAP-49)

## Trap: inventory_blindness

The examples directory had accumulated without a census. Each addition seemed small in isolation, but the aggregate created a discovery problem. The trap: assuming "I added a README" equals "users can find it." Without an index, even well-documented examples are effectively undiscoverable.

## Cure: periodic_inventory

Schedule inventory audits for directories that grow by accretion (examples, scripts, tools). A simple count mismatch (README mentions 8, directory contains 30) signals drift. The audit test now enforces this automatically.

## Seed

Could the three-category demo index (Learning/Utility/FR Validation) be generated from YAML frontmatter in each demo's README, eliminating manual sync?
