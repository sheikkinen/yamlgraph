# 2026-07-16 — A map for the amnesiac

**Context:** graduating the storage–data-model arc from repo memory
(the tap note, `where-repo-notes-live`) into the record: session
titles in the cost tables, the actual-cost recheck, the full Copilot
storage tree, and MAP.md. The arc ended by producing a document whose
intended reader is *me after the next compaction* — and that framing
turns out to be the day's real finding.

**"Repo memory" does not live in the repo.** Filesystem inspection:
all three memory-tool scopes sit under the user dir, keyed by
workspace hash. The repo scope travels with neither git nor machine —
one repo on two machines has two disjoint "repo" memories. The name
promises a scope the implementation doesn't deliver: a
*name-implies-portability* cousin of `gate_checks_shape_not_substance`
— the label validates an expectation nobody tested. The existing
doctrine note (`where-repo-notes-live`: diaries are the durable
memory) was written from instinct; today it acquired a filesystem
proof. Instinct upgraded to fact — which is exactly what this diary
system is for.

**The universal join key.** One base64 decode
(`ODU0YzZhMzUt…` → `854c6a35-…`) confirmed the session UUID threads
eight stores: request log, transcript, spilled tool results, debug
logs, edit checkpoints, session memory, todo lists, and the OTel tap.
The investigation's recurring method held for every store this week:
`read_raw_output_first` — one raw record read (a decode, a sqlite
SELECT, a head -1) beat every schema speculation, every time, at a
cost of seconds. The basement probes also surfaced a live blind spot:
**`copilotcli:/` sessions appear in ChatSessionStore.index and are
costed by nothing** — every chaplain/watcher run is invisible spend.

**Why the map has a "do not re-derive" section.** This morning the
tap watched my own context get guillotined (748K → 69K). The lesson
generalizes past session memory to *project* knowledge: six
calibration constants (98% cache, rounds×, ~750K ceiling, the phantom
rule, seam-lag semantics, 1 cr = $0.01) each cost a real incident to
learn, and each would be silently re-derived — wrongly, at some cost —
by any future session that didn't inherit them. MAP.md's structure
(instrumented / probed / dark, seams with escalation ladders, facts
marked do-not-re-derive) is the compaction altimeter's insight applied
to documentation: **write for the amnesiac successor, because the
amnesia is scheduled.** A doc addressed to "whoever reads this" is
addressed to no one; a doc addressed to a post-compaction agent that
must not re-pay for known facts has a reader, a rung, and a moment —
the reception test the board initially failed.

**Distilled:** `document_for_the_successor_not_the_present` — the
test of an investigation artifact is not whether it records what was
found, but whether a context-free reader can *resume without
re-paying*. Territory state, join keys, calibration constants,
escalation ladders, ranked directions: these are the resume-file
fields. Findings prose without them is a trip report, not a map.

**Seed:** the map marks `copilotcli:/` cost attribution as direction
#3 — but the chaplain is yamlgraph's own automation, so this is the
introspection suite pointing at the project's *other* blind eye: we
measured the editor agents all day while the CLI agents ran unmetered.
Probe: do CLI sessions write chatSessions files, or is the tap the
only witness there too? Second seed: MAP.md declares territory states
— a stale map misleads worse than no map; should the map carry an
NC-393-style freshness marker (last-verified date per row) before it
earns trust as a resume-file?
