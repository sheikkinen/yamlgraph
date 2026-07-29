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

### D-4 Mechanize: authoring sentinel + PreToolUse guard (revised per R-1–R-4)

**Sentinel (R-1, scoped, non-global):** `scripts/author.sh` creates a
per-run sentinel file under `tmp/` containing an unpredictable token
plus route metadata, passes the token to the adapter execution
environment, and removes the sentinel on wrapper exit. The PreToolUse
guard allows governed writes only when the environment token matches a
fresh sentinel. A global sentinel that allows all sessions while
present is forbidden. Existing report-artifact verification in
`author.sh` is preserved.

**Bright-line rule (R-2, path-based, no semantic classifier):** for
agent sessions, ANY unsentineled write to a governed artifact path is
denied — new or tracked. Governed paths: `examples/**/graph.yaml`,
`examples/**/prompts/*.yaml`, `graphs/*.yaml`,
`.chaplain/graphs/*.yaml`. No "material edit" warn-only carveout — a
PreToolUse hook cannot classify edit semantics before the edit runs;
any maintenance escape hatch is a separate explicit operator command
or separate FR.

**Write surfaces (R-3, enumerated):** PreToolUse coverage includes
`create_file`, `replace_string_in_file`, `multi_replace_string_in_file`,
and `apply_patch` paths (shared parsing exists in
`.github/hooks/scripts/checks/common.sh`), and terminal commands using
`cp`, `mv`, `tee`, heredocs, or `>`/`>>` redirection into governed
paths, including quoted-path variants. If a terminal command shape
cannot be parsed safely, deny with a route-to-`scripts/author.sh`
message — never fail open. PostToolUse is advisory only; prevention
lives in PreToolUse.

**Commit backstop (R-4, model chosen: local-only pre-commit proof):**
a local pre-commit check verifies that any staged NEW governed
artifact is listed in the current `tmp/draft-authoring-report.md`.
No CI/merge-boundary claim is made — `tmp/` is ignored and invisible
in a clean checkout; the existing `demo-gate` (demo-output.log in PR
diff) remains the PR-boundary complement for new demos. Tracked-proof
+ CI gate (model b) is explicitly deferred to a future FR if the
local proof proves insufficient.

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

Revised by judgement (2026-07-29) — these supersede the original eight:

- [ ] AC-01: `doctrine.md`, `SKILL.md`, and `.github/copilot-instructions.md`
      contain no `delegated`/`substantial` discriminator for route
      choice; `scripts/author.sh <task-brief.md>` is stated as the sole
      route for all agent-authored governed graph/prompt artifacts,
      with only the adapter re-entry guard as exception.
- [ ] AC-02: The "repeated local drafting of examples and demos stays
      in this skill" sentence, and any equivalent blessing of direct
      in-session authoring, is removed.
- [ ] AC-03: `SKILL.md` contains a "Forbidden routes" section
      explicitly naming direct main-session authoring, ad-hoc subagent
      briefs, copy/move/adapt file-operation framing, and one-shot
      generator output as forbidden routes.
- [ ] AC-04: `SKILL.md`'s first actionable authoring instruction is the
      command `scripts/author.sh <task-brief.md>` stamped `(SOLE
      ROUTE)`, before any workflow prose for the adapter executor.
