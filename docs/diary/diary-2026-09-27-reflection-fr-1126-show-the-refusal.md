# Reflection: FR-1126 — show the refusal, not just the cure

**Date:** 2026-09-27
**FR:** FR-1126 (ramp_rtm as the FR-1125 showcase)

## What happened

By the time FR-1125 merged, the repository had a rule, a reference
section, twenty-six migrated prompts and three live proofs, and the
operator still asked "how does one use Anthropic now?" and "is there an
example?" Every artifact taught the cure; none showed the refusal, and
none was labelled as the place to look. `ramp_rtm` had everything a
showcase needs (a committed fixture, the built-in provider default, a
fresh live log) and no sentence saying so.

The judge added three revisions that were all about the same thing:
what "exact" means. The refusal reproduction had to set
`PROVIDER=anthropic` because a host `.env` had already changed that
classification once today; the live command had to set the model
because "two calls on haiku" was an environment default dressed as a
fact; and the README's quoted diagnostic had to *equal* the linter's
message after whitespace normalisation, not share an eighty-character
prefix. My first test then rejected the diagnostic for containing
`{...}`, which is the linter's own legitimate text. The guard against
truncation had itself been a shape check.

## Trap

`documentation_without_demonstration`: a rule that is documented,
enforced and migrated but never *shown* leaves the reader to
reconstruct the failure from prose. Commandment 2 names it; the day's
work had satisfied every gate around it and skipped the demonstration.

## Heuristic

For any new refusal, the demo is the pair: the exact message a reader
will see, reproduced by a command that costs nothing, beside the
working form and a real run of it. Pin every environment-sensitive
input in the command the reader will paste; the value the framework
resolves by default is not the value the reader's host resolves. And
when a test guards against truncation, assert equality with the source
of truth, not the absence of a symbol.

**Seed:** The E017 diagnostic is now quoted in a README and asserted
equal to the linter's output. Should each linter code own a canonical
"showcase" fixture, a demo directory named in `checks_schema.py` and
its siblings, so that renaming a message anywhere fails one test that
points at the README to update, instead of silently leaving the
documentation behind?
