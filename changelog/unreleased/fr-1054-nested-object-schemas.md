---
type: fix
scope: schema
---
- **FR-1054 Nested object schemas reach the provider**: `output_schema` fields declaring nested `object` properties are now built into real Pydantic models instead of collapsing to `dict`, so the declared shape survives into the schema sent to the provider. Applies to array items and bare object fields, recursively; nested `required` is honoured. An object declared without `properties` still maps to `dict`. Fourteen shipped example prompts were silently losing their declared nested keys.
