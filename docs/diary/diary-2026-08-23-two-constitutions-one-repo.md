# 2026-08-23 — Two constitutions, one repo: what the comparison actually taught

**Arc:** FR-870 post-enforcement reflection. The exhibit
(`docs/constitution-diff.md`) carries the numbers; this entry carries what
the numbers don't say. Raw artifact preserved:
`docs/memento/speckit-constitution-2026-08-23.md`.

## On the constitution as a document

Read side by side, the two documents are different *genres*, not different
qualities.

The generated constitution is a **mirror**. It is accurate, well-organized,
and entirely reactive: every principle is a restatement of something the
repo already enforces. Its seven principles map to our gate suite with
almost no residue — which means it would have been equally happy to
constitutionalize a *bad* repo. Point `/speckit.constitution` at the
December spike and it would have produced "Principle I: Ship Fast" with a
confident rationale. A mirror has no opinion about what it reflects. The
Scripture, by contrast, is a **scar record**: nearly every clause exists
*against* something that happened. The generated document has rationales;
the Scripture has witnesses. That is the genre difference — a rationale
explains why a rule is plausible, a witness proves why it was necessary.

Second observation: the generated constitution is *better organized* than
the Scripture. Seven crisp principles, a gates table, a workflow section —
versus our accreted YAML-in-markdown with traps interleaved into cures. The
generator lost on content and won on form. That's worth admitting: the
Scripture's structure is an archaeology of its growth, not a design, and a
reader who isn't its author pays for that. (The successor-session problem —
`what_would_the_successor_need` — applies to the law itself.)

Third: the constitution's tense is uniform — everything is MUST, present,
timeless. The Scripture has *history* in its grammar ("third strike recorded
2026-07-14", "graduated FR-853"). Timeless law is easier to obey and
impossible to audit; dated law tells you which rules are load-bearing. When
we eventually restructure the Scripture, the dates and witnesses are the
part that must survive.

## On the process comparison

Spec Kit's pipeline (constitution → specify → plan → tasks → implement →
converge) and the Sermon (Research → Plan → Judge → Enforce → Purge →
Submit → Distill) differ at exactly two joints, and both joints are trust
boundaries:

1. **No Judge.** Every Spec Kit checkpoint is author-verified: the same
   agent that wrote the spec confirms the spec. The Sermon inserts an
   adversarial reader with input closure before authority is granted.
   FR-870 itself demonstrated the value — the judge's six revisions (R-1
   sanitization above all) are why the experiment measured rediscovery
   instead of leakage. Run under Spec Kit's own process, this experiment
   would have read the answer key and reported success.
2. **No Distill.** Spec Kit's loop ends at converge; nothing flows from
   incident back into constitution except manual amendment. The Sermon ends
   at Distill, and the graduation pipeline is why the Scripture contains 29+
   incident-paid clauses at all. This is the mechanism difference behind the
   measured content difference: the generator couldn't rediscover the case
   law because *no forward pass produces case law* — only the backward pass
   from failure does.

Everything else is convergent: frozen scope ↔ frozen spec, acceptance
criteria ↔ checklists, gates ↔ converge. The two missing joints are
precisely the two the origin story predicted ("no independent judge",
"specs are launch documents, not case law") — written before the experiment
ran. That's the most reassuring part of the whole arc: the prose claim
survived contact with its own falsification test.

## Trap noted: the exhibit almost became the essay

Mid-classification I felt the pull to editorialize inside the exhibit —
to argue in table (d) instead of labeling. The FR's scope freeze ("the
classification IS the judgement work") held it to labels + evidence, and
the arguing got deferred to here, where it belongs. `intent_drift` caught
at the document boundary: the exhibit measures, the diary interprets, the
essay (unwritten) will argue.

## Next steps

1. **The essay** (origin-story proposal 1, the FR-870 first consumer):
   "A Judged Fork of Spec-Driven Development" can now cite the exhibit.
   Chaplain inbox proposal when the operator calls for it.
2. **G-02 graduation candidate**: "test-only Pydantic models prove
   genericity" — the one genuine generator find. Small convention, cheap FR.
3. **Legibility audit** (seed from the distill entry): enumerate Scripture
   units that are law-without-police (prose-only, mechanizable) — e.g.
   Judge-independence is enforced only by skill text, not by any hook.
   Candidate chaplain proposal: "police the judge boundary mechanically."
4. **Scripture form debt**: the generator's structural win suggests a
   restructure pass (principles → gates table → case law with dates), kept
   content-identical. Only if the operator wants it — form changes to law
   are high-blast-radius.
5. **FR-866 ramp tie-in**: the ramp transplants governance to foreign repos;
   the exhibit is evidence for its pitch — a generated constitution gives a
   foreign repo the mirror, the ramp gives it the missing organs (judge +
   distill loop).

**Seed:** Spec Kit's constitution has an explicit amendment procedure with
semantic versioning; the Scripture's amendment procedure (graduation) is
stronger but *unversioned* — there is no way to cite "Scripture as of
FR-727". Should the Scripture carry a version stamp per graduation, so
judgements can pin the law they were rendered under?
