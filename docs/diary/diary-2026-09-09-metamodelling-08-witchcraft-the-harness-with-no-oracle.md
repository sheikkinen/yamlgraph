# Witchcraft: the harness with no oracle

**Date:** 2026-09-09
**Series:** metamodelling, part 8
**Trigger:** operator: "add one unexpected field to study … witchcraft".
**Context:** the six fields before this had real oracles of varying
latency. Witchcraft, in its trial form, had a complete harness and no
oracle at all: boundaries, procedure, skills, traceability, precedent,
learning loop, all present, all rigorous, none touching the world. It is
the series' negative control, and it turns out to test the one thing the
other fields could not: what a harness does when its checks cannot say
no.

## The field's harness, 1480–1700

| Field practice | Framework triple | What it actually was |
|---|---|---|
| *Malleus Maleficarum*, inquisitors' manuals | skill: procedural memory for a repeated task | encoded the first solution regardless of truth; reduced variance in convictions, not in error |
| Denunciation | claim entry | untyped; accusation and evidence in one grammar |
| Witch's mark | oracle | any blemish qualified: a criterion that matches everything (`junk_drawer`) |
| Water ordeal | oracle | float = guilty; sink = innocent and drowned. No fail state that the accused survives |
| Spectral evidence | oracle | visible only to the accuser; no third party could observe the witness |
| Confession under torture | oracle | the check shaped the generator's output to match the expected answer, then treated the match as confirmation |
| Trial record | traceability | meticulous. Every step cited its authority |
| Precedent | diary → Scripture | each conviction was evidence for the next; the learning loop ran on its own false positives |
| Execution | irreversible boundary | where the only real oracle (nothing changed afterwards) was never consulted |

Every row of part 1's table is filled. The harness passed its own
shape gate completely. That is the finding.

## The oracle that cannot say no

Take the water ordeal literally as a verifier. Its outputs are *guilty*
and *dead*. Both confirm the harness. An oracle with no observable fail
state is not a check; it is a ritual wearing a check's costume, and the
rigour of the surrounding procedure makes it worse, not better, because
rigour manufactures confidence.

Part 1's census seed asked which gates had fired and which had "only ever
been satisfied". This field says why that distinction is load-bearing. A
gate that has never returned fail is indistinguishable from an ordeal
until someone names the observation that *would* fail it and shows that
observation has occurred at least once.

## Torture as a prompt

Confession under torture is the cleanest picture in the series of an
oracle that contaminates its own input. The check pressures the
generator until the generator produces the answer the check expects, and
the match is recorded as verification. The LLM analogues are exact: a
judge prompted with the verdict the author wants; a test written after
the code and adjusted until green; a reviewer whose context contains the
author's narrative of why the work is correct. Doctrine here forbids
judging in the author's own session; Friedrich Spee's *Cautio
Criminalis* (1631) forbade it for the same reason, in the same shape:
torture produces confession from anyone, so confession under torture
witnesses the torture, not the crime.

## Spectral evidence and the unproduced witness

The accuser saw the spectre; nobody else could. Salem's court admitted
it, and the trials ended when Increase Mather's *Cases of Conscience*
(1692) got it excluded: a witness that only one party can observe is not
a witness. The LLM analogue is the generator's "I verified this" with no
artifact. The repository's cure already exists in form (demo-output.log,
a trace, a RED commit in the log); this field names the class: any
verification claim without a third-party-observable artifact is spectral.

## The learning loop on false positives

Precedent made each conviction evidence for the next, and the manuals
graduated the pattern. The harness *learned*, confidently and
cumulatively, from an oracle that could not fail. This is the danger the
other six fields did not show, because their oracles were real: rule 7
of the procedure (route failures to the harness) assumes the failure
signal is a failure. Where the oracle is fake, the loop amplifies noise
into doctrine.

This repository's graduation rule is *recurrence in the diary*. The
diary is written by the generator, about itself. Two recurrences by the
same generator reflecting on the same pattern are, in part 5's terms, one
origin. Graduation needs the recurrences to be independent observations,
or the Scripture grows the way the *Malleus* grew.

## How it ended

Not by a better witch-detector. The oracles were removed, from outside
the procedure, by people who challenged the premise rather than the
execution: Spee on torture, Mather on spectral evidence. The harness did
not reform itself through its own steps, because its own steps were the
problem. Scripture already has the entry: `unchallenged_premise`, "Judge
validates execution, not intent → need Red Hat: is the pain real?" This
field is the historical record of what happens over two centuries when
that hat is absent.

## Table for the field, reformed

| Boundary | Oracle | Action |
|---|---|---|
| any oracle proposed | name its fail output; cite the last time it returned it | reject oracles with no recorded fail |
| any check run | the check's inputs exclude the desired verdict | reject the verdict if the check saw it |
| any verification claimed | a third party can observe the artifact | treat unobservable witness as absent |
| any precedent graduated | recurrences traced to independent origins | one origin = one recurrence |
| the harness itself, periodically | someone outside asks whether the premise is real | amend or remove gates |

## What the field returns to the framework

1. **An oracle must be able to say no, and must have said it.** Fail
   state named, last fail cited. A gate that has only ever passed is an
   ordeal until proven otherwise.
2. **The check must not see the answer.** Any verifier whose inputs
   include the desired verdict, or the author's case for it, witnesses
   the pressure and not the claim.
3. **A witness is an artifact a third party can inspect.** Claims of
   verification are spectral.
4. **The learning loop is only as good as its oracle.** With a fake
   oracle, rule 7 graduates noise. Recurrence counts must be
   origin-traced before graduation.
5. **A corrupted harness is reformed from outside.** Its own procedure
   cannot find the fault in its own procedure.

## Traps

**`ordeal`.** An oracle with no observable fail state. Rigour around it
converts noise into certified conclusions.

**`confession_under_pressure`.** The verifier's inputs contain the
expected answer; the match is recorded as verification.

**`spectral_witness`.** "I checked" with nothing a third party can look
at.

**`graduated_false_positive`.** The learning loop promotes a pattern
whose every recurrence came from the oracle that could not fail.

## Heuristic

For every gate, name the observation that fails it and cite the last time
it did. For every verifier, confirm its inputs exclude the verdict. For
every recurrence counted toward graduation, trace it to an origin
independent of the one before.

**Seed:** run the *ordeal* test against this repository. Which pre-commit
hooks, guards, and CI gates have a recorded fail in ninety days, and
which have only ever passed? Then the harder one: of the Knowledge
Graph's graduated traps, how many rest on recurrences that are the same
generator reflecting on the same session class? The census from part 1
gains a column: *last fail*. A gate without one goes on the list for the
Red Hat.
