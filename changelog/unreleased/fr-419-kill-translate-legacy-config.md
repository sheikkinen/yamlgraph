---
type: fix
scope: fsm
---
- **FR-419 Kill _translate_legacy_config**: Replaced `_translate_legacy_config()` compatibility shim with Pydantic `ActionConfig` schema boundary validation. Unknown YAML keys now raise `ValidationError` at parse time (`extra=forbid`). Flat config aliases (`vars`, `error`) handled via `AliasChoices`. `_normalize_event_map` moved into `ActionConfig` field validator. `_ENVELOPE_KEYS` strips `type`/`params` envelope before validation.
