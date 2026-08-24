# Feature Request: Investigate the Incomplete Ramp Install in deviant-daily

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced (judged 2026-08-24, R-1..R-4 folded; investigation complete same day)
**Effort:** 0.25 day (investigation only)
**Requested:** 2026-08-24
**First consumer / first event:** the next repo to be ramped. The first
event is running `scripts/ramp.sh` against it and getting an install
whose gaps are *known and dispositioned* rather than discovered by
inspection afterwards. The immediate consumer is FR-867, which cannot
close until each gap below is attributed.

**Prior art:** **FR-865** defines the installer whose manifest may be
incomplete \u2014 this FR does not change it, it determines whether it is at
fault. **FR-866** defines the tailoring graphs whose outputs are absent
from the target \u2014 likewise. **FR-867** is the application whose
acceptance criteria are unmet; this FR is the investigation that must
precede its completion (`investigation_before_fix`). **FR-864** is the
family parent. FR-826/862/863 are target-repo history, non-overlapping.
No REJECTED prior art occupies this territory.

## Summary

The Tier-3 ramp of `sheikkinen/deviant-daily` (commit `e9595b6`)
installed 20 hash-verified assets. The investigation row set is
**closed at the nine surfaces** in the Problem table: seven gap rows
plus two **positive controls** (the live pre-commit hook set and the
Copilot guard set), which are in scope as controls and excluded from
the gap count. Determine, per row, a `primary_disposition` — exactly
one of **`installer-defect` (FR-865)**, **`fr-867-step`**, or
**`deliberate`** — plus optional `secondary_dispositions` for
contributing causes, each label citing the deciding artifact — then
route each row to its `route_target`.

## Value Statement

The next ramp either installs a working process or states exactly which
parts it cannot, instead of leaving an install that looks complete and
is not.

## Problem

Verified at `deviant-daily@12bd530` on 2026-08-24:

| Surface | State | Suspected cause |
|---|---|---|
| `.pre-commit-config.yaml`, 12 hooks | **live** \u2014 fired on a real commit | working as designed |
| Copilot guard set | installed | working as designed |
| `.github/workflows/tests.yml` | **inert stub**, `on: workflow_dispatch` | FR-865 R-3 honest-stub choice; FR-867 was to activate it |
| `AGENTS.md` | 9-line stub | FR-866 graph output never landed |
| `docs/incidents.md` | **absent** | `ramp_incidents` never run against target |
| `capabilities/` | README only, **0 entries** | `ramp_rtm` output never landed |
| requirement tags in tests | **0** | FR-867 step 5 not performed |
| `scripts/judge.sh` | **cannot run** | contested — see hypothesis below |
| `docs/ramp-manifest.md` | `reviewed_source_sha: pending-human-review` | FR-865 AC-14 gate unsatisfied |

### The judge/review launcher question (hypothesis, not verdict)

`scripts/judge.sh` was installed and invokes:

```
.github/skills/judge-fr/adapters/graph.yaml
```

The installed skill directory contains `SKILL.md`, `doctrine.md` and
`judgement.template.md` — **no `adapters/` directory**. The launcher
shipped without the graph it launches. The same question must be asked
of `scripts/review.sh`.

This is a **hypothesis to investigate, not a pre-judged installer
defect**: FR-865's record says the curated wrappers intentionally add
an adapter-graph existence check because the installer ships no graphs
(`feature-requests/FR-865-ramp-installer.md`, Decisions), and
`ramp/curation-diffs.md` states the adapter graph "must be authored in
the target per its own doctrine" — while the installed `SKILL.md`
bundle maps name `adapters/` and declare the adapter the sole route.
The rows for `judge.sh`/`review.sh` are ordinary investigation rows
whose disposition must reconcile all four artifacts: manifest entries,
curation-diff rationale, installed script references, and installed
skill bundle maps. If `installer-defect`, state why FR-865's curation
rationale is insufficient; if `deliberate` or `fr-867-step`, state the
concrete route by which the target obtains usable judge/review
adapters before it can govern its own FRs.

Consequence meanwhile: `deviant-daily` cannot judge its own FRs, which
is why this FR and FR-873 are filed in yamlgraph rather than in the
repo whose code they concern.

### Why this is an investigation, not a fix

The seven gaps have at least three different causes, and fixing them
without attribution would put target-specific content into a generic
installer \u2014 the exact mechanism FR-207 proved decays. The deliverable is
the attribution.

## Ideal Result