- [ ] AC-05: Doctrine contains the session-separation rule ("never
      author in the requesting session") and the rationale that if the
      adapter is broken, the adapter is fixed rather than routed
      around.
- [ ] AC-06: `scripts/author.sh` creates a fresh, scoped authoring
      sentinel with a per-run token, passes that token to the adapter
      execution environment, removes it on exit, and preserves
      existing report-artifact verification.
- [ ] AC-07: The PreToolUse guard denies unsentineled writes to
      governed artifact paths across `create_file`,
      `replace_string_in_file`, `multi_replace_string_in_file`,
      `apply_patch`, and terminal write shapes (`cp`, `mv`, `tee`,
      heredoc, `>`/`>>` redirection), including writes to existing
      tracked governed artifacts.
- [ ] AC-08: Hook tests under `.github/hooks/tests/` prove deny without
      sentinel, allow with sentinel, no global sentinel leakage to
      another token/session, denial for existing tracked governed
      artifact edits, denial for terminal copy/move/redirection
      bypasses, and safe denial for an ambiguous terminal write shape.
- [ ] AC-09: The commit backstop follows the chosen model (a):
      local-only pre-commit proof that staged new governed artifacts
      are listed in `tmp/draft-authoring-report.md`, tested, with no
      CI/merge-boundary claim.
- [ ] AC-10: `.github/hooks/README.md` documents the guard, governed
      paths, denial reason, sentinel lifecycle, false-positive/escape
      policy, and the chosen commit backstop model.
- [ ] AC-11: A fresh-session replay of the 2026-07-29 acceptance prompt
      ("create a graph for chinese horoscope") either runs through
      `scripts/author.sh <task-brief.md>` or is denied at the first
      governed artifact write, and the observed route/denial is
      recorded in the FR implementation status.
- [ ] AC-12: No changes are made to judge/review routes, YAMLGraph
      runtime primitives, `examples/yamlgraph_gen`, mobile/web/remote
      trigger surfaces, auto-commit/PR/merge behavior, inbox polling,
      worktree management, or CI-running behavior under this FR.

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

## Judgement (2026-07-29)

**Verdict:** APPROVED WITH REVISIONS — rendered via the sole-route
judge adapter (`scripts/judge.sh`, model gpt-5.5, session 7062b11f);
full artifact archived in
`FR-767-graph-authoring-sole-route.judgement.md`. R-1–R-4 folded into
this FR 2026-07-29; authority active.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Sentinel undefined against concurrent sessions — a global `tmp/.authoring-sentinel` would allow ALL sessions while armed | Per-run unpredictable token in the sentinel, matched against the adapter execution environment; removed on wrapper exit (folded into D-4 + AC-06) |
| R-2 | "Material edits" warn-only carveout contradicts sole-route claim and is not mechanically testable pre-edit | Bright line: ANY unsentineled write to a governed path is denied, new or tracked; no semantic classifier in the hook (folded + AC-07) |
| R-3 | Write surfaces underspecified — enforcement risk of a "regex costume" | Enumerated: 4 file-write tools + terminal cp/mv/tee/heredoc/redirection incl. quoted paths; unparseable shapes deny, never fail open (folded + AC-07/08) |
| R-4 | Commit backstop claimed merge-boundary coverage from an ignored `tmp/` artifact invisible in clean checkouts | Model (a) chosen: local-only pre-commit proof, no CI claim; demo-gate remains the PR-boundary complement; tracked-proof+CI deferred (folded + AC-09) |

**Scope frozen:** D-1–D-10 per the judgement artifact (doctrine/skill/
instructions route collapse, Forbidden routes, wrapper reorder,
sentinel in `author.sh`, PreToolUse guard, hook tests, hook README,
local pre-commit backstop, FR status, changelog/diary as gates
require).

**Not authorized:** changes to judge/review routes; launching another
judge; runtime primitive or copilot-node changes; reviving
`examples/yamlgraph_gen`; remote authoring triggers; auto-commit/PR/
merge/inbox/worktree/CI behavior in the adapter; global hook bypasses;
silent fallback from a denied write to in-session authoring.

**Conditions C-1–C-8 GATE** — notably: C-1 human review before merge
(enforcement infrastructure = adversarial input); C-2 token-bound
sentinel; C-3 prevention in PreToolUse, PostToolUse advisory only;
C-4 path-based materiality; C-5 deny on unparseable shapes; C-6 no
PR-gate claim from ignored `tmp/` state; C-7 re-entry executor still
lints and smokes; C-8 adapter output stays advisory and uncommitted.
