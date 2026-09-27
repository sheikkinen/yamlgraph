# Reflection: FR-1124 — the scanner that said "none"

**Date:** 2026-09-27
**FR:** FR-1124 (top-level `llm` default `on_error: fail`)

## What happened

The census classified 224 undeclared `llm` nodes as A (adopt `fail`) or
B (intentional tolerated skip). The raw output had 199 `a`, 15 `b` and
5 abstain. After reading every `b` and abstain against source, 17 of
them became A.

Most overridden rows cited the same line of the dossier:
`NODES_REFERENCING_STATE_KEY: none`. That line came from a substring
scan of the graph YAML. It cannot see a python node reading the key in
its function body, so "none" meant "the scanner found nothing", not
"nothing reads this". The model reasoned correctly from what the
dossier said. The dossier was wrong.

The six novel_fandom `create_*` graphs have the same `check` node. The
census split them 3 `b` / 3 `a`. The source settled all six as B: the
prompt header says the check is an advisory verdict of two lines or
fewer, and the node runs after `persist`.

A second contradiction appeared at GREEN. FR-1097's AC-02 test pinned
exactly the record-and-continue exit 3 that this FR removes. The
judgement also forbade changing FR-1097 expectations. Both could not
hold. The operator chose the deviation, and it is recorded, not buried.

## Trap

`absence_from_blind_scanner`: a dossier field that reports absence
("none", "0 readers") inherits the blind spots of the scan that produced
it. A census model treats that absence as evidence, and the verdict
looks well-supported.

## Heuristic

Label every absence field in a census dossier with its scan method
(`substring-in-yaml`, not `readers`). Before accepting any verdict that
rests on an absence, check one row by hand through the channel the scan
cannot see. When identical items get split verdicts, the model is
reporting that it cannot decide. Settle the question from the source,
not by majority vote.

## Seed

**Seed:** Should `corpus_census` dossiers carry a per-field provenance
tag, and should the reducer flag rows whose deciding evidence is only an
absence field, so that a reader knows which claims came from a blind
scanner?