A dated disposition table: one row per gap, each marked
`installer-defect` / `fr-867-step` / `deliberate`, each with the
evidence that decided it and the FR it routes to. Nothing is fixed under
this FR. FR-867's remaining work becomes a known list rather than a
discovery exercise, and FR-865 gains a defect list if it has one.

## Proposed Solution

1. For each of the nine surfaces above, establish the cause from
   artifacts: `ramp/manifest.yaml` (was the asset ever declared?),
   `docs/ramp-manifest.md` (was it installed?), FR-867's steps (was the
   step performed?), FR-865/866 acceptance criteria (was it in scope?).
2. Verify the `judge.sh` / `review.sh` dependency closure specifically:
   enumerate every path each script references and check the manifest
   declares it.
3. Check whether `ramp/manifest.yaml` declares any other **launcher
   without its dependencies** \u2014 the defect class, not just the instance.
4. Record the disposition table in this FR, one row per surface, with
   fields: `primary_disposition`, optional `secondary_dispositions`,
   deciding artifact citation (path + line/section), and
   `route_target` — an existing FR plus AC number, a new follow-up
   FR/proposal path, or a documentation section with no implementation
   action.
5. Route: installer defects → an FR-865 follow-up; unfinished steps →
   FR-867's remaining witnesses; deliberate outcomes → documented as
   such in `docs/plan-ramp-spike-to-governed.md`.

### Evidence boundary (frozen, R-3)

The target repository is **read-only**. YAMLGraph runtime code, ramp
assets, graph artifacts, prompts, hooks, CI, and skill doctrine are
**read-only**. Permitted yamlgraph writes: this FR, the FR-867
reference, and any documentation/proposal artifact explicitly named as
a `route_target` in the disposition table. Cross-repo evidence must be
from committed artifacts or a recorded clean checkout state. The
enforcement record must include before/after `git status --short` and
HEAD for both repositories, proving the target did not change.

## Acceptance Criteria

*(revised per judgement 2026-08-24; R-1..R-4 folded)*

- [x] AC-01: FR-872 is revised to define the closed investigation row
      set, primary/secondary disposition schema, evidence boundary,
      permitted write set, and per-row routing contract from R-1
      through R-4.
- [x] AC-02: Before evidence collection, the record captures yamlgraph
      HEAD/status and `deviant-daily` HEAD/status; the target repo
      must be clean and remains read-only throughout the investigation.
- [x] AC-03: Every in-scope row has `primary_disposition` exactly one
      of `installer-defect`, `fr-867-step`, or `deliberate`, optional
      `secondary_dispositions`, and at least one deciding committed
      artifact cited by path and line/section.
- [x] AC-04: `scripts/judge.sh` and `scripts/review.sh` have their
      referenced-path closure enumerated from the installed scripts
      and skill files; every absent referenced path is listed and
      reconciled against `ramp/manifest.yaml` and
      `ramp/curation-diffs.md`.
- [x] AC-05: `ramp/manifest.yaml` is scanned for every shipped
      launcher or instruction artifact that references paths not
      shipped by the manifest; the result is stated even if empty.
- [x] AC-06: A mechanical follow-up check is proposed, not implemented
      here, that would catch launcher-without-dependency or
      instruction-without-bundle closure gaps at install validation
      time.
- [x] AC-07: Each `installer-defect` row names the FR-865 acceptance
      criterion that should have caught it, or states that no existing
      criterion covers it and names the follow-up route. *(rows 8/9:
      no existing FR-865 criterion covers instruction closure or the
      review-stamp lifecycle — AC-02/03 validate manifest source
      paths, not paths referenced inside assets; AC-14 requires only
      `ramp/consumers.md` + FR records; both route to the FR-865
      follow-up in AC-06)*
- [x] AC-08: Each `fr-867-step` row names the FR-867 acceptance
      criterion or remaining-step record it belongs to.
- [x] AC-09: Each `deliberate` row cites the controlling design
      decision, judgement condition, curation record, or accepted
      limitation that makes it deliberate.
- [x] AC-10: The completed disposition table is added to FR-872 and
      referenced from FR-867; any deliberate-outcome documentation or
      installer-defect follow-up proposal is limited to the route
      target named in the table.
- [x] AC-11: Completion records final yamlgraph and `deviant-daily`
      HEAD/status; `deviant-daily` is unchanged, and yamlgraph changes
      are limited to the revised FR/documentation/proposal artifacts
      authorized by AC-10.

## Risks

**Investigation becomes remediation.** The temptation is to fix
`judge.sh` while looking at it. AC-07 makes that a criterion violation;
the fix belongs to whichever FR the attribution routes it to.

