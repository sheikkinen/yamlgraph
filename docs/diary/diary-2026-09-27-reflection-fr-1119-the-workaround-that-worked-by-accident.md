# Reflection — FR-1119: the workaround that only worked by accident

## What happened

FR-1116 hit a false E007 on `{state._map_verdict.summarize.dispatch}` and
"repaired" it by declaring `_map_verdict: dict` in `meta_map`'s `state:`.
The declaration looked harmless. It was harmless only because the state
builder happens to let node-derived fields overwrite declared ones — if
that precedence ever flipped, the declaration would silently replace the
`merge_by_key` reducer with plain last-write, and parallel map verdicts
would clobber each other.

The fix was seven lines in the linter. The judge's contribution was
larger than the fix: I had counted three map-owned fields; the builder
creates five. My FR also claimed the linter could not import the state
builder — it already did, one line above the function I was editing.

## Trap

**Workaround-by-precedence:** a workaround that type-checks, lints and
runs can still depend on an ordering rule nobody wrote down. The test
that would catch it is not "does it run" but "what if the other side
won".

## Heuristic

When a declaration exists only to silence a checker, ask which
component's precedence makes it inert. If the answer is "an unwritten
merge order", fix the checker, not the declaration site. And count the
oracle's output before counting from memory — `extract_node_fields` was
the parity test and the spec in one call.

**Seed:** E007 now mirrors the builder for map nodes only. Would a
single "fields this node creates" function shared by builder and linter
have prevented both FR-1073's omission and my three-vs-five miscount —
and what negative controls would it need to not widen E007 for every
other node type?
