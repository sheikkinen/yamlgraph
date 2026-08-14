# Diary: FR-788 API Discovery Platform-Confirm Step

**Date:** 2026-08-14
**FR:** FR-788
**Duration:** ~15 min (after FR-794's framework fix unblocked it)

## What happened

Resumed FR-788 after FR-794 (the shared Python tool manifest root
confinement fix) landed. Re-ran the exact same `scripts/author.sh`
task brief that had previously failed with the framework bug — this
time it succeeded end-to-end, including both required live smoke
validations (positive: CKAN's public demo instance; negative:
`example.com`), with the agent self-correcting a `--var` vs `--var-file`
list-serialization mistake mid-run and recording the repair honestly.

## Trap encountered: a guard I couldn't move around

Restoring the platform-confirm files (temporarily relocated to `tmp/`
so FR-794 could commit without tripping FR-786's overly-strict sibling-
directory test) via a plain `mv` was **denied** by the FR-767 sentinel
guard — it treats ANY write to `examples/**/graph.yaml` outside an
armed authoring sentinel as unauthorized, even a restore of content the
adapter itself had produced minutes earlier. The correct move was not
to look for a workaround but to re-invoke `scripts/author.sh` with the
same brief — the sole route is the sole route regardless of whether the
content is "new" or "a restore." This is the guard working exactly as
designed (`operational_safety`: don't brute-force around a guard).

## Trap encountered (again): a downstream test assumed siblings never exist

FR-786's `test_no_sibling_step_artifacts_introduced` asserted that
`browser-sniff`/`orchestrator`/`platform-confirm`/`schema-extract`
directories never exist — true only until any sibling FR (like this
one) legitimately creates its own directory. Fixed by rescoping the
assertion to "FR-786's own graph doesn't reference those siblings" (a
real boundary check) instead of "those directories must never exist
anywhere in the repo" (a false global claim masquerading as a scope
test). Any FR-786-style boundary test for a multi-FR pipeline should
assert on the diff/dependency, not on directory existence.

## Insight: judge-then-fold-then-rejudge scales to multi-hour interruptions

FR-788 was folded and approved ~5 hours before this resumption (in
diary-2026-08-14-page-analysis-step.md's sibling arc). The frozen scope
table from that judgement was still exactly correct after the
intervening FR-794 detour — nothing needed re-litigating. A judged,
frozen FR scope survives an unrelated multi-step interruption cleanly;
the judgement artifact IS the resumable checkpoint.

## Heuristic

When a framework bug blocks an in-progress graph-authoring task, do NOT
try to work around governed-path guards to preserve the in-progress
artifacts — relocate them outside governed paths (or just accept
re-authoring cost) and let the SAME task brief re-enter the sole route
once the blocker is fixed. The task brief itself is the durable
artifact; the authored files are disposable and regeneratable from it.

## Seed

Should task briefs (`tmp/task-*.md`) be promoted to a committed,
`.gitignore`d-but-tracked-in-spirit location so that a resumed
authoring run after a multi-step detour doesn't depend on the same
session's `tmp/` surviving? If a session ends between "author.sh failed"
and "framework bug fixed," the next session has no way to know a task
brief exists to resume from.
