# FR-419 — Kill `_translate_legacy_config`: ActionConfig Schema Boundary

**Date**: 2026-05-19
**FR**: [FR-419](../feature-requests/FR-419-kill-translate-legacy-config.md)
**Commandment ref**: Commandment 8 ("No shims")

---

## What happened

The task was to kill `_translate_legacy_config()` — a compatibility shim in the chaplain FSM adapter that:
1. Silently mapped flat YAML keys (`vars`, `error`, `success`, `event_map`, …) into a `params` sub-dict
2. Had grown to an allowlist that could silently drop unknown keys
3. Violated Commandment 8 by existing at all

FR-419 replaced it with a Pydantic `ActionConfig` model (`extra="forbid"`, `AliasChoices`) that parses once at the schema boundary in `execute()`.

---

## Cognitive traps encountered

### 1. Downstream-fix trap
The FR-416 patch (event_key forwarding in `_translate_legacy_config`) was a downstream fix — adding another case to an allowlist. I caught this and wrote FR-419 to normalize at the boundary instead. Classic `downstream_fix` → `normalize at entry boundary` cure.

### 2. Test-interface ossification
After deleting the shim, three tests kept accessing `action.config.get("params", {})` — which was the shim's side-effect, not a contract. They passed before deletion because the shim stuffed the parsed params into `config["params"]`. After deletion, they silently returned `{}` and broke. Fix: rewrite tests against `ActionConfig.model_validate()` directly — the real contract now lives in the Pydantic model.

This is a variant of **plausible_wrong_answer**: the tests had the right shape (they called through the adapter) but were testing an implementation detail that should never have been the contract.

### 3. Vulture false positives on Pydantic framework methods
Vulture flagged `_normalize_event_map` (a `@field_validator`) and `failure` (a field with `AliasChoices`) as dead code. These are framework-invoked; vulture can't see the call sites. Added both to `vulture_whitelist.py`. Lesson: any `@field_validator` or field with complex alias needs a whitelist entry immediately — don't wait for the test to catch it.

### 4. Stale test in FR-413 suite
`test_ac03_legacy_top_level_config_translates_to_shared_params` tested the shim's `config["params"]` side-effect. After the shim was deleted, the test assertion became false by construction. Updated to test `ActionConfig.model_validate(flat_config)` directly — which is both correct and more precise.

---

## Heuristics extracted

- **When deleting a shim, grep its side-effects** — `config["params"]`, not just the method name. Tests accessing `action.config.get("params")` are testing the shim artifact, not the contract.
- **Pydantic validators need immediate whitelist entries** — `@field_validator` and `AliasChoices` fields are invisible to vulture; don't wait for the CI vulture test to catch them.

---

## Seed

When `extra="forbid"` rejects an unknown key at runtime (not in tests), the error surfaces in FSM logs. Is there a pattern to promote those validation errors into FSM `error` events automatically, so the state machine can recover rather than crashing the action?
