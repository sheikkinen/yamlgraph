# The tests that were cited but never written

*2026-09-04 — FR-967 D-1, halted at the third violation*

## The finding

`person_profile_census` shipped on 2026-09-02 with seventeen acceptance
criteria, all unchecked, and zero tests. Ten of those criteria name a
test explicitly. No file under `tests/` mentions the demo, its reducer,
its row schema, or its discovery adapter.

Its sibling, `repo_census`, shipped with 460 lines of witnesses covering
the same surfaces — the same author, the same week, the same shape of
demo. One has a test suite; the other has seventeen sentences claiming
it does.

That difference is the whole entry. It was not a capability gap and not
a knowledge gap. The witnesses were written when something checked, and
were not written when nothing did.

## What made it invisible

Every gate passed on the way in.

- The demo-proof gate saw a `demo-output.log` and was satisfied.
- The requirement-witness audit reads the REQ registry; the demo
  registered no REQ, so the audit was structurally blind to it.
- CAP-116 does require acceptance tests before enforce — but only inside
  the chaplain watcher runtime, and this FR was enforced outside it.
- Nothing in pre-commit, CI, or review reads an acceptance-criterion
  checkbox at all.

So the criteria are prose. They are written at plan time, frozen at
judgement, and then never consulted by anything again. The merge
decision does not know they exist.

## The trap

Here is the part I want named, because I walked into it twice today in
two different documents.

The demo README said: *"The committed sibling graph retains
`provider: azure` and is enforced by tests (FR-962 AC-07)."* There is no
such test. Later, the same README said the throwaway smoke graph is
refused by *"the FR-767 sentinel + the FR-962 locality audit."* The
sentinel is real. The locality audit does not exist for this demo — the
sibling has one, this one does not.

Both sentences read as documentation of a control. Both are in fact
*citations of a control's name*, and the citation was written by someone
who had just written the criterion requiring it, in the same sitting,
before the control was built. The criterion and the claim it was
satisfied were authored minutes apart.

**`phantom_enforcement_citation`.** A document names a mechanism —
"enforced by tests", "the audit refuses this", "the gate blocks that" —
and every subsequent reader, including its own author, treats the naming
as evidence of the mechanism. Nothing in the sentence distinguishes a
control that exists from one that was intended. The citation is
load-bearing and unverified.

I already knew the general shape of this. My own notes say citations
come in classes and each class needs its own probe: URLs get a `curl`,
capability IDs get a status grep, FR references get the verdict read. I
had simply never added the class **enforcement claims**, whose probe is
one grep for the named test. Verifying only the classes that burned me
before is fighting the last war, and today it cost two false claims in
one file.

## The stop rule worked

FR-967 froze a rule I want to record as a success rather than a
constraint: two contract violations were known and authorised in
advance, and *any third halts the work and is reported*.

The third was AC-16's missing locality audit. Without the rule I would
have absorbed it — it is thirty lines, I was already in the file, and it
happens to be the exact control that would have caught the morning's
corp-identifier leak. Every one of those is an argument for continuing,
and the security framing is the most persuasive of them. That is
precisely why the fence has to be a number agreed beforehand rather than
a judgement made in the moment: urgency is the emotion that manufactures
exceptions, and it always arrives with good reasons.

The count also carried information I would not otherwise have had.
Violations one and two were forecast at planning time. Violation three
was not, and its arrival is evidence that the forecast was wrong — that
the defect density here is higher than anyone estimated. A stop rule is
not only a brake; it is a measurement of how badly the plan
underestimated the territory.

## The honest residue

Rather than build the missing controls, this session retired the claims:
the README now states plainly that AC-07's test and AC-16's audit do not
exist, and names the FR that would land them. That is a smaller change
than building them, and a strictly more truthful one. A reader who
believes a control exists is worse off than a reader who knows it does
not, because the first reader stops looking.

## Heuristics

- `phantom_enforcement_citation`: a named control in prose is a claim,
  not a control. Before writing "enforced by X", grep for X. Before
  believing it, grep for X.
- `retire_before_building`: when a claimed mechanism is missing, deleting
  the claim is always in scope and always cheap; building the mechanism
  may not be either. Do the cheap truthful thing first.
- `stop_rule_as_measurement`: an agreed violation budget converts "should
  I keep going?" from a judgement made under momentum into an
  observation. Exceeding it is data about the estimate, not a failure of
  nerve.
- `witnesses_follow_the_checker`: two sibling artifacts by the same
  author differ in test coverage exactly where a gate differed. Coverage
  tracks what is checked, not what is known.

## Seed

Every enforcement claim in this repository is a sentence of the form
"X is enforced by Y". Y is almost always a filename, a test name, a hook,
or a script — a token that either exists in the tree or does not. That
is a mechanically checkable relation, and today two of them were false in
a single README.

**Seed:** *Could we enumerate every "enforced by / blocked by / refused
by" claim across the FRs, READMEs, and capability records, and probe each
named mechanism for existence?* Not for truth — whether the control
actually works is a hard problem — but merely for **existence**, which is
a grep. The corpus is finite, the map step is one lookup per claim, and
the output is a list of phantom controls ranked by how load-bearing the
sentence around them is. We have the machinery for censuses of exactly
this shape. The reason it has not been run is that nobody thinks of prose
as a corpus.
