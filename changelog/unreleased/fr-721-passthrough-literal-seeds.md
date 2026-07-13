---
type: fix
scope: schema
req: REQ-YG-546
---
- **FR-721 Passthrough literal seeds**: `output`/`outputs` on passthrough nodes now validate as `dict[str, Any]`, matching the runtime contract — `resolve_template` passes non-string literals (lists, dicts, bools) through unchanged, so init nodes seeding state with literals no longer fail schema validation. Unblocks consumers pinned at 0.5.7 whose graphs raised ValidationError on upgrade (ninchat NC-370). Mapping fields (`output_mapping`) remain string-only. (REQ-YG-546)
