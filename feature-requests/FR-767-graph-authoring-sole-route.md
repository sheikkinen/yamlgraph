# Feature Request: FR-767 Graph-Authoring Sole-Route Hardening

**Priority:** HIGH
**Type:** Doctrine / Enforcement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-29
**First consumer / first event:** the next agent session given a graph
task ("create a graph for chinese horoscope" — the exact acceptance
test that failed 2026-07-29), at the moment it finishes the precedent
search and chooses between authoring in-session and running
`scripts/author.sh`.

## Summary

The graph-authoring skill failed its acceptance test: the agent loaded
the skill, read the doctrine, searched precedent correctly — then
authored directly in-session. The route the test expected
(`scripts/author.sh <task-brief.md>`) was bypassed *with textual
cover*: the contract contains an undefined discriminator
("substantial"), an explicitly blessed direct path ("repeated local
drafting of examples and demos stays in this skill"), and no forbidden
route naming the bypass actually taken. Harden the contract to
judge-fr parity: one route, enumerated forbidden alternatives,
executable command first, and a mechanical sentinel gate.

## Value Statement

Skill compliance stops depending on the agent resolving an ambiguous
predicate mid-flow. The route becomes a property of the system
(mechanism), not of the session (instruction text) — the same
transition that made judge-fr compliance boring.

## Problem

Structural diff between the compelling contract (judge-fr) and the
non-compelling one (graph-authoring), from the 2026-07-29 acceptance
failure analysis:

1. **Two routes, undefined discriminator.** judge-fr: "the YAMLGraph
   adapter is the ONLY permitted execution route" — no predicate.
   graph-authoring: adapter is sole route "for delegated authoring",
   gated on "substantial graph creation" — *substantial is never
   defined*, and the doctrine explicitly blesses the direct path:
   "Repeated local drafting of examples and demos stays in this
   skill." A new demo directory is textually exactly that, so the
   bypass was *defensible under the contract's own words*.
2. **Primacy inversion.** The wrapper's first actionable section ("To
   author a graph") is an imperative to author directly; the adapter
   appears second, qualified. judge-fr leads with the invocation
   surface stamped **(SOLE ROUTE)**.
3. **Forbidden-routes strawman.** judge-fr enumerates the exact
   alternatives an agent would reach for (VS Code prompt,
   sister-session, subagent). graph-authoring forbids only "ad-hoc
   subagent briefs" — direct main-session authoring, the most probable
   bypass and the one taken, is on no forbidden list.
4. **No structural separation rule.** judge-fr: "Never judge in the FR
   author's own session" makes in-session execution categorically
   impossible. Authoring has no analogue, so in-session execution
   reads as legitimate.
5. **No workaround-closing rationale.** judge-fr: "If the graph
   toolchain is broken, fix the toolchain — do not route around the
   judge." graph-authoring gives no reason direct authoring is worse,
   so precedent-copying momentum feels like full compliance
   (`quick_confidence`).

Trap taxonomy: `gate_checks_shape_not_substance` applied to skills —
the hook verified the skill *loaded*; nothing verified the *route*.
And `two_strike_split`: this is the second same-day route bypass
(strike 1: "mv hello-runpod" — skill never fired, patched with trigger
prose in 910e2c82; strike 2: acceptance test — skill fired, prose read
through its escape hatch). Two strikes ⇒ the abstraction level belongs
in CODE; stop rewording.

## Ideal Result

An agent given any graph-authoring task either runs
`scripts/author.sh <task-brief.md>` or is the adapter's own execution
(re-entry guard); every other route is named forbidden, and a direct
write to a governed graph artifact without the adapter's sentinel is
mechanically denied before the file changes — the contract cannot be
complied with accidentally or bypassed defensibly.

## Proposed Solution

Minimal path back from the ideal, four deliverables:

### D-1 Collapse to one route (doctrine.md + SKILL.md + copilot-instructions.md)

Delete the "delegated"/"substantial" discriminator and the "repeated
local drafting stays in this skill" blessing. The adapter is the sole
route for ALL authoring of governed artifacts; the ONLY exception is
the re-entry guard (an agent launched BY the adapter authors directly,
still lints and smokes). Add the session-separation analogue: *"Never
author in the requesting session — the requesting session writes the
task brief; the adapter authors."* Add the workaround-closing
rationale: *"If the adapter is broken, fix the adapter — do not route
around it."*

### D-2 Forbidden routes section (SKILL.md)

Enumerate the actual alternatives, mirroring judge-fr:
- Direct main-session authoring of new graph/prompt artifacts
  (the 2026-07-29 bypass) — forbidden.
- Ad-hoc subagent briefs bypassing the adapter — forbidden.
- Copy-then-adapt framed as file ops (mv/cp) — forbidden (trigger
  boundary, 910e2c82).
- One-shot generation (`examples/yamlgraph_gen` model) — forbidden
  (already documented, keep).

### D-3 Reorder the wrapper (SKILL.md)

Executable command first: "## To author a graph" opens with the
`scripts/author.sh <task-brief.md>` invocation stamped **(SOLE
ROUTE)** and the task-brief contract; doctrine-reading and workflow
prose follow as the adapter executor's contract (re-entry context),
explicitly labeled as such.

### D-4 Mechanize: authoring sentinel hook (two-strike pre-emption)

PostToolUse hook (new `.github/hooks/scripts/checks/`
`graph-authoring-guard.sh`, wired into `post-edit-checks.json`):
denies `create_file`/`edit` results touching `examples/**/graph.yaml`,
`examples/**/prompts/*.yaml`, `graphs/*.yaml`, or `.chaplain/graphs/*.yaml`
unless an authoring sentinel is armed. `scripts/author.sh` arms the
sentinel (file under `tmp/`, mirroring the reasoning-sentinel one-shot
pattern); the sentinel carries the adapter session identity and is
consumed/expired on completion. Repairs to *existing* committed graphs
during non-authoring work (e.g., version bump touching a demo) are the
known false-positive class — scope the deny to new-file creation plus
material edits (node/edge/prompt changes), warn-only for the rest, and
record the discrimination rule in the hook README.

### Distilled constraints

- Doctrine changes go through Plan → Judge → Enforce (this FR is the
  Plan; per graph-authoring's own Escalation section, changing the
  skill's contract is not authoring work).
- judge-fr wrapper is the structural template — parity, not invention.
- The hook must not block the adapter's own execution (sentinel armed)
  or the Chaplain enforce pipeline's graph edits (same sentinel or an
  equivalent pipeline identity).
- Instruction text changes (D-1..D-3) and mechanism (D-4) ship
  together: the Scripture's `detection_without_enforcement` — prose
  without a gate is advisory, and this failure class has already
  proven it reads prose through escape hatches.

## Acceptance Criteria

- [ ] AC-01: `doctrine.md`, `SKILL.md`, and `copilot-instructions.md`
      contain no "delegated"/"substantial" discriminator; the adapter
      is stated as the sole route for all governed authoring with the
      re-entry guard as the only exception.
- [ ] AC-02: The "repeated local drafting of examples and demos stays
      in this skill" sentence (or equivalent blessing of direct
      in-session authoring) is removed.
