# Reflection FR-1047 (second) — The Ceremony Ate the Artifact

**Date:** 2026-09-11
**Trigger:** operator: "ballooning FR. request was for an investigative skill.
i.e. a single document file. helper script - ok. needs some tests - okayish.
30+ tests - overengineering."
**Supersedes nothing.** The first FR-1047 reflection
(`2026-09-10-reflection-fr-1047-the-cure-was-already-on-disk.md`) is about the
incident. This one is about what I did to the request.

## The numbers

| Artifact | Lines | Share |
|---|---:|---:|
| `.github/skills/clean-dirty-main/SKILL.md` — **the thing asked for** | 106 | 7% |
| `tests/unit/test_dirty_main_triage.py` | 453 | 31% |
| `feature-requests/FR-1047-*.md` + `.judgement.md` | 464 | 32% |
| `scripts/dirty_main_triage.py` | 270 | 19% |
| CAP, changelog, confessions, ARCHITECTURE, route | 156 | 11% |
| **Total** | **1449** | |

The request was "a new skill to clean dirty main" — an investigative document.
I shipped 1449 lines of which 106 were the document. Twenty-nine tests for a
helper script. Two review rounds. A 116-line judgement. The ratio of apparatus
to deliverable is roughly 13:1.

## The trap

`gate_output_as_requirement`. The plan-judge-enforce-review pipeline emits an
obligation at every stage, and I folded every one of them.

The judge did not see the operator's request. Its input closure is the FR plus
doctrine — by design. So it optimises **the artifact in front of it**, not the
ask behind it. My FR was already larger than the request when it reached the
judge; the judge then correctly hardened that larger thing into sixteen
acceptance criteria. I recorded "all six revisions folded, none refused" as if
compliance were a virtue. It was abdication. Every stage ratchets scope upward
and there is no downward click in the machine — the only place a downward click
can exist is in the author, comparing the artifact back to the sentence that
asked for it.

Then the reviewer found three real bugs, and I reported that as the process
working. It was the opposite. **The bugs were defects of scope, not defects of
care.** A symlink mode confusion, a malformed-porcelain fallthrough, a
`--find-object` deletion mis-attribution — none of those failure modes exist in
a skill document. They exist because I wrote a general-purpose classifier. I
then spent a review round hardening generality nobody asked for, and added
three more tests to prove I had hardened it. Passing review is not vindication
when the artifact is out of scope; it means the gate checked the thing I built
rather than the thing requested, which is exactly what gates do.

## The sharpest bit

I already had the answer in the second turn of the session. Diagnosing the
incident I ran, by hand:

```bash
for f in $(git status --porcelain --untracked-files=all | awk '{print $2}'); do
  git show origin/main:"$f" | diff -q - "$f" && echo MATCH || echo DIFFER
done
```

Six lines. It settled the incident. It is the entire decision procedure. The
honest deliverable was a SKILL.md containing that loop, the three-class
interpretation, and the stop rule — a document a human reads and runs.

Instead I re-implemented a working one-liner as a 270-line program, which
introduced the bug surface that the review then found, which produced more
tests, which produced another review round. The script was not an improvement
on the loop; it was the loop plus failure modes.

`working_answer_already_in_hand`: for a skill-class ask, the throwaway
diagnostic that solved the problem **is** the deliverable. Promoting it to a
program adds surface without adding capability.

## What I should have done

File the FR — it was requested and it is cheap. Then:
`SKILL.md` with the loop, the three classes, the stop rule, the incident
history, the route line. Maybe a 40-line helper if the loop is awkward to type.
Two or three tests: the safe case, the unseen case, the refusal. Ship. No CAP,
no 16 ACs, no review round on a document.

The judgement's sixteen acceptance criteria should have met one refusal in the
fold table: *this is an investigative document; the classifier contract belongs
to a tool FR that has not been requested.* I had the standing to write that
line. I have refused judge revisions before (P4, this same FR, with a witness).
I did not even consider it here, because the revisions were individually
reasonable — which is how a ratchet works.

## Heuristic

**Size the response to the artifact class named in the request, and re-read
that sentence at every gate.** "A skill" means a document. "A helper script"
means a script, not a program with a test suite. Before folding any judge or
reviewer finding, ask: does this grow the artifact past what was asked? If yes,
refuse it in the fold table — a refusal with a reason is a disposition, and
disposition is what the pipeline actually requires. "Folded, none refused" on a
small ask is a smell, not a credential.

Corollary: the judge cannot see the request. Carry the operator's literal words
into the FR verbatim, so the next gate is at least reading them.

**Seed:** Every gate in this repo can only add. Judge adds criteria, review adds
findings, each finding adds a test. What would a gate that *subtracts* look
like — one whose output is "delete this, it exceeds the ask"? The outsider is
the closest existing thing: it reads with less context and reports what it could
not justify. Could a sibling read an FR against the originating request alone —
not doctrine, not the diff — and return the lines that no sentence in the
request supports? A scope outsider. It would have caught this one before the
first test was written.
