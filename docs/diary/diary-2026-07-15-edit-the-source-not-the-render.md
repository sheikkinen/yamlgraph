# 2026-07-15 — The gate that ordered my commits, and the edit I almost fossilized

**Context:** FR-731 enforce (WebLLM rung-1 spike): RED → GREEN in two
commits, 14 condemning tests, compiler + artifact + consent-gated page.

**Trap one — hand-editing the generated.** The req-coverage hook
rejected the RED commit because REQ-YG-562 existed only in test marks.
My first fix was to hand-edit the REQ row into ARCHITECTURE.md — inside
a block bounded by `<!-- END GENERATED CAPABILITIES -->`. The marker
was in plain sight; I saw it only after the edit. A hand edit inside a
generated region is a fossil: correct today, silently overwritten on the
next `aggregate_capabilities.py` run, and then the gate failure returns
wearing a different commit. Reverted, edited the CAP YAML (the source),
ran the generator. The general rule is the one_law itself applied to
docs: **edit at the source-of-truth boundary, never at the rendered
surface** — the same discipline as not patching compiled output.

**Trap two — the traceability spine has an ordering constraint.** The
RED commit could not land before the REQ existed in the registry: the
gate forces REQ-before-test, which means the traceability paperwork is
not "AC-05 paperwork at the end" but a *precondition of the first
commit*. The enforce-order in judgements should say so; this one
didn't, and the discovery cost three commit bounces.

**Recurrence noted, not new:** tmp/msg-fr731-red.txt vanished between
write and use — another session's tmp/ sweep (one_session_one_repo,
strike N). Commit messages are now the second artifact class lost to
the shared-repo interleave, after staged files.

**What went right:** read_raw_output_first was mechanical this time —
`cat prompt.json` before any test asserted on it showed
`minimum/maximum` and defaults in place; the tests then confirmed what
had already been *seen*. The FR-732 judgement two days ago (native
schema path preserves constraints; output_schema path does not) is
exactly why this artifact compiles from critique.yaml's native block —
cross-FR constraint reuse with zero new framework surface.

**Seed:** the req-coverage gate taught me commit *ordering* — could the
judgement template carry a mechanical "enforce preconditions" list
(REQ registered, CAP id free, changelog fragment named) that the
chaplain checks before the first RED, the way pre-commit dry runs
check format? The gates exist; what's missing is their *schedule*.
