# Reflection: FR-1057 — the census that could not see its own subject

**FR:** FR-1057 Prompt template dialect is decided at three different granularities
**Date:** 2026-09-23

## The trap: measuring a grammar defect with the defective grammar

The FR's Alternatives section carried a census — a real one, executed, with
numbers a probe produced, exactly as `alternatives-as-probes` demands. It
classified 1064 tracked YAML files by dialect and reported **1 MIXED** file:
one live incident, tidy, repairable in a single edit. AC-11 was written to
match: lint the corpus, expect zero findings after *the* repair.

The census classifier used `\{(\w+)\}`.

That regex is **defect D2**. It is the exact pattern the FR exists to delete,
named in its own Problem section as "narrower than `str.format`'s field
grammar". It cannot see `{synopsis.title}`, because of the dot. It cannot see
`{"chapters": []}`, because of the quotes. So the instrument I used to size
the problem was blind to most of the problem — not by accident of tuning, but
by the same construction the FR was written to condemn.

Running the corpus lint with the *shipped* parser returned 6 findings across 4
defect sites in 3 files. Among them: `examples/dungeon_master/prompts/author_plot_plan.yaml`,
whose `system` message is literal JSON with no Jinja markers. On base code it
raises `KeyError '\n  "agents"'` before any LLM call. Two nodes use it. That
graph — the FR-561/562/563 plot lane — has not been able to run since it
landed, and no test, no lint rule, and no census noticed.

The FR said D1 had no committed instance. D1 was the most broken thing in the
repository.

## Why it survived judgement

The judgement interrogated the census hard — R-4 corrected it once already, for
walking the filesystem instead of the git index. Both author and judge treated
"the census was executed" as the property that mattered. Neither asked what
grammar the classifier used, even though the FR's own D2 section printed that
grammar three paragraphs earlier and called it the bug.

This is `contract_encodes_wrong_model` in miniature: the FR, the judgement, and
the AC all agreed, and all three inherited one premise from the same place.
Agreement among documents that share an input is one observation.

It is also `threshold_encodes_forecast`, which the Scripture already names:
AC-11's "zero findings" was not testing the fix, it was testing my forecast
that exactly one defect existed. The gate would have passed either way — with
one repair or with three — and the number it would have revealed was the number
I most needed to see.

## The heuristic

**A census is only as good as its grammar. When the defect under measurement
*is* a parsing defect, the measuring instrument must be the new parser, never
the old one.** More generally: before quoting a census, name the classifier
and check it is not itself an instance of the thing being counted.

Corollary, earned twice in this FR: running the new check over the entire
committed corpus is a different act from running it over fixtures. It found the
live D1 crash, two false-positive classes in my own E014, and a regression
(`extract_variables` suddenly demanding a `pred` variable) that 6907 unit tests
did not see. Fixtures test what I imagined; the corpus tests what exists.

## The coda: a gate that asked the right question

The three `novel_generator` repairs then hit `check_demo_proof.sh`, which wants
a successful `demo-output.log` for any changed demo. I could not produce one:
that demo also carries the fifth defect shape — `{synopsis.title}` in a
non-Jinja message, a `getattr` against a dict that can never render — which the
judgement had frozen out of scope.

My instinct was to widen scope by one file. I asked instead, and the operator's
answer was neither of the options I had drafted: move the demo to a private
project tree and delete it from the repository. The demo had no capability, no
`ARCHITECTURE.md` entry, no README line, no `demo.sh` registration — fourteen
files and one integration test, claimed by nothing. It had been quietly broken
and nobody had noticed, which is the only real evidence a demo is not being
read.

This is `growth_as_default` answered correctly: the cheapest resolution to "a
gate blocks my change" was not to satisfy the gate and not to widen the change,
but to remove the thing the gate was protecting, because it turned out nobody
was standing behind it. The gate did its job exactly — it refused to let a
broken demo be edited into looking maintained.

## Seed:

The Scripture has `read_raw_output_first` for LLM stages — read the artifact
before measuring it. This FR suggests a sibling for static analysis:
**run the new checker over the whole committed corpus before believing the FR's
census** — and when the two disagree, the FR is wrong, not the corpus. Should
that be a mechanical step in the enforce phase for any FR that adds a lint
rule: a required "corpus delta" line recording what the new rule finds that the
old instrument missed? The number is one command away, and in this case it was
the difference between a tidy one-file fix and discovering a whole demo lane
had been dead for weeks.
