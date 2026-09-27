---
type: fix
scope: schema
req: REQ-YG-712
---
- **FR-1125 Refuse unconstrained objects on Anthropic-bound nodes**: an output-schema object with no declared `properties` (`dict`, `dict[str, Any]`, `list[dict]`, or an `output_schema` object without `properties`) is refused at lint (E017 static Anthropic, W029 run-time provider), compile and bind time on Anthropic-bound nodes, because constrained decoding rewrites it to `{}` and the model can only answer empty (the digest's zero-story run on 0.6.1). `schema_walk` returns typed `SchemaFinding`s for both kinds; the refusal message points at the `output_schema` form with declared item properties instead of `list[dict]`; the SDK parity test compares transformed content by canonical path; the linter check moved to `checks_schema.py`. The repository's nine Anthropic-bound open-object fields are retyped with declared properties, and `questionnaire#classify` runs on Mistral. (REQ-YG-712)
