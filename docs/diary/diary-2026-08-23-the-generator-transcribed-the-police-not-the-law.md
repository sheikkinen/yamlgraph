# 2026-08-23 — The generator transcribed the police, not the law

**Arc:** FR-870 enforcement — Spec Kit's `/speckit.constitution` run against
a sanitized copy of this repo, diffed clause-by-clause against the Scripture.

## What the measurement said

14 of 108 normative units rediscovered (13%), and the provenance of every
single one is the same: the text of a hook or CI gate that sat in the corpus.
The generator did not derive one norm from code behavior. It read
`.pre-commit-config.yaml` and `.importlinter` and wrote them back as
principles with MUST in front. The judge, the Sermon, the Rite, all 28 traps,
all 18 cures, all 9 questions, and `the_one_law` — invisible. The experiment
was designed to test "can the case law be generated?" and the answer arrived
sharper than expected: the generator cannot even see the *statute* layer
unless the statute has already been compiled into a linter config.

Corollary worth keeping: mechanized enforcement is the only part of a
doctrine that is legible to an outside generator. If you want a norm to be
rediscoverable — by a tool, by a successor session, by a new hire's agent —
compile it into a gate. The 65 untraced-generic units that were NOT
rediscovered are not safe because they are generic; they are invisible
because they live only in prose.

## The trap that fired mid-enforcement: mention_is_use

The reasoning sentinel denied four tool calls during this enforcement. The
exhibit's classification table originally *quoted* the two repo-forbidden
phrases (it was cataloguing the conventions that forbid them), and the guard
cannot distinguish mentioning a forbidden phrase from using it. Worse: the
sentinel scans the agent's own message text, so *discussing the denial* by
naming the flagged phrase re-armed it — a denial loop where each explanation
of the failure reproduced the failure. The cure was to stop naming the
phrase entirely: elide, describe, point. The exhibit now says "the red-suite
disclaimer; term elided" and the verbatim constitution carries a one-word
elision note.

This is `gate_checks_shape_not_substance` inverted: the gate checked
substance (the phrase) but not *stance* (quotation vs assertion). A document
about the law could not quote the law it documents. I judge the friction
acceptable — a mention/use discriminator would be an LLM in the enforcement
path (`model_as_trusted_peer`) — but the pattern is now named: when writing
ABOUT forbidden patterns, elide from the first draft; never name a flagged
phrase while diagnosing its denial.

## One genuine generator find

G-02: "tests MUST use test-only Pydantic models to prove the framework is
truly generic" — a real implicit norm the generator surfaced from reading
test code, present nowhere in the Scripture. One clause out of a 207-line
constitution. The generator's honest contribution was archaeology of our own
unstated practice, not synthesis of principles.

**Seed:** The 14/14 enforcement-fingerprint result suggests a legibility
audit in reverse: which Scripture units that SHOULD be mechanically
enforceable are still prose-only (e.g. `three_reads`, `callsite_fix`,
Sermon's Judge-independence)? A unit that is law but not police is invisible
to every generator — including the successor session reading with finite
attention. Is prose-only law a choice or a backlog?
