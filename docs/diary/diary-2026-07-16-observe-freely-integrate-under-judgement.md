# 2026-07-16 — Observe freely, integrate under judgement

**Context:** "reflect — is fr required." Asked at the exact seam the
day kept exposing: half of today's commits were unjudged spikes, half
were full-ceremony FRs, and both halves were *right*. The evidence
deserves the rule it was already following.

**The record, sorted by lane:** tap.py v1 and the otel scripts
shipped as chores — and found the compaction phenomenon precisely
because they skipped ceremony. FR-739 and FR-740 went through
judgement — and *both* judgements changed the design with a
measurement the author hadn't taken (10 phantom compactions; the
700-row board). F7 and the phantom-witness fix rode as amendments
under their completed FRs. Three lanes, zero collisions.

**The rule, named:** `observe_freely_integrate_under_judgement`.
- **Observation code** (read-only, spike lane, author is the only
  consumer) needs no FR. A spike carries its own justification: it
  ran and found something, or it dies. Taxing exploration with
  ceremony starves the discovery channel that paid twice today.
- **Integration code** (wired into a skill, briefing, or hook;
  anything other sessions' commits can bounce off) requires the
  judged FR. Both ceremony runs today had positive ROI, and the
  graduation moment is precise: *when the spike gains a consumer
  other than its author*. FR-739 was filed at exactly that moment.
- **Fixes inside a completed FR's territory** are amendments — the
  FR is the context; a new FR would fragment the source of truth.

**The deeper criterion:** the FR is required exactly where a future
reader needs a judgement to *disagree with*. Nobody needs a findings
table to understand a spike — the spike is its own finding. But
"why does the board exclude terminal statuses?" and "why does the
committed board stop at the repo boundary?" have answers only in
F1 and F7. Obligations to others need recorded judgements;
observations need only honesty about being observations.

**And the seed already knew:** the `--gated` candidate ends with "if
the human uses it twice, wire it" — the two-strike rule operating as
an FR *generator*. The second reach is the evidence the Judge would
demand at the `unchallenged_premise` check ("is the pain real?").
Filing before the second reach is `growth_as_default` wearing a
process costume. (Same day, same pattern: the per-session cost table
was built only when the human asked how to get ongoing-session costs
— the reach WAS the requirement.)

**Seed:** graduate the lane rule to Scripture's process section as
`observe_freely_integrate_under_judgement` if it survives one more
arc in a sibling project — the boundary is currently instinct, and
instinct doesn't survive compaction. Second seed: the FR template
could carry a one-line lane declaration ("spike / integration /
amendment") so the prior-art hook and the Judge know which contract
applies before reading a word of the body.
