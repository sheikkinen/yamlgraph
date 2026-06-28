# The doctrine that never reached the desk where prompts are written

**Date:** 2026-06-28
**Context:** Philosopher review of `author-prompt` SKILL.md against the prompt-complexity diary arc (FR-497, FR-581–589)
**Companion:** [the brief I would never give a subagent](diary-2026-06-24-the-brief-i-would-never-give-a-subagent.md)

## What I was asked

"Check diary / prompt complexity and author-prompt skill. Reflect." A read, then a
judgement: does the document that *teaches prompt authoring* carry what the project
paid most dearly to learn about prompts?

## What I found

It did not. The lesson exists, enforced, in four places:

- **Diary** — the `delegation_asymmetry` trap and the prompt-as-subagent-contract
  cure (FR-585 → FR-587).
- **Scripture / user memory** — abstraction-span as the diagnostic metric.
- **A linter** — `W026` in `checks_prompts.py` (FR-586), live and gating.
- **An example** — `examples/abstraction_span` (FR-589), the calibration harness.

Every place *except* `author-prompt/SKILL.md` — the one document an agent opens when
it sits down to write a prompt. The skill taught syntax (fields, Jinja2, schema
types) and a single limp bullet, "keep system messages focused." An agent following
it faithfully would author a ten-headed monolith and meet the doctrine only when
`W026` fired downstream — if it fired at all.

## The trap (named)

**enforcement_without_upstream_teaching** — a lesson can be fully captured (diary),
fully enforced (linter), and still be *absent from the artifact that forms the
intent the enforcement later judges*. The knowledge graph treats this family as
boundary violations: the boundary here is the author's intent, and the skill is
where intent is formed. W026 normalizes *downstream*, at the finished prompt; the
skill is the *entry boundary*, and it was silent. This is the same shape as the
FR-616 linter blind spot I filed this session — enforcement present, prevention
absent — which suggests the pattern is not incidental but structural: we write the
gate and the post-mortem, and forget the briefing.

## Why it happens

Doctrine accretes where the *correction* happens — in the FR, the diary, the linter
that caught the next instance. The skill is upstream of all corrections, so no
single failure ever lands on it; it is nobody's blast radius. The cost of its
silence is paid globally and invisibly, exactly like the cost of each sentence added
to the L5 monolith. The asymmetry repeats one level up: I split the *meta-work*
(FRs, gates, linter) with care while leaving the *teaching artifact* a syntax sheet.

## The cure (applied)

Added a load-bearing "One prompt = one subagent brief" section to the skill, at the
top where it is read first: the five-clause contract, the *split-don't-tune* rule,
the two FR-497 invariants (no call sees the whole corpus; no call emits a number),
and a pointer to `W026` + the calibration example. Promoted "one judgement per
prompt" to Best Practice #1. The skill now teaches at the entry boundary what the
linter only enforces at the exit.

## Seed

If a captured-and-enforced lesson can still be missing from its own teaching
artifact, is there a *third* gate beyond diary and linter: a mechanical check that
every `Wxxx` lint rule names the skill section that would have *prevented* it — and
fails CI when a rule has enforcement but no upstream teaching cross-reference? The
diary records the correction, the linter catches the recurrence; what guarantees the
briefing is updated so the recurrence never starts? Where else is a hard-won law
enforced downstream but unwritten at the desk where the work begins?
