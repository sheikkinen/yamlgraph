# Building a history oracle: one anchor in three drifted

**Date:** 2026-09-09
**Series:** metamodelling, part 11 (applied)
**Trigger:** operator, over three turns: "how would you build a high
school chapters and lessons about history of rome" → "trace contemporary
sources. i.e. how do we know" → "reflect on the process — building a
history oracle".
**Context:** the series (parts 1–10, PR #646) described a harness for
fields without compilers. This entry records the first attempt to build
one: a source ledger for Roman history, produced from memory, then
checked against the text it cited.

## What was built

A curriculum harness (objectives → assessment items → lessons, claims
typed fact / interpretation / legend / counterfactual, student-model and
historian-model readers with input closure), then chapter 1's content:
an evidence ledger by period with the column that matters for a past
that cannot be re-run, **latency** — years from event to earliest
surviving witness. Kingdom 500–700; early Republic 300–500; Punic Wars
20–200 (Polybius); late Republic 0–250 (Cicero, Caesar); Principate
0–200; a second ledger for the transmission of the texts themselves
(Tacitus *Annals* 1–6 in one manuscript; 35 of Livy's 142 books).

## The check

Before reflecting, one fetch: the three Polybius anchors against the
LacusCurtius Loeb text.

| Anchor as written | Found | Result |
|---|---|---|
| 3.22, treaties Rome–Carthage, "he read the bronzes" | 3.22 has the treaty text; the bronze tablets "in the treasury of the Quaestors beside the temple of Jupiter Capitolinus" are at 3.26.1 | drift: right claim, wrong section |
| 3.33, Hannibal's inscription at Lacinium | 3.33.17–18, verbatim | correct |
| 3.56, army numbers from the same inscription | 3.56.4 | correct |

One in three. One fetch, about a minute. That pair — 33 % drift, one
minute per anchor — is the cost/yield number part 10 asked for before
building a claim-typer. It says: run it.

The same page held two witnesses the ledger had not used. Polybius
3.9.4–5 on Fabius Pictor: readers who consider "that he was a
contemporary and a Roman senator, at once accept all he says as worthy
of credit … but readers should in most cases test his statements by
reference to the actual facts." Contemporaneity ≠ credibility, stated
by a contemporary, inside the source. And 3.20.5 dismissing Chaereas and
Sosylus — Hannibal's own companions — as "the gossip of a barber's
shop": the surviving pro-Roman witness discrediting the lost
pro-Carthaginian ones. The record's asymmetry is visible inside the
record.

## What building it showed

**The oracle is structural, not truth-valued.** It never returns
"Caesar crossed the Rubicon: true". It returns: type *fact*; earliest
witness *Caesar, Cicero's letters*; latency *0*; origins *≥ 2*;
transmission *wide*; verdict *fact, contemporary, partisan*. GRADE for
the past — the rung stamped on the claim (part 6). Building it is a
table join: claim → passage → author → (floruit, agenda, manuscript
width). The data exist (Perseus, LacusCurtius, PHI epigraphy, Jacoby's
fragments). The missing link is sentence → passage, which is
Quellenforschung, which is a corpus-map-reduce.

**Structure was method; cells were memory.** The columns came from the
framework and are sound. The cell contents came from the weights the
series says cannot verify themselves, and 1 in 3 checked anchors
drifted. Method and fact shared one table with no visual difference:
`type_costume` at the level of layout. A built oracle fixes it for free
— every cell carries a URL and a verified flag. A chat table cannot.

**Latency is necessary, not sufficient.** Livy at 200 years using
Polybius at 20 beats Caesar at 0 on independence. The column that
matters is *chain latency* — the distance of the earliest source in the
citation chain, not of the surviving narrator. Not modelled. Harder
join.

**Selection was mine and untraced.** The ledger reproduces the
Anglophone classics syllabus, the origin of the training's Rome.
Carthaginian, provincial, and non-elite voices appear only where that
syllabus already placed them. A built oracle needs a coverage check
against the *catalogue* of surviving sources, not against recall.

**The lesson and the oracle are one artifact.** Chapter 1, "how do we
know", *is* the ledger. Teaching source criticism is teaching students
to compute the rung. In code the analogue holds: TDD is both the check
and the craft. Where the oracle is structural, curriculum and verifier
converge, which is the strongest argument for building it as a tool
rather than writing it as prose.

## Process finding

Three consecutive turns produced three fluent artifacts about
verification; none ran a check until the fourth. Part 10's heuristic —
run the artifact through its own rules once — was written and not
applied one turn later. That is not a heuristic failure. It is the
expected decay of a prompt-level patch, and the series predicted it: the
cure belongs in the route, not the doctrine. A fact-ledger response
without a fetch-verify pass is a draft and should say so.

## Minimal built oracle

- **Input:** claim, period.
- **Map:** retrieve candidate passages; classify witness (material /
  literary / documentary); author floruit → latency; stated sources →
  chain latency; agenda from a curated author table; manuscript width
  from a curated table; count independent origins.
- **Reduce:** `{type, earliest_witness, latency, chain_latency, origins,
  transmission, verdict}` per claim, with URL and verified flag.
- **RED:** a gold set of ~30 claims with known verdicts (Romulus →
  legend; Rubicon → fact, contemporary; Nero's fiddle → later
  embellishment, Tacitus places him at Antium; 476 → contested). It must
  misclassify sometimes on held-out claims, or it is an ordeal.

## Traps

**`method_and_memory_in_one_table`.** The sound part (columns, from
method) and the unverified part (cells, from recall) rendered
identically. The reader cannot see which to trust; the author cannot
either.

**`recall_as_catalogue`.** Enumerating "the sources" from memory and
calling the enumeration complete. Recall returns the syllabus, not the
archive.

## Heuristic

For any generated fact-ledger, check one anchor per source before
publishing and record the drift rate; below 100 % verified, label the
table a draft. Build the oracle when the ledger will be produced twice.

**Seed:** the 33 %-in-one-minute pair is the estimate for the
claim-typer over the ten metamodelling entries (part 10, step 2). Run
the hand pass; if the drift rate on the series' own anchors is in the
same range, the claim-typer graph has its first two corpora and its
first consumer.