**Attribution is contested.** The inert CI stub is both "deliberate"
(FR-865 R-3) and "unfinished" (FR-867 was to activate it). Such rows
get one `primary_disposition` plus `secondary_dispositions` with the
reasoning recorded, rather than being forced into one label or given
two contradictory primaries.

**The gaps are treated as an indictment of the ramp.** They are not: 20
assets installed correctly and the pre-commit gate is live and firing.
The investigation is about the delta, not the whole.

## Alternatives Considered

- **Fix each gap as found.** Rejected: it would push target-specific
  content into a generic installer without deciding whether it belongs
  there, which is FR-207's failure mechanism.
- **Fold into FR-867.** Rejected: FR-867 is the *application*; whether
  its tooling is defective is a different question and its answer may
  change FR-865.
- **Wait for the next ramp to see if it recurs.** Rejected: there is a
  live target with a broken judge route now.

## Implementation Record (2026-08-24) — ENFORCED

### Boundary record (AC-02, before)

- yamlgraph HEAD `c1379ef618c38a092b164689e349e58ac59e094b`; working
  tree clean except two foreign staged diary files
  (`docs/diary/2026-08-2{3,4}-git-report.md`, parallel session,
  untouched throughout).
- `deviant-daily` HEAD
  `12bd530cbaeb6f8149e39c0f72f0d222600b4387`, `git status --short`
  empty. Read-only throughout — no target file was opened for write.

### Disposition table (AC-03, dated 2026-08-24, at target `12bd530`)

Positive controls (in scope as controls, excluded from the gap count):

| Row | Surface | primary_disposition | Deciding artifact | route_target |
|---|---|---|---|---|
| 1 | `.pre-commit-config.yaml`, 12 hooks | working control | target commit `e9595b6` was gated by these hooks at creation; `ramp/curation-diffs.md#pre-commit-config` (curation kept standard repos at identical revs) | none — documentation row |
| 2 | Copilot guard set | working control | `.github/hooks/pre-command-guard.json` references `.github/hooks/scripts/pre-command-guard.sh`, shipped by `ramp/manifest.yaml` (entries at lines 19–25); closure complete | none — documentation row |

Gap rows:

| Row | Surface | primary_disposition | secondary_dispositions | Deciding artifact | route_target |
|---|---|---|---|---|---|
| 3 | `.github/workflows/tests.yml` inert stub | `deliberate` | `fr-867-step` | FR-865 Implementation Record, Decisions: "explicit `workflow_dispatch` setup stub (AC-13 second branch) … activation is the operator's move"; the installed file's own header declares it a stub to replace | FR-867 AC-13 (remaining step 6) |
| 4 | `AGENTS.md` 9-line stub | `fr-867-step` | `deliberate` | installed `AGENTS.md:1-9` self-declares "stub by design … installer never writes doctrine content (FR-865)"; doctrine draft `6e03df7a0ff2` sits in the FR-867 R-3 handoff table awaiting reviewer | FR-867 AC-09 (remaining step 4) |
| 5 | `docs/incidents.md` absent | `fr-867-step` | — | incidents draft `686e86a2eff5` in FR-867 handoff table awaiting reviewer; landing it is FR-867 step 4 | FR-867 AC-10 |
| 6 | `capabilities/` 0 entries | `fr-867-step` | — | RTM draft `465708c3d04a` (80 candidates/108 tests/0 gaps) in FR-867 handoff table awaiting reviewer | FR-867 AC-11 |
| 7 | requirement tags in tests: 0 | `fr-867-step` | — | FR-867 remaining step 5 ("Tag tests / record gaps"), not yet performed; depends on row 6 landing | FR-867 AC-12 |
| 8 | `scripts/judge.sh` / `scripts/review.sh` cannot run | `deliberate` | `installer-defect` (bundle-map claim only, see AC-04) | `ramp/curation-diffs.md#judge-sh`: existence check added deliberately, "the adapter graph must be authored in the target per its own doctrine" — the scripts fail loudly and instructively exactly as curated | scripts: FR-867 (the target authors its adapters per installed `doctrine.md` before it can govern its own FRs — new FR-867-family step); SKILL.md claim: FR-865 follow-up (below) |
| 9 | `docs/ramp-manifest.md`: `reviewed_source_sha: pending-human-review` | `installer-defect` | — | `scripts/ramp_installer.py:224` hardcodes the literal; the install ran *after* FR-865 AC-14 approval was recorded (`cea3e49f` in `ramp/consumers.md`), so the stamp was already wrong at write time — the installer has no way to receive a completed review | FR-865 follow-up (below) |

