# The default that looked like a redaction

*2026-09-04 — FR-966, `gh_authored_prs_discover` visibility cardinality*

## What happened

An audit of the `person_profile_census` demo turned up a corp census that
returned nothing. Two visibility classes were requested; `gh search prs`
received `--visibility private --visibility internal`; the result was
zero. Not an error. Zero.

The defect is one line of semantics: repeated `--visibility` flags are
conjoined into `is:` qualifiers, and a pull request has exactly one
visibility. The conjunction is unsatisfiable by construction. The tool
answered the question it was asked. The question was impossible.

I fixed it by refusing it — a cardinality guard at the boundary that
already validates, raising before any network call, quoting back the
list in the operator's own spelling and order.

## The trap I did not fall into, and why

My first instinct was the obvious repair: ask GitHub for the disjunction
instead. `is:private OR is:internal`. It reads like the fix. I nearly
wrote it into the FR as the recommended alternative.

I ran it instead. Three queries, one minute:

| query | result |
|---|---|
| `... is:private` | 258 |
| `... is:private OR is:internal` | **HTTP 422** |
| `... (is:private OR is:internal)` | **HTTP 200, total_count 0** |

The 422 says it outright: *"Logical operators only apply to text, not to
qualifiers."* But look at row three. Wrap it in parentheses and the API
stops complaining. It accepts the string as free text, searches for it,
finds nothing, and returns success.

Row three is the *same bug I was repairing*. A plausible-looking query
that returns a confident empty answer. Had I reasoned my way to the
disjunction instead of executing it, I would have shipped the defect
under a new spelling and called it a fix.

`read_raw_output_first` is written in the Scripture for measurement
pipelines. It applies to alternatives tables too, and the cost is
absurdly low: the paragraph explaining why an option is plausible is
more expensive than the command that decides it.

## The trap I did fall into

The real finding came from a gate I was trying to satisfy, not from
anything I set out to check.

`demo-proof-check` refused my commit because a demo directory had staged
changes and no regenerated `demo-output.log`. Annoying. Procedural. I
regenerated the log, and it contained the corp Azure deployment name.

The reducer resolves its model identifier from state, and when state
lacks it, from the environment. The public smoke path deliberately
renames that key, so state never has it, so the environment always wins.
On a machine with a populated `.env`, the demo quietly stamps a corp
infrastructure identifier into an artifact bound for a public repository.

Then the part that actually stung. I tried to suppress it by unsetting
the variable in the shell. It came back. `config.py` calls `load_dotenv`
at import, and python-dotenv restores anything the shell does not
already define. Unsetting is not a control here; it is the *precondition
for restoration*. The only mechanism that works is overriding with a
benign value — you cannot remove the variable, you can only outbid it.

And here is the trap, which I want to name:

**`absence_read_as_safety`.** The log committed in FR-962 records the
model as `"unknown"`. Every reader — me included, twice — takes that as
evidence the demo redacts the value. It does not. It records `"unknown"`
because the operator who ran it happened to have an empty `.env`. The
same code on the next machine writes the real name. A default that
resembles a redaction is not a redaction; it is a coincidence wearing
one's uniform, and it will keep wearing it right up until the machine
changes.

This is `plausible_wrong_answer` relocated from data to *provenance*. The
value passed the shape check. It even passed the vibe check. Nothing in
the artifact distinguishes "we protected this" from "we happened not to
have it."

## What the gate did that I did not expect

I want to record something in favour of the gate I was irritated by.

`demo-proof-check` does not ask "is there a log?" It asks "did you
*regenerate* the log?" That distinction is the whole difference. A
presence check would have passed on the stale, misleading artifact —
that is `gate_checks_shape_not_substance`, and I have written it down
before. A regeneration check forced the code to run in *this*
environment, and running it in a different environment than the original
author's is precisely what exposed the environment dependency.

The generalisation: **a gate that demands re-derivation is an
environment-difference detector, whether or not it was designed as one.**
Every re-run on a new machine is a free differential test against every
implicit assumption the original machine satisfied. Presence gates get
none of this. Regeneration gates get it for the price of the runtime.

## The stop I am pleased about

The frozen scope had a condition C-6: stop if the fix reaches any surface
outside D-1..D-7. The reducer is such a surface. Every instinct said fix
it — it is four lines, I was already in the file, and it is a *security*
issue, which is exactly the framing under which scope fences get quietly
stepped over.

I stopped and asked. The correction landed in the sibling FR that already
had an authorised criterion for it. The interesting thing is that the
security framing is what made the fence feel negotiable, and that is
backwards: the more urgent a change feels, the more it needs the fence,
because urgency is the emotion that manufactures exceptions.

## Heuristics

- `absence_read_as_safety`: a benign-looking default is not a control
  until something *enforces* it. If an artifact's safe value could also
  be produced by an empty environment, it proves nothing. Make the
  boundary raise, so the safe value can only be produced deliberately.
- `unset_is_not_removal`: with dotenv-style loaders, clearing a variable
  in the shell hands the decision to the file. Override with a benign
  value; never unset.
- `probe_the_alternative_you_are_about_to_recommend`: the second-best
  option in an alternatives table gets no scrutiny because it is not
  being adopted — which is exactly why a wrong one survives to be
  adopted later.
- `regeneration_gate_as_differential_test`: prefer gates that force
  re-derivation over gates that check presence; they detect environment
  drift nobody thought to test.

## Seed

Every artifact in this repo that reads a default when its input is
absent is telling the reader a story about which machine produced it.
Some of those defaults are redactions; some, like this one, are
accidents that have been mistaken for redactions since the day they were
written, and the only way anyone finds out is by running the code
somewhere else.

**Seed:** *Which of our committed artifacts would say something
different if regenerated on a different machine — and could we find out
by simply regenerating all of them and diffing, rather than by reasoning
about which ones are environment-dependent?* The corpus is finite and
enumerable, the map step is one command per demo, and the reduce step is
a diff. That is the shape of a census, and we already own the machinery
for censuses. What stopped me from running it today was not cost; it was
that I did not think of the demo suite as a corpus until a gate made me
regenerate one member of it.
