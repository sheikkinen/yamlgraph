# Diary: FR-796 Watcher2 Witness Curation

**Date:** 2026-08-15
**FR:** FR-796

## What happened

Ten infrastructure witnesses had accumulated under `examples/demos/` because
the demo proof gate required executable evidence for changes that touched demo
paths. Their files satisfied the gate, but their purpose was regression proof,
not teaching. FR-796 deleted three one-shot witnesses and moved seven retained
watcher2 graphs beside the Chaplain runtime they inspect.

The move was deliberately content-preserving. An independent audit verified
26/26 non-README files byte-for-byte and all seven graphs linted from their own
artifact directories. Default discovery stopped exposing the nine graph names
without any discovery-code change. One relocated CI-remediation witness ran
successfully from `.chaplain/demos/` and produced fresh evidence there.

## Reflection

The trap was **membership by compliance**: passing a directory's gate was
quietly treated as proof that the artifact belonged in that directory. The
gate answered whether an artifact was runnable, not whether newcomers should
see it or MCP should advertise it. Location remained an unexamined product
decision with a recurring context cost.

The move also exposed historical witness rot. Two unchanged tool-only graphs
still linted but failed against runtime or documentation contracts that had
since disappeared. Preserving bytes made that evidence visible instead of
silently modernizing the witnesses under a curation FR.

**Heuristic:** Validate both admission and membership: execution proof answers
"does it run?" while ownership and discovery policy answer "does it belong
here?"

**Seed:** Should discovery surfaces require an explicit audience classification
so infrastructure witnesses cannot enter a user-facing garden by path alone?
