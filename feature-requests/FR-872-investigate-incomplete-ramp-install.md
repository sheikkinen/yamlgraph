# Feature Request: Investigate the Incomplete Ramp Install in deviant-daily

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
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
installed 20 hash-verified assets, but seven governance surfaces are
placeholders or non-functional. Determine, per gap, whether the cause is
an **installer defect (FR-865)**, an **unfinished FR-867 step**, or a
**deliberate design outcome** \u2014 then route each to the right FR.

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
| `scripts/judge.sh` | **cannot run** | installer defect \u2014 see below |
| `docs/ramp-manifest.md` | `reviewed_source_sha: pending-human-review` | FR-865 AC-14 gate unsatisfied |

### The one unambiguous defect

`scripts/judge.sh` was installed and invokes:

```
.github/skills/judge-fr/adapters/graph.yaml
```

The installed skill directory contains `SKILL.md`, `doctrine.md` and
`judgement.template.md` \u2014 **no `adapters/` directory**. The launcher
shipped without the graph it launches. The same question must be asked
of `scripts/review.sh`.

Consequence: `deviant-daily` cannot judge its own FRs, which is why this
FR and FR-873 are filed in yamlgraph rather than in the repo whose code
they concern.

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
4. Record the disposition table in this FR.
5. Route: installer defects \u2192 an FR-865 follow-up; unfinished steps \u2192
   FR-867's remaining witnesses; deliberate outcomes \u2192 documented as
   such in `docs/plan-ramp-spike-to-governed.md`.

## Acceptance Criteria

- [ ] AC-01: every surface in the Problem table has a disposition of
      exactly one of `installer-defect`, `fr-867-step`, `deliberate`,
      with the artifact that decided it cited by path.
- [ ] AC-02: `scripts/judge.sh` and `scripts/review.sh` have their full
      referenced-path closure enumerated; every missing path is listed.
- [ ] AC-03: `ramp/manifest.yaml` is scanned for other launcher-without-
      dependency cases; the result is stated even if empty.
- [ ] AC-04: a mechanical check is proposed (not implemented here) that
      would have caught the `judge.sh` gap at install time.
- [ ] AC-05: each `installer-defect` row names the FR-865 acceptance
      criterion that should have caught it, or states that none exists.
- [ ] AC-06: each `fr-867-step` row names the FR-867 acceptance
      criterion it belongs to.
- [ ] AC-07: no source file in either repository is modified under this
      FR \u2014 investigation only; a `git status` in both repos is recorded
      clean at completion.
- [ ] AC-08: the disposition table is added to this FR and referenced
      from FR-867.

## Risks

**Investigation becomes remediation.** The temptation is to fix
`judge.sh` while looking at it. AC-07 makes that a criterion violation;
the fix belongs to whichever FR the attribution routes it to.

**Attribution is contested.** The inert CI stub is both "deliberate"
(FR-865 R-3) and "unfinished" (FR-867 was to activate it). Such rows get
**both** labels with the reasoning recorded, rather than being forced
into one.

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

## Related

- `feature-requests/FR-865-ramp-installer.md`, `FR-866-ramp-tailoring-graphs.md`, `FR-867-ramp-deviant-daily.md`
- `docs/plan-ramp-spike-to-governed.md` \u2014 family overview
- `docs/diary/diary-2026-08-24-twenty-gates-and-a-human-found-the-fire.md` \u2014 the observation that produced this FR
- `sheikkinen/deviant-daily` @ `12bd530`, ramp install `e9595b6`
