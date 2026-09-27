# Reflection: FR-1122 — the key nobody read

**Date:** 2026-09-27
**FR:** FR-1122 (daily digest map node on the FR-1073 contract)

## What happened

The digest's map node said `on_error: skip` for over a month, at the
map level, where no compiler version has ever read it. Under 0.6.0 the
unread key was harmless by accident: a failed branch became an
`_error` row in `collect`, and the ranker prompt rendered it as an
article with no title, which the model quietly ignored. Under FR-1073
the same unread key is fatal: the failure is untolerated, the strict
default fires, and one unreachable URL is a red morning. The RED run
said so in one line: `accepted 2/3 (succeeded=2, tolerated=0,
failed=1)`. Tolerated zero, on a graph whose author had written the
word skip.

FR-1073's own migration census had already named this graph, row 10,
and the in-repo example was fixed under that FR. The standalone copy
was outside the census's edit surface, so it kept the key. The
research personas then made the mirror-image mistake: two of them
argued the migration could ship now because "the sub-node key is read
on both versions". True, and beside the point: the key is read on
both, but the collected shape differs, so the flat-item prompt is only
correct on the release that classifies failures. The judge's C-2 gate
was the cure, and the isolated 0.6.0 install proved why in one
traceback: `No module named yamlgraph.models.map_results`.

## Trap

`declaration_is_not_policy`: a correctly spelled key in the right file
feels like a decision made. A configuration key is a claim; only the
compiler's read makes it a policy. The same trap, one level up, is a
version floor with no ceiling: `>=0.5.23` feels like a decision and is
in fact a promise to accept whatever the next release means.

## Heuristic

For every policy key a graph declares, ask which line of the compiler
reads it, and write the witness at that line, not at the YAML. When a
consumer lives outside the repository that owns the contract, gate its
migration on the published version that carries the contract, and
prove the gate with an isolated install of the version it runs today,
not with reasoning about which keys are "read on both".

**Seed:** The unread-key class is detectable statically: a schema of
"keys the map compiler reads at map level" versus "keys it reads on the
sub-node" would let `graph lint` say "map-level `on_error` is never
read" the day it is written. FR-1119 taught the linter what a map
creates; should a sibling teach it what a map ignores, and would that
lint have caught row 53 (`image_pipeline`), which FR-1073 left strict
on purpose?
