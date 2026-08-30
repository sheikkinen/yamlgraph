# Problem brief: judging an FR occupies an attended local session

<!-- Closed input for the research route (FR-890). Incident record only;
     no solution content. -->

**Prior art:** filename-noun hits on other briefs are unrelated subject matter.
`fr-925-lane-delivery-problem-brief.md` and `fr-926-error-surfacing-problem-brief.md`
concern hook delivery and pipeline diagnostics respectively — distinguished; this
brief concerns where the judge stage executes and what it costs.

## Problem statement

Every feature request must receive an independent judgement before any
implementation authority exists. The judge stage is fully mechanized —
a yamlgraph graph behind an operational launcher — yet each run
executes on the operator's machine inside an attended agent session:
interpreter setup, a filesystem lock, five to ten minutes of blocking
latency, then a manual copy of the draft into the canonical judgement
file. The operator states judgement output is never manually
challenged (900+ FRs of conditioned trust), so the attended session
adds cost without adding review. Doctrine forbids judging in the FR
author's own session, forcing extra session discipline. The formerly
automated plan-judge pipeline is not running; its abandonment is
attributed to the per-run cost of this hand-cranked stage.

## Classification

judgement/analysis/generation

## Constraints

- The judge graph, its prompt, its doctrine, and its launcher are the
  sole judge route; a second judge route may not be created.
- The judgement is advisory until a human decision point; the human
  merge decision at the PR boundary is the exercised human gate.
- Input closure: the judge may see only the FR content and repo
  doctrine — never the author's chat narrative.
- The judge must not run in the FR author's session.
- Main is OS-locked; all durable writes land via worktree → PR →
  squash merge.
- Any LLM step handling repository content must not hold a
  repository-write credential (instruction-boundary doctrine treats
  agent output as untrusted).
- The FR and its judgement are committed files in feature-requests/;
  their pairing is checked by existing gates.

## Witnessed incidents

- 2026-08-30, FR-927: judge run occupied an attended session in a
  dedicated worktree; the draft was hand-folded into the judgement
  file and a prior-art gate failure forced a second commit round.
- 2026-08-30, FR-928 first judging round: identical attended ritual
  (lock, interpreter prefix, fold).
- Operator calibration 2026-08-30 (diary "the gates nobody walks
  through"): plan-judge never manually challenged; chaplain and
  inquisitor not running; per-FR cost named the process's major
  handicap.
- The sibling repository's issue-driven runner executes yamlgraph
  graphs with an agent CLI on ephemeral cloud runners daily (live
  since 2026-08-19); its intake run 32361594593 is cited in this
  repo's capability registry.
