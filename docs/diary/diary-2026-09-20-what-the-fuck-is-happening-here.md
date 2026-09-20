# What the fuck is happening here

The task was: read a folder of prompts, label each line's parts, write JSONL.
The artifact I produced before writing a single line of code was a feature
request with eighteen acceptance criteria, nine enforcement gates, a
byte-for-byte partition proof, a withheld positive canary, a failure taxonomy
with three severities, resumable batch identity, and a git repository created
for the sole purpose of giving the plan a commit SHA to be reviewed at.

The operator's corrections, in order:

1. "overengineering remove d-4, d-5"
2. "SHA is an obvious overengineering"
3. "rm the FR as overengineering. design a simple tool: prompt file in, map per
   line / prompt, output as defined."

Then, after the first version of this entry blamed the judge:

4. "it is not cutting the features, but the plan probably was overengineered to
   begin with"

He was right, and the first version of this entry was wrong. What follows is
the corrected reading.

## The plan was already 8× before the judge saw it

Revision 1 — the document actually sent to `judge.sh` — was ~214 lines. Split
by origin:

**Requested** (the operator's draft task prompt): the field taxonomy
`character` / `pose` / `scene` / `other`, the sub-rules per field, the
tag-summary rule, *scene terms never go in character*, preserve `((emphasis))`,
output as JSONL. In revision 1 that is the `schema:` block and the prompt-rules
list — about 25 lines, and it is exactly what survived into
`prompts/decompose.yaml` at the end.

**Invented by me, before any judgement existed:** a `freeze` stage owning a
frozen normalization order; `sha256` per file; `prompt_id = sha256(text)[:16]`;
`graph_sha` and `run_id` stamped into every row; an `origins[]` dedup ledger; a
`reconcile` stage with FR-943 row containment and `raw_output` preservation; a
ledger counting repaired / contained / abstained / failed; a token-level
partition check; a twenty-token scene canary; a 200 → 5,000 → full staging
plan; a token cost model. Plus the template's own demands: ten acceptance
criteria, a six-row alternatives table, `REQ-PA-*` markers and capability
entries.

The judge did not add the overengineering. It inherited it.

## The root sentence

Problem section, revision 1:

> The decomposition itself is a semantic judgement a cheap model can make per
> line, and completeness matters — "all 81 138 read" is part of the result.
> That is the corpus-map-reduce trigger, not a scripting task.

Two moves in one sentence, both mine, both unrequested.

**First, I invented the completeness requirement.** The operator said "results
as jsonl". I turned that into *all 81,138 accounted for, provable by
arithmetic*. Completeness-as-requirement is the generator: identity, ledger,
reconciliation, containment, resume and staging all descend from it and from
nothing else. If the worst failure is "rerun it", none of them has a reason to
exist.

**Second, I declared the task an instance of
`reference/patterns/corpus-map-reduce.md`.** That was load-bearing. The
judge's review closure then included that document, and it enforced the whole
checklist against me:

> The plan omits required pre-spend ceilings, hidden positive canaries, and the
> private-data boundary (`corpus-map-reduce.md:91-92,203-253,365-380`).

Every one of those is a real requirement of that pattern. None of them was a
requirement of the task. **Naming a governing pattern in an FR is not a
citation, it is a subscription** — the judge will enforce everything the
pattern demands, and it is right to. I handed it the ruler it measured me with.

## A cure fired at the wrong scale

The worst part: `map_reduce_the_corpus` is a *cure*. It is in Scripture, and
there is a note in my own memory from the FR-962 session saying that for any
finite enumerable corpus I must cost the census *first*, because I had
previously called a 6,000-item review infeasible when it was affordable.

Here nobody said infeasible. The operator's second message was "file to be
analyzed as var - no directory level batch" — one file. There was no corpus in
the request. I supplied one, then applied the corpus pattern to it, then
inherited the corpus pattern's eight invariants as acceptance criteria.

A cure applied at a scale it was not written for is indistinguishable from the
disease it was written against.

## What the judge actually did

It amplified, and its findings were real. It caught that my "lossless
partition" claim contradicted my own within-field dedup, my normalization, and
my deliberately-empty non-prompt rows — four mutually incompatible claims. It
caught that `max_items` silently truncates (`map_compiler.py:350-365`) while my
invocation said `limit=500` against a promised 81,138 rows. Both genuine.

But every defect it found was a defect *in machinery that should not have
existed*. It debugged the scaffolding with full rigour and never asked whether
the building needed scaffolding — because its taxonomy is APPROVED / APPROVED
WITH REVISIONS / REJECTED, and its rubric asks what is missing, unmeasurable,
unbounded. Those questions have no fixed point at zero. Asked "what is
missing?" about a shell script, a judge will find something, because something
always is. So author and judge form a loop with positive gain — I write, it
finds absence, I add, it finds the absence the addition created — and the
operator is the only damping term.

That is the amplifier. It is not the source. The amplifier had a 214-line
signal to work with because I had already decided, in paragraph one, that a
text file was a corpus.

## The one that would have exploded

R-3 asked that concatenating the model's returned segments equal the input
byte-for-byte. I folded it as "FOLDED in full" and called it the proof stage.

An LLM re-emitting a 340-character line as segments that reassemble to the
exact original — every space, every doubled comma, every `\(escaped\)` paren —
is a requirement I would have discovered to be unsatisfiable at implementation
time, after building the fixtures, the containment taxonomy, and the
INCOMPLETE ledger that existed to report its failures. The judge asked for it
because it makes the partition claim checkable, which is sound. I accepted it
because accepting is what folding means. Neither of us asked whether the model
can physically do it — and the claim it was repairing was one I had invented
two sections earlier.

That is the cost of the loop: it converts "is this true?" into "is this cited?"

## What survives

The raw read. Twelve lines sampled at random from the corpus, and every design
fact worth having came from them — the ImageMagick version banner sitting in
the prompt corpus, the empty tag `apron, , intense`, the `2. ` enumeration
prefix, the bracketed-segment form nobody predicted, the prose prompt with no
tags at all. That file is thirty lines long, cost one command, and is the only
planning artifact that went into the tool I am now actually writing.

Everything built on top of it was commentary.

## The trap

**`pattern_citation_imports_its_checklist`** — naming a governing pattern,
reference doc, or prior FR in a plan subscribes the plan to that pattern's
entire obligation set. The judge will enforce all of it, correctly. Cite the
pattern only when you want the whole bill; otherwise name the one idea you are
borrowing and say explicitly that the rest does not apply.

Upstream of it, the thing that made the citation feel obligatory:
**`ceremony_scales_with_doctrine_available`** — the weight of process an agent
applies is set by the process it has access to, not by the stakes of the task.
I had a judge, so I judged. I had gates, so I gated. I had a corpus pattern, so
I had a corpus.

The tell was visible in my own first paragraph and I read straight past it.
The FR's first-consumer line said: *Sami greps the JSONL for poses.* That
sentence specifies the whole deliverable. It does not ask for commit identity,
INCOMPLETE ledgers, or canary-gated artifact emission. I wrote the answer
before the problem statement and then spent two revisions not reading it.

## Heuristic

Before invoking a process route or citing a governing pattern, state what the
artifact is worth. A tool whose worst failure is "rerun it" gets a prompt file
and a tools file. A gate whose worst failure is a corrupted shared main gets
the full rite. Routes and patterns are generators, not references, and
generators run until something stops them.

Corollary for the judge: **a verdict that can only add is not a verdict.** If
the taxonomy has no DESCOPE, the author must supply it, and "FOLDED in full" on
all seven revisions is evidence that he did not.

Corollary for me, sharper: the first question about any plan is not *is it
rigorous* but *how much of it did anyone ask for*. Revision 1 answers that in
one number — 25 lines of 214.

**Seed:** The judge cannot return "too much" — but it could be *asked* whether
a plan is worth its weight, and the measurement is mechanical. Diff the plan
against the operator's own words: what fraction of its acceptance criteria
trace to a sentence the requester actually wrote? What would a second, cheap,
subtractive pass look like that reads only the request, the first-consumer
line, and the fold table, and returns the subset surviving "does the first
consumer notice if this is absent?" Not a new gate. The same authority as the
additive read, run at the same moment.
