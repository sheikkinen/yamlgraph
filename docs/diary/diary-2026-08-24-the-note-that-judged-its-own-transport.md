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

---

## Addendum (same day): rejected and reverted

Everything above was written at GREEN, before the security review. The
operator's review request surfaced the fact that invalidated the arc:
**the repo is public**, and neither author, judge, nor enforcer ever
checked. The seed corpus staged for commit contained customer-confidential
material with no prior public baseline; its details are intentionally
omitted here. Both
commits reverted unpushed; FR-874 is now REJECTED precedent.

**The trap, precisely:** `threat_model_inherited_unverified` — every
stage validated against the threat model stated in the FR (peer-shared
repo) and none re-derived it from the world (`gh repo view` is one
call). The judgement even wrote the right correction (R-5: exclude
customer-private data) and the enforcer executed it against the wrong
adversary: I scanned for secret *values* when the leak class was
*facts*. A grep for tokens cannot identify a sensitive operational
fact — only a judgement over meaning can.

**The deeper defect the operator named:** the corpus itself is
unjudged — "random memory glimpses from the past." I built transport
for content that had never passed a gate. That is the pipe before the
pipeline: selective amnesia (judge each note: keep / redact / forget)
is the prerequisite mechanism, and it is a yamlgraph graph by nature —
per-note LLM judgement over a manifest is exactly the map-node shape
(`is_this_a_graph` fired late, again). Proposal filed to the chaplain
inbox.

**Revised heuristic:** the day's original heuristic ("second witness
converts a diary fact into a mechanism FR") survives, but gains a
guard: *the mechanism inherits every unverified premise of the
observation.* Verify the premises — especially visibility/audience —
before building the mechanism, not after.

**Seed (replacing the one above):** should the judge doctrine require
a "blast radius" line in every FR that moves data across a boundary —
stating audience, visibility, and worst-case reader — the way
measurement FRs require a raw-output read?

---

## Addendum 2: the successor shipped the same day

FR-875 (the curation graph the rejection demanded) was judged and
enforced within hours: collect/reconcile/apply as tested code, the
judge stage authored through the sole route, fixture smoke green on
first pass. Two details worth recording. First, the FR-875 judge
caught *me* re-committing the FR-874 sin at smaller scale: my draft's
blast-radius line claimed "tmp/ only" while the map node ships every
note body to a cloud provider — the egress was in plain sight and the
author's eye slid off it again. The R-1 gate (provider approval as a
recorded human line) is the mechanized fix. Second, the fixture smoke
validated the mechanism the honest way: the planted sensitive note —
synthetic customer-confidential operational details, the
exact FR-874 leak classes — came back `redact` with a correct
rationale on the first run. The graph that exists because pattern
scanning missed a fact-leak was witnessed catching a fact-leak.

**Seed 2:** apply's drift refusal is validate-all-then-apply-all — an
all-or-nothing transaction over the memory root. The same shape
(frozen manifest → judged plan → hash-gated execution) fits any
agent-driven destructive operation: worktree cleanup, branch pruning,
config migration. Is there a general "gated apply" primitive hiding
here, or is three instances (FR-868, FR-875, next) the graduation
bar?

---

## Addendum 3: whose memories are these — the recall-time value law

The operator read the first real disposition and asked the right
question: the corpus is *agent* memory, so the curation policy is
mine to state. Introspecting on how I actually use these notes
exposed what the judge cannot see: **a note's value is determined at
recall time, not at write time.** I do not browse this corpus; I hit
it by filename when a situation matches (judge-sh-uv-fallback fired
twice today and paid for itself both times). The filename is the
index; the trigger-recognizability of the name is most of the value;
the content is read only after the name matches. A content-only
judge — which is what FR-875 built — measures plausible durability,
not fired-ness. That is why it rated 56/57 fresh: it judges text,
and staleness lives in the world, not the text.

Consequences, stated as the policy I want: hygiene verdicts are
keep / compress / forget-with-tombstone, where "compress" is redact
under a machine-local premise (same schema, the premise re-scopes the
meaning — no graph change needed); forgetting requires a tombstone
line (date, name, reason, superseded-by) because negative knowledge
is case law — the graveyard doctrine applied to my own memory; and
forget is earned only by mechanization (cure graduated to
Scripture/code/test) or impossibility of recurrence, never by mere
age. The missing instrument is a fire-count: recall events are
observable (memory tool reads) but unrecorded — incident_density_
ranking wants to apply here and cannot yet.

**Seed 3:** the reception hierarchy (skills → memory → READMEs →
scripts) governs *discovery*; the tombstone index would be memory
about memory — does it belong as a note in the corpus it indexes
(self-reference, curated by the same graph) or outside it? And: can
the SessionStart hook log which memory files each session actually
reads, making the fire-count a query instead of a self-report?

---

## Addendum 4: the gate the operator killed

The operator challenged the C-6 sign-off directly: "superficial at
best — long document for a manual review", and the disposition itself
is "more forecasting". Both charges held against the record — the
human-skims doctrine, and the fact that neither real catch of the day
came from document review. FR-878 (judged, enforced same day) is the
structural answer: **remove irreversibility instead of approving
through it** (archive + restore + tombstones), **validate forecasts by
outcome** (re-derivation advisory: a re-created forgotten note is the
mechanical "forecast was wrong" signal, with a restore), and **tier
human attention to residual irreversibility** (none / delegated /
structured question / non-delegable for export). The judge added the
detail that survives contact: `premise_kind` as a validated enum
failing closed to the strictest tier — never substring-matching prose
— and the tombstone index protected from curating itself away.

Heuristic, candidate for graduation: *a human gate that reviews a
document is theatre; a human gate that answers a decision-shaped
question at an irreversibility boundary is control. When a gate feels
superficial, first try to delete the irreversibility it guards.*

**Seed 4:** tier-1 standing delegation is now a machine-checked string
citing this FR. Delegations accumulate; nothing today lists or expires
them. Is a delegation registry (who may sign what, granted when,
witnessed where) the next `_tombstones.md` — case law about authority
instead of about forgetting?

---

## Addendum 5: the marker that almost cried wolf

FR-877 closed the family: detection mechanical, execution deliberate.
The judge's R-1 catch deserves its own line — my draft marker kept the
pre-apply manifest as the baseline, so the very first advisory after a
forget-curation would have counted the intentional forgets as deleted
drift and fired "consider a hygiene pass" on the heels of one. An
advisory that false-fires immediately after the action it recommends
is worse than none: it trains the reader to skim past it — the same
attention-erosion that killed the C-6 sign-off. The cure was to define
the baseline as the *post-apply live corpus* (enumerate what exists,
not what was planned) — `read_raw_output_first` applied to state
design: record the world, not the intention. Witnessed by
`test_forget_run_yields_zero_immediate_drift`.

**Seed 5:** the advisory's threshold (5) is a guess — a
`threshold_encodes_forecast` in miniature. When field data exists
(how many drifted notes typically precede a curation-worthy pass?),
the number should be re-derived from the record, not defended.
