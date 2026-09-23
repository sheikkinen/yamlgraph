---
type: fix
scope: prompts
req: REQ-YG-686
---

- **FR-1057 Decide the prompt template dialect once, per message**: The Jinja-vs-`str.format` decision is now made by a single discriminator (`is_jinja`) and always about one message — scalar `system`, each list-form `system` item, each `system_segments[*].content`, and `user`. Validation traverses the same units the renderer does, so a Jinja system message can no longer vouch for a `str.format` user message the renderer will reject (this was crashing `examples/dungeon_master`'s plot lane at runtime, on every run, since the lane landed). Simple-format fields are parsed with `string.Formatter` instead of a brace regex, so `{obj.field}` and `{items[0]}` are seen. Every well-formed field is a required variable whatever its format spec — `{score:.2f}`, `{name!r}`, `{value:{width}}` and the type-specific `{when:%Y-%m-%d}` alike — because Python hands the spec to the value's own `__format__` and no grammar can rule a field out. Nothing infers that a brace is merely prose: an author who wants a literal brace declares it with `{% raw %}`. Two lint errors gate the failure classes before execution: `E013` (a non-Jinja message `str.format` cannot render, naming both Jinja escapes for literal braces) and `E014` (a bare `{var}` inside a Jinja message). `W024` is retired, superseded by `E014`. (REQ-YG-686)
