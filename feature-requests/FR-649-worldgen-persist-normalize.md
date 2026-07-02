# FR-649: Worldgen persist_pages normalize at boundary

**Status**: Enforced
**Scope**: `examples/novel_fandom`

## Problem

The worldgen pipeline silently drops deepened pages because `persist_pages` validates LLM output against strict Pydantic schemas in `canon.py`, and the LLM returns structurally varied data.

Evidence from a 2-iteration run (2026-07-02):
- 26 validation failures across 3 iterations
- Affected entities: aldric_vane (×5), thrain (×4), hestia (×2), ashfall (×4), cave_of_whispers (×2), ashguard_emberwright_war (×1)
- All deepened content (backstory, triggers, relationships) was generated but silently discarded
- Pages reverted to thin skeletons — the pipeline's core work product was lost

### Root cause

Schema-LLM mismatch at the persist boundary. The LLM invents structurally equivalent but schema-incompatible representations:

| Field | Schema expects | LLM returns |
|-------|---------------|-------------|
| `Relationship` | `{to, kind, valence}` | `{target_id, type, description}` or `{id, description}` or `dict[str, str]` |
| `Event.participants` | `list[str]` | `list[dict]` with `{entity, role, loss, gain}` |
| `Event.consequences` | `list[str]` | `dict` with faction-keyed gains/losses |
| `references` | `list[str]` | `list[dict]` with `{pageId, type}` |
| `Location.atmosphere` | `list[str]` | `str` |

This is a textbook instance of the Scripture trap **downstream_fix**: validation rejects at persist (symptom), but the fix belongs at the boundary where LLM data enters (normalize).

## Proposed solution

Add a `normalize_page(page: dict) -> dict` function in persist_pages (or a new `normalize.py` module) that coerces LLM-varied shapes to schema-expected shapes **before** Pydantic validation:

1. **Relationships**: Extract `to` from `target`, `target_id`, or `id`; extract `kind` from `type`; coerce `valence` from `description` if missing; handle dict-of-strings format
2. **Participants**: If list contains dicts, extract `entity` or `name` field as string
3. **Consequences**: If dict, flatten to `list[str]` as `"{key}: {value}"` entries
4. **References**: If list contains dicts, extract `pageId` or `id` field as string
5. **Scalar/list mismatch**: Wrap bare strings in lists where schema expects `list[str]`
6. **Rule.domain**: Default missing/unrecognized domain to `"social_rule"` (valid Literal values: `magic_system|character_state|physical_constraint|social_rule|temporal_rule`)
7. **Strip `_map_index`**: Defensive `page.pop("_map_index", None)` to prevent map-node metadata from polluting YAML

The normalizer runs once per page in `_validate_and_write`, before the `model_cls(**page)` call.

**Fallback**: If normalization + validation still fails, persist the raw page anyway with a logged warning — the pipeline's work product is more valuable than strict schema compliance for a fiction wiki.

## Acceptance criteria

1. All observed normalization patterns from the 2026-07-02 run are covered; unknown patterns log a warning but do not silently drop the page
2. Deepened pages retain backstory, triggers, relationships after persist
3. Existing seed pages (kaelen, maren, voss) continue to validate without normalization
4. Unit tests cover each normalization path (relationship variants, participant dicts, consequence dicts, reference dicts, scalar→list coercion, Rule.domain default, _map_index strip)
5. Pages that still fail after normalization are persisted with a warning (not dropped)

## Out of scope

- Changing the deepen_entity prompt to force exact schema shapes (fragile, provider-dependent)
- Relaxing Pydantic schemas to accept arbitrary shapes (defeats validation purpose)
- Fixing render_wiki.py tolerance (already done separately)

## Constraints

- Normalize at boundary, not downstream (Scripture: the_one_law)
- Pure Python, no LLM calls
- Must not break existing persist_pages test suite
