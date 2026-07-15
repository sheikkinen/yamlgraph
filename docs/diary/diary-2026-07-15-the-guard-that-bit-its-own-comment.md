# 2026-07-15 — The guard that bit its own comment

**Context:** FR-735 enforce: making the WebLLM spike page
self-evidencing (console records, byte-fidelity downloads, session
evidence.md in F1 tally shape).

**The wrinkle worth keeping:** the F3 lexical guard asserts
`.message.content` appears exactly once in the page — the single-read
invariant that guarantees the Blob and the DOM show the same bytes. My
GREEN failed it because a *comment* explaining F3 mentioned the
property name. The guard cannot distinguish code from prose, and that
crudeness is the point: I reworded the comment rather than weakening
the test. A lexical invariant that forces even documentation to stay
out of its namespace is annoying exactly once, and then it is
load-bearing — the next person who adds a second read for a
"convenience variable" gets caught by the same tripwire, comment or
code. Cheap guards earn their keep by being indiscriminate.

**The design insight:** run 1's whitespace flood (FR-731) taught that
an instrument's failure-path ergonomics matter more than its
success-path polish — the degenerate output is the one you must
capture verbatim, and it is precisely the one that copy-from-DOM
mangles. The general shape: **build the evidence channel for the
pathological case; the healthy case rides along free.** Same law as
ninchat's forensic route artifacts rendering on abort-with-partial-
route: the crash run is the run you need rendered.

**Protocol note:** the F2 judgement call — cure session mortality with
honest labeling (`failures: N/M`, session id) instead of persistence —
kept the purge list intact by making incompleteness *visible* rather
than impossible. Labeling over storage is the cheaper honesty.

**Seed:** three FRs now share one instrument (FR-731 spike, FR-735
ergonomics, the pending 10-run tally). When the tally completes, the
evidence.md the page emits becomes the spike-evidence.md the FR
demands — the instrument writes its own acceptance artifact. Is that
the general endgame for AC evidence: every manual protocol eventually
absorbed into the artifact-under-test until the human's only job is
judgement? Where is the line where self-evidencing becomes
self-grading — the gate_checks_shape_not_substance trap wearing a
nicer costume?
