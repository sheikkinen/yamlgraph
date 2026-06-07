# Feature Request: FR-Number Allocation & Collision Gate

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-06

## Summary

Add an allocation helper and a CI/pre-commit gate for **FR document numbers**, mirroring the
uniqueness guarantees that `validate_capabilities.py` already enforces for CAP `id:` and
REQ-YG IDs. FR numbers are currently allocated by hand with no validation, so parallel work
streams (e.g. the Chaplain automation vs. manual branches) repeatedly assign the *same* FR
number to *different* features.

## Value Statement

Contributors get a single command to claim the next free FR number and a gate that blocks a PR
the moment two different features collide on one number — making FR identifiers as trustworthy
as CAP/REQ identifiers and eliminating the rebase-time renumbering churn observed in v0.5.5.

## Problem

A whole-registry numbering audit (2026-06-06) found:

| Registry | Uniqueness | Gate today | Audit result |
|----------|-----------|------------|--------------|
| CAP `id:` (in YAML) | required | `validate_capabilities.py` | ✅ clean (152 files) |
| CAP filename ↔ `id:` | required | `validate_capabilities.py` | ✅ consistent |
| REQ-YG IDs | required | `validate_capabilities.py` + `req_coverage.py` | ✅ 291 unique, RC=0 |
| **FR doc numbers** | **expected** | **none** | ❌ **30 genuine two-topic collisions** |

The CAP/REQ registries are clean *because* a validation gate exists. FR numbers collide *because*
no gate exists — the only FR-related hook is the commit-msg rule requiring a `feat:` commit to
*reference* some `FR-XXX`, which does not check that the number is unique or unclaimed.

Representative genuine collisions (different topics sharing one number):

- `FR-082` — `minesweeper-game` vs `sampling-backend`
- `FR-179` — `append-only-changelog` vs `asterisk-ari-audiosocket-provider`
- `FR-239` — `chatterbox-speak-multilingual` vs `meta-yamlgraph-self-improving-graphs`
- `FR-464` — `deepseek-structured-output-fallback` vs `meta-self-reflective-demo`
- `FR-465` — `llm-safety-settings` vs `watcher2-test-cleanup`
- `FR-466` — `cap-retirement-support` vs `dungeon-master-example`
- `FR-467` — `conditional-edge-to-map-node` vs `mission-control-unified-observability`

The four `FR-464…467` pairs are simply the newest instances of a 30-pair systemic pattern; the
v0.5.5 release had to manually renumber CAP/REQ IDs at rebase time to avoid clobbering upstream.

This is the doctrine's `detection_without_enforcement` trap: a convention that is documented but
not mechanically gated drifts. Per `enforcement_at_merge_boundary`, the fix belongs at the PR gate.

## Proposed Solution

Three small additions, no changes to existing FR files:

1. **`scripts/next_fr.py`** — prints the next free FR number, considering FR files on the current
   branch **and** on `origin/main` (so concurrent branches don't collide):

   ```bash
   $ python scripts/next_fr.py
   FR-469
   ```

2. **`scripts/validate_fr_numbers.py`** — fails when one FR number maps to two or more *distinct
   topic slugs* (`FR-NNN-<slug>.md`). Benign stubs (`FR-NNN.md`) and directories are ignored.
   A `--baseline` file records the 30 pre-existing historical collisions so the gate blocks only
   *new* collisions (the historical 30 are accepted debt, not worth churn-renumbering).

   ```bash
   $ python scripts/validate_fr_numbers.py --strict
   ❌ FR-470 has 2 distinct topics: alpha-thing, beta-thing
   ```

3. **CI + pre-commit gate** — add `fr-number-gate` to `.github/workflows/commitlint.yml`
   (PR boundary) and a local `pre-commit` hook calling `validate_fr_numbers.py --strict`.

### Explicitly NOT doing: mass renumbering

Renaming the 30 historical collisions would break cross-references in commit messages, CHANGELOG
fragments, diary entries, and CAP `fr:` fields for zero behavioural benefit. The baseline file
freezes existing debt; the gate prevents *new* debt. This matches how `confessions.md` records
accepted `# noqa` debt rather than rewriting history.

## Acceptance Criteria

- [ ] `scripts/next_fr.py` returns a number unused on both local branch and `origin/main`.
- [ ] `scripts/validate_fr_numbers.py --strict` exits non-zero on a *new* two-topic collision and
      zero on the current tree (baseline absorbs the 30 historical pairs).
- [ ] Baseline file lists exactly the 30 current genuine collisions; adding a 31st new collision
      fails the gate.
- [ ] `fr-number-gate` added to CI required status checks; pre-commit hook added.
- [ ] Tests added (`tests/unit/test_validate_fr_numbers.py`) with `@pytest.mark.req`.
- [ ] CAP + REQ allocated for the new capability; `CLAUDE.md` allocation note updated.
- [ ] Diary reflection added.

## Alternatives Considered

- **Mass-renumber all 30 collisions** — rejected: breaks references across the repo for no
  behavioural gain (see "Explicitly NOT doing").
- **Switch FR IDs to UUIDs/timestamps** — rejected: human-unfriendly, breaks the readable
  `FR-XXX` convention used throughout Scripture and commit messages.
- **Register FRs in a single YAML manifest (like CAPs)** — heavier; deferred. The
  filename-based gate is the minimal sufficient enforcement and keeps FRs as plain markdown.

## Related

- Audit findings: CAP/REQ registries clean (`validate_capabilities.py`, `req_coverage.py`).
- `scripts/validate_capabilities.py` — the uniqueness gate this FR mirrors for FR numbers.
- Doctrine traps: `detection_without_enforcement`, `enforcement_at_merge_boundary`,
  `cross_project_graduation` (collisions arise from parallel Chaplain + manual streams).
- v0.5.5 release: rebase-time CAP/REQ renumbering (CAP-163→166, 164→167, 165→168;
  REQ-YG-428→467) that this gate would have flagged earlier.
