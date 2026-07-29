# The Skill That Was Only a Shadow

**Date:** 2026-07-29
**Context:** FR-765 addendum 2 — operator-directed retirement of the `author-graph` / `author-prompt` syntax skills

## What happened

Hours after FR-765 shipped the `graph-authoring` workflow skill "composing
author-graph and author-prompt as syntax references" (AC-03, judged and
frozen), the operator ordered both composed skills deleted. The layer that
round 1 was explicitly built *on top of* turned out to be the layer made
obsolete *by* it: once the workflow skill pointed agents at the right
moment to consult syntax, the intermediary skills were just lossy caches
of `reference/graph-yaml.md` and `reference/prompt-yaml.md` — 459 lines
whose only defense was "what if someone asks?"

## The trap

**Distillation accretes provenance.** The preservation audit found the
skills were ~95% condensed duplication — but the remaining 5% was the
most expensive knowledge in either file: the FR-744 `path:` vs `module:`
field incident, the `messages:` role-list KeyError, and the five-clause
prompt contract paid for by FR-581–587. None of it lived in the reference
docs the skills claimed to be distillations of. A summary that is easier
to edit than its source becomes the *de facto* canonical copy, and the
canon silently starves. Deleting the summary without the audit would have
destroyed the only copy of knowledge bought with five failed FRs.

## The heuristic

**Retire a document only after diffing it against its claimed source —
migrate the residue first.** The residue is where the incidents live,
because incidents get recorded wherever the author happens to be
standing, not where the doctrine says they belong. (This is
`normalize at the boundary` for documentation: field incidents entered
at the skill layer instead of the reference layer, and manifested as
drift.)

Also a small confirmation of `growth_as_default`'s inverse: the healthy
move after shipping a composition layer is often to prune the layer it
replaced, not to keep both "for discoverability." Two entry points to
the same syntax is a fork, not a convenience.

## Seed

When an incident is recorded in a derived document (skill, README,
tutorial) rather than its canonical reference, what mechanical check
could catch the misfiled knowledge at commit time — a "derived docs may
not contain FR-XXX incident citations absent from their canonical
source" lint?
