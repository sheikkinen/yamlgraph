# The Vocabulary I Searched With

**Date:** 2026-09-04
**FR:** FR-981 phased summary pattern (planning record merged as #580)
**Session:** the FR author's own; judgement and research ran through their sole routes

## What happened

An operator described a production shape: long clinical visit notes reduced to
a per-visit brief, and the patient's lifetime summary built from the briefs.
Is the pattern documented? I swept `reference/patterns/`, `reference/*.md`,
and `examples/demos/`, found `book-summary`, `corpus-map-reduce`, and
`compaction`, and answered: undocumented, and its three distinguishing
properties — durable substitutive brief, subject axis, incremental cost — are
"precedented zero times" in this repository.

That answer survived a five-persona research route, a rejection, a second
judgement, seventeen acceptance criteria, and a merge to `main`.

Then, an hour after the merge, asked to "check patterns", I opened
`examples/demos/wiki-memory/README.md`: *inter-run state accumulation with a
deterministic integrity gate*. One YAML file per page under `wiki/<id>.yaml`,
grown across runs, read back through a `data_files` glob, with a Python gate
that refuses any page whose references do not resolve. Then
`examples/novel_fandom/`: `canon/character/*.yaml`, `canon/event/*.yaml` — a
typed, entity-keyed, durable store with a no-orphan-reference gate *and* a
lane-immutability rule that forbids the LLM overwriting static pages.

The durable per-item store is precedented twice. The deterministic
"every claim resolves to a stored artifact" gate — which I wrote into the
pattern document as invariant 5 and into the FR as a novel testable
contract — is precedented twice. I had graded both as zero.

## The trap

I searched with the vocabulary of the answer I already had. "Brief."
"Summary." "Digest." "Rollup." Every search I ran, manual and mechanical,
was a search for words. `wiki-memory` and `novel_fandom` share no word with
the clinical shape; they share its *problem* — how does a graph keep typed
artifacts across runs without the model corrupting them.

The doctrine names this exactly, about `prior_art.py`: retrieval "finds prior
art that shares vocabulary and misses prior art that shares a problem, so the
block is a floor on the search, never a ceiling." I quoted that sentence into
the FR to disposition the route's retrieval hits. I quoted it while committing
the error it describes. The tool's blind spot was documented; I had simply
assumed it was the tool's, not mine.

`false_duplicate` has an inverse and this is it. That trap says syntactic
similarity is not semantic equivalence — four "brief" FRs matched my nouns and
meant nothing. Its mirror is worse, because it is silent: syntactic
*difference* is not semantic difference, and nothing fires when you miss.

The cure is not a better grep. It is a second search keyed on mechanism rather
than subject: before claiming a mechanism is unprecedented, describe it
without any noun from its domain — "one file per key, written by the graph,
read by a later run, validated by Python" — and search *that*. Both witnesses
answer it in one query.

## Three smaller ones

**Borrowed optimizations do not inherit their purpose.** The librarian found
CLIN-SUMM; I adopted its Jaccard near-duplicate filter and wrote that a
witness omitting it "teaches the pattern wrong". The judge deleted it: skipping
a near-identical record means the required N+1 run can make *zero* brief calls,
silently voiding the one proof the demo exists to produce. The filter is
correct in the pattern and wrong in the witness. An optimization imported from
a system with different purposes must be re-derived against the purpose here,
not carried across with its rationale intact.

**A dissent can be right about the defect and wrong about the reason.** Three
of five personas voted to withdraw the pattern documentation on the grounds
of "a single unverifiable anecdote". The librarian, running in parallel and
invisible to them, found CLIN-SUMM and POMR — the premise was false. But the
subtractionist's *principle* held, and the fold kept it as a standing
condition. Refuting a premise is not refuting a finding.

**The convention I broke was a test away.** `FR-981-pilot-raw-read.md` parsed
as a second primary FR numbered 981 and CI failed. `feature-requests/evidence/`
already existed, with two FR-959 files in it. I invented a location instead of
looking at where the repository already puts evidence.

## Heuristic

**search_the_mechanism_not_the_subject:** before writing "precedented zero
times", restate the mechanism with every domain noun stripped out and search
that sentence. Vocabulary search finds what shares your words; a claim of
novelty is a claim about problems, and problems hide under other words.

## Consequences owed

FR-981 is merged and overstates novelty. Owed: an amendment citing
`wiki-memory` (FR-120/625/628/629) and `novel_fandom` (FR-655) as prior art
for the store and the reference gate, narrowing the FR's novelty claim to
substitution, subject-scoped rollup, version invalidation, and incremental
cost — which remain genuinely unexercised. The implementation should reuse
`write_data_file` + `data_files` rather than hand-rolling a store.

**Seed:** the two store witnesses were found by reading demo READMEs one line
at a time, which is the `impossibly_large_sequential_task` shape this project
has a census for. If a mechanism-keyed index over every committed graph
existed — "writes files a later run reads", "gates model output with Python",
"fans out then reduces" — would a novelty claim ever again survive a single
session? And what else is currently documented as absent because nobody
searched without its nouns?
