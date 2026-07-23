# Feature Request: FR-754 Remove `.chaplain` Path Leak from `yamlgraph.utils.id_registry`

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced (2026-07-21)
**Effort:** 0.5 days
**Requested:** 2026-07-21
**First consumer / first event:** any pip consumer of the `yamlgraph` wheel; first event is the first `import yamlgraph.utils.id_registry` in an installed environment, where `REPO_ROOT / ".chaplain"` resolves into `site-packages` and points at a directory that cannot exist.

## Summary

`yamlgraph/utils/id_registry.py` is process tooling (CAP/REQ ID reservation for the chaplain workflow) living inside the shipped package, with a hardcoded default path into the repo-process directory:

```python
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REGISTRY_PATH = REPO_ROOT / ".chaplain" / "id-registry.yaml"
```

This is the only core → `.chaplain` dependency in the codebase (verified by grep audit, 2026-07-21). Its only real consumer is `scripts/validate_id_registry.py` — a process script already excluded from the wheel.

## Value Statement

The shipped package contains zero references to repository process infrastructure, making the package boundary honest and the wheel self-contained.

## Problem

1. **Layer violation:** a Layer 3 utils module encodes knowledge of `.chaplain/`, a repo-process directory that is not a framework concept. The `.importlinter` contract cannot catch this because it is a filesystem path, not an import.
2. **Broken in installation:** `REPO_ROOT` derived from `__file__` resolves to `site-packages/` for installed packages; the default path is a lie outside the development checkout.
3. **Wrong tree:** the module's only non-test consumer is `scripts/validate_id_registry.py`. Process tooling consumed only by process scripts does not belong in the distributed package (`pyproject.toml` already excludes `scripts*` from the wheel — the code it depends on should live with it).

Scripture: `the_one_law` — normalize at the boundary. The boundary here is the package edge; the leak is inside it.

## Ideal Result

`grep -r "chaplain" yamlgraph/` returns nothing. The wheel contains no module whose only purpose is repository process management. `python scripts/validate_id_registry.py` keeps the same user-facing behavior in the development checkout.

## Proposed Solution

Relocate, don't parameterize (no shims per Commandment 8):

1. Move `yamlgraph/utils/id_registry.py` → `scripts/id_registry.py` (snake_case, outside the wheel).
2. Update `scripts/validate_id_registry.py` to import from the script-local module while preserving CLI output, exit codes, and default `.chaplain/id-registry.yaml` semantics.
3. Move `tests/unit/test_id_registry.py` expectations to the new location; the tests remain in the suite (scripts are still tested) but are classified as process tests (see FR-756).
4. Update or remove the `vulture_whitelist.py` entries that currently protect `yamlgraph.utils.id_registry` so the whitelist does not preserve a false public-API signal.
5. Delete the old module — no re-export, no deprecation shim.

## Acceptance Criteria

- [x] RED: failing test asserting `yamlgraph/utils/id_registry.py` does not exist and no `*.py` file under `yamlgraph/` contains `.chaplain` (commit separately, `SKIP=pytest`; shell `grep` optional)
- [x] GREEN: module relocated; `scripts/validate_id_registry.py` passes against `.chaplain/id-registry.yaml`
- [x] `grep -rn "chaplain" yamlgraph/ --include='*.py'` returns empty
- [x] Existing `test_id_registry.py` tests pass at new import path
- [x] `vulture_whitelist.py` no longer imports or preserves `yamlgraph.utils.id_registry`
- [x] `lint-imports` passes
- [x] Changelog fragment in `changelog/unreleased/`
- [x] Diary entry

## Judgement (2026-07-21)

**Verdict: AUTHORITY GRANTED.** Scope is frozen to relocating the ID-registry helper out of the shipped package and preserving the current validator behavior from `scripts/`.

Source read confirms the central claim: `yamlgraph/utils/id_registry.py` is the only Python file under `yamlgraph/` that references `.chaplain`, and the only live production import found outside the FR text is `scripts/validate_id_registry.py`. `tests/unit/test_id_registry.py` and `vulture_whitelist.py` are the expected test/dead-code-whitelist shadows and must move with the helper.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | The proposed relocation is correct, but the validator currently imports `DEFAULT_REGISTRY_PATH` from the package. If the script-local module keeps computing repo root from its own `__file__`, the behavior remains honest because `scripts/` is repo-root-adjacent and wheel-excluded. | Move the module to `scripts/id_registry.py`; update `scripts/validate_id_registry.py` to import from `id_registry` after inserting `scripts/` or repo root as needed. Do not leave a package import path behind. |
| F2 | The acceptance criterion says the validator works unchanged, but the import line necessarily changes. The user-facing behavior should remain unchanged, not the source text. | Preserve CLI behavior and default path semantics for `python scripts/validate_id_registry.py`; source edits to its imports are in scope. |
| F3 | `vulture_whitelist.py` currently protects `yamlgraph.utils.id_registry`. Leaving that entry after the move would keep a false public-API signal. | Update the whitelist to the new script-local module or remove entries proven unnecessary after the move. |
| F4 | The RED criterion should not depend on a fragile shell grep embedded in pytest when a direct path/string assertion is cheaper and cross-platform. | The condemning test may assert the old file path is absent and no `*.py` file under `yamlgraph/` contains `.chaplain`; shelling out to `grep` is optional, not required. |

**Purge list:** no shim, no package re-export, no environment-variable escape hatch, no new public `yamlgraph.utils` surface.

**Witness commands:** `pytest tests/unit/test_id_registry.py -q --no-cov`, `python scripts/validate_id_registry.py`, `rg -n "chaplain" yamlgraph --glob '*.py'`, and `lint-imports`.

## Alternatives Considered

- **Env var / injected path, keep module in package:** parameterizes the leak instead of removing it; the module still has no in-package consumer, so it remains dead weight in the wheel. Rejected.
- **Move to `.chaplain/scripts/`:** valid, but `scripts/` already hosts its only consumer and is already wheel-excluded; least movement wins.

## Related

- Discovered during monorepo-split critical review (2026-07-21)
- FR-180 (original Plan-Phase ID Reservation)
- `scripts/validate_id_registry.py`, `tests/unit/test_id_registry.py`, `tests/unit/test_fr441_precommit_files_patterns_red.py`
- FR-756 (core test isolation — this FR removes one of the entanglements FR-756 measures)