- [ ] AC-03: SKILL.md has a "Forbidden routes" section explicitly
      naming direct main-session authoring of new graph/prompt
      artifacts.
- [ ] AC-04: SKILL.md's first actionable content is the
      `scripts/author.sh` invocation stamped (SOLE ROUTE), before any
      direct-workflow prose.
- [ ] AC-05: Doctrine contains the session-separation rule ("never
      author in the requesting session") and the fix-the-adapter
      rationale.
- [ ] AC-06: A PostToolUse hook denies unsentineled creation of new
      `graph.yaml`/`prompts/*.yaml` under governed trees, with a test
      under `.github/hooks/tests/` proving deny (no sentinel), allow
      (sentinel armed), and warn-only (material edit to existing
      committed graph).
- [ ] AC-07: `scripts/author.sh` arms the sentinel before the adapter
      graph runs and disarms after; a re-run of the 2026-07-29
      acceptance test ("create a graph for chinese horoscope") through
      a fresh session either uses the adapter or is denied at the
      first artifact write.
- [ ] AC-08: Hook README documents the guard, the sentinel lifecycle,
      and the false-positive discrimination rule.

## Alternatives Considered

- **Prose-only hardening (D-1..D-3 without D-4):** rejected —
  two strikes in one day proved instruction text with any reading
  ambiguity is read through the ambiguity; `two_strike_split` mandates
  code.
- **Hook-only (D-4 without prose changes):** rejected — the denial
  message must point at a contract that actually says one route;
  otherwise the agent reads the current text, finds the blessed direct
  path, and files the denial as a hook bug.
- **Define "substantial" mechanically instead of collapsing routes**
  (e.g., new directory or >1 authored file ⇒ adapter): viable but
  inferior — it preserves a predicate the agent evaluates mid-flow,
  and every predicate boundary becomes the next defensible bypass.
  Judge may resurrect this if adapter-for-everything proves too heavy
  for one-line prompt tweaks; if so the bright line must be mechanical
  and hook-enforced, not prose.
- **Session-separation without adapter (author in any *other*
  session):** rejected — reintroduces the manual sister-session route
  judge-fr already forbids for judgement; the adapter IS the
  separation.

**Prior art:** FR-765 created the skill/doctrine/adapter and its
judgement anticipated route discipline but modeled the discriminator
on delegation willingness, not artifact class — this FR disposes of
that discriminator as the root defect. Commit 910e2c82 (same day)
patched the *trigger* boundary with prose after strike 1; it is
subsumed, not contradicted: trigger prose remains, route enforcement
moves to code. The reasoning-sentinel one-shot pattern
(`.github/hooks/scripts/reasoning-pattern-check.sh`) is the
mechanization precedent. judge-fr's wrapper (FR-737 lineage) is the
structural template.

## Related

- `.github/skills/graph-authoring/` — the contract under repair
- `.github/skills/judge-fr/SKILL.md` — parity template (SOLE ROUTE +
  Forbidden routes)
- `docs/diary/diary-2026-07-29-skill-trigger-artifact-class.md` —
  strike 1 (trigger); this FR is strike 2 (route)
- `.github/hooks/README.md`, `post-edit-checks.json` — hook wiring
- Scripture: `two_strike_split`, `gate_checks_shape_not_substance`,
  `detection_without_enforcement`