### AC-04: judge.sh / review.sh referenced-path closure

Enumerated from the installed scripts and skill files at `12bd530`:

| Referencing artifact | Referenced path | Present? | Reconciliation |
|---|---|---|---|
| `scripts/judge.sh:29,10,11` | `tmp/`, `tmp/.judge.lock`, `tmp/draft-judgement.md` | runtime-created (`mkdir -p` line 29) | not a gap |
| `scripts/judge.sh:12` | `.github/skills/judge-fr/adapters/graph.yaml` | **ABSENT** | consistent with `ramp/manifest.yaml` (no graph entries — closed manifest, FR-865 GATE C-4) and `ramp/curation-diffs.md#judge-sh` (existence check added for exactly this state) |
| `scripts/judge.sh:22` | `.github/skills/judge-fr/doctrine.md` | present | — |
| `scripts/review.sh:13` | `.github/skills/review-pr/adapters/graph.yaml` | **ABSENT** | same as judge.sh — designed fail-loudly state |
| `scripts/review.sh:23` | `.github/skills/review-pr/doctrine.md` | present | — |
| `.github/skills/judge-fr/SKILL.md:28-29,39` | `adapters/`, `adapters/README.md` | **ABSENT** | **unreconciled**: the installed bundle map asserts `adapters/` is part of the bundle with "execution instructions in `adapters/README.md`", but nothing ships it and the SKILL gives no signal it must be authored in-target |
| `.github/skills/review-pr/SKILL.md:28-29,39` | `adapters/`, `adapters/README.md` | **ABSENT** | same instruction-without-bundle gap, second instance |

The scripts behave exactly as curated (`deliberate`); the two SKILL.md
bundle-map claims are the `installer-defect` component of row 8.

### AC-05: manifest-wide launcher/instruction scan

Every shipped launcher and instruction artifact was scanned for
referenced paths not shipped by `ramp/manifest.yaml`:

- `scripts/gates/{changelog,diary}_gate.sh` — reference
  `changelog/unreleased/`, `docs/diary/` (target-created on use) and
  carry their own wiring instructions in header comments; deliberately
  NOT wired into the shipped `.pre-commit-config.yaml`
  (`ramp/curation-diffs.md#pre-commit-config`: cold-wired local gates
  would break the target's first commit). Not a closure gap.
- `scripts/req_coverage.py` — references `capabilities/` (shipped
  README) and `tests/` (target-owned). No gap.
- `.github/hooks/pre-command-guard.json` →
  `.github/hooks/scripts/pre-command-guard.sh` — shipped. No gap.
- `.github/workflows/tests.yml` — echo-only stub, no path
  dependencies. No gap.
- `.github/skills/*/SKILL.md` — **2 instances** of
  instruction-without-bundle (`adapters/README.md`), one defect class,
  recorded in row 8 / AC-04.

**Scan result: one defect class, two instances, both in skill bundle
maps. No launcher ships without its executable dependencies.**

### AC-06: proposed mechanical check (not implemented)

`ramp.sh --validate-closure` (or a unit test over `ramp/assets/`):
for each curated asset, extract repo-relative path references
(path-shaped tokens in scripts and skill/doc bundle maps) and assert
each is one of (a) a manifest destination, (b) declared in a new
per-asset manifest field `expects_authored:` (paths the *target* must
create, rendered into the install transcript as explicit TODOs), or
(c) a runtime prefix (`tmp/`). The `judge.sh` gap would have surfaced
as an undeclared `expects_authored` path at curation time. Route:
FR-865 follow-up FR (with the row-8 SKILL.md wording fix and the row-9
`--reviewed-sha` stamp option folded into the same follow-up).

### Boundary record (AC-11, after)

- `deviant-daily` HEAD unchanged at `12bd530`, status clean —
  untouched.
- yamlgraph changes: this FR, the FR-867 reference (AC-10), and
  `docs/fr-board.md` — exactly the permitted write set.

## Related

- `feature-requests/FR-872-investigate-incomplete-ramp-install.judgement.md` — verdict, frozen scope, C-1..C-6
- `feature-requests/FR-865-ramp-installer.md`, `FR-866-ramp-tailoring-graphs.md`, `FR-867-ramp-deviant-daily.md`
- `docs/plan-ramp-spike-to-governed.md` \u2014 family overview
- `docs/diary/diary-2026-08-24-twenty-gates-and-a-human-found-the-fire.md` \u2014 the observation that produced this FR
- `sheikkinen/deviant-daily` @ `12bd530`, ramp install `e9595b6`
