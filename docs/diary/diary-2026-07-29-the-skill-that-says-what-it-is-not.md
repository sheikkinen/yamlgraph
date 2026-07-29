# The skill that says what it is not

**Date:** 2026-07-29
**FR:** FR-765 — graph authoring workflow skill
**Context:** Enforcement of a judged skill-package FR: two markdown
artifacts, a test upgrade, and a capability registry extension. No
runtime code. The interesting part was not what was built but how much
of the artifact is negative space.

## The observation: doctrine by exclusion

Roughly a third of the delivered SKILL.md and doctrine.md is statements
of what the skill is *not*: not the one-shot generator, not FR
judgement, not PR review, not a syntax reference, not a remote
create-and-run surface. This mirrors the judgement's R-3 — the original
FR draft said "judge-fr-style delegation" and the judge correctly read
that as boundary erosion. The cure was not softer wording but explicit
prohibition: named forbidden routes, banned verdict vocabulary.

The pattern generalizes: a workflow skill placed *between* two existing
heavyweight processes (raw chat generation below, Chaplain/judge/review
above) is defined primarily by its borders. The 2026-07-27 reflection
(`the-skill-became-the-law`) recorded the opposite failure — the
review-pr skill's mere existence pulled ordinary bugfixes into worktree
ceremony because it had no anti-scope. FR-765's skill ships with the
anti-scope built in on day one: an Escalation section that names when to
leave the skill, and an Anti-patterns section that names how the skill
itself fails. The trap `framework_costume` has a documentation twin: a
skill without an exit clause becomes an attractor for work it was never
meant to own.

## The trap encountered: gate matches shape, not meaning

The FR-756 process-boundary conftest gate flagged my test module because
a *docstring* contained the literal `examples/yamlgraph_gen`. The test
touches only `.github/skills/` — no process boundary. The regex
(`examples/`) checks the shape of a reference, not its substance;
ironically the same `gate_checks_shape_not_substance` trap the
judgement's R-2 made me fix in the skill tests themselves. I reworded
the docstring rather than marking a pure-filesystem test as `process`
(which would have exempted it from the fast unit tier — a worse lie).

## Heuristic

When authoring any skill or process doc, write the exit clause first:
who should NOT use this, and where they go instead. A skill's
anti-scope is not defensive boilerplate — it is the mechanism that
prevents the artifact from becoming a behavioral attractor
(`the-skill-became-the-law`, now cured at authoring time instead of
diagnosed post-hoc).

**Seed:** The FR-756 gate and the FR-446 presence tests both failed the
same way — matching shape, not substance. Could a lint pass over our
*gates themselves* mechanically flag shape-only checks (regex on
prose/docstrings, existence-only assertions) and demand a substance
counterpart, the way `req_coverage` demands a test per requirement?
