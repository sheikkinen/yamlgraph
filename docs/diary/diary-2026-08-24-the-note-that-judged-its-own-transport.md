# 2026-08-24 — The note that judged its own transport

**Context:** FR-874 enforcement — cross-device agent memory sync. The
operator's one-line introspection ("intel is not being shared between
peers") turned out to be the second independent witness of a fact the
2026-07-16 diary had already proven by filesystem inspection: "repo
memory does not live in the repo." Two occurrences → graduation bar →
this time a mechanism, not another observation.

**The trap: observation without a consumer.** The first discovery
(2026-07-16) produced a correct diary entry and a correct doctrine note
(`where-repo-notes-live`) — and no mechanism. The finding was filed as
*knowledge* when it was actually a *defect*: name-implies-portability,
the "repo" scope silently machine-local. What made the second occurrence
different was not better evidence but a named first consumer: the agent
on the operator's other device, at SessionStart, re-deriving facts a
sibling already paid for. `would_you_use_this` answered itself.

**The recursion that paid the toll.** Mid-enforcement, the judge route
failed on the known `judge.sh` uv-fallback breakage — and the cure came
from `/memories/repo/judge-sh-uv-fallback-broken.md`, a machine-local
note that would have been invisible on any other device. The FR being
judged was justified, live, by the failure mode it exists to fix. That
note is now in the seed corpus it argued for.

**Design notes that survived the judge.** R-2 killed mtime comparison
before it was written (mtimes lie across git checkout and devices; the
base-hash manifest is the boundary normalization). R-1 killed the
denylist framing of `shared/` — a privacy default should be allowlist
(explicit promotion) because the failure mode of a denylist is silent
leak, and the failure mode of an allowlist is silence. R-4 is
`detection_without_enforcement`'s cousin: fail-open without evidence is
a success-shaped failure.

**Heuristic:** *second witness converts a diary fact into a mechanism
FR.* A recorded observation that recurs has proven both its truth and
that recording it did not cure it — the correct response to recurrence
is never a better-worded note.

**Seed:** the store now carries repo-scope intel across devices — but
the *diary graduation pipeline* (`seeds.diary_graduation_pipeline`)
and this store are converging on the same shape: notes → recurrence →
promotion → committed artifact. Should the memory-sync manifest track
recurrence counts per note, making graduation to Scripture a query
(`notes seen on N devices, imported M times`) instead of a manual
sweep?
