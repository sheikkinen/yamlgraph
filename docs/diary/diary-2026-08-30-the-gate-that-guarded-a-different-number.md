# The Gate That Guarded a Different Number

**Date:** 2026-08-30
**Context:** Operator asked for an audit of overlapping hooking / branch
protection mechanisms. Mapped all five enforcement rings (PreToolUse,
PostToolUse, pre-commit/commit-msg, CI, branch protection) and their
rule-by-rule overlap.

## What happened

The overlap map itself was mostly clean: every apparent duplication
(trailers ×3, prior-art ×2, ruff/size/terms ×2, changelog ×3, authoring
route ×2) turned out to be deliberate layering across distinct bypass
modes, each documented with its FR. The redundancy is the design.

The audit surfaced one concrete defect instead: FR-714 "gate-truth"
raised the coverage threshold 70→85 in `pyproject.toml` addopts and
corrected the stale CLAUDE.md claim — but `.github/workflows/workflow.yml`
passes `--cov-fail-under=80` explicitly, and CLI args override addopts.
The *required* CI check has been enforcing 80 the whole time doctrine
claimed 85. The FR whose entire purpose was aligning gates with truth
fixed the documentation and the config, and missed the one invocation
where the gate actually binds. Submitted to `.chaplain/inbox/`.

Two structural observations that are policy, not defects, but worth
naming: (1) with `enforce_admins` off, the effective merge boundary for
the default single-dev flow is pre-commit — made binding only by the
PreToolUse `--no-verify` block, so the innermost agent-only ring is
doing the outermost ring's job; (2) the deep quality gates (radon,
bandit code scan, vulture, jscpd, hedging, req-coverage) have no CI
echo at all — one `SKIP=` and they vanish without a witness.

## The trap

**Threshold duplication is drift with a delay.** The same number lived
in three places (pyproject, workflow.yml, CLAUDE.md); FR-714 updated
two. A gate value copied into a second enforcement surface is not
redundancy — redundancy is two *mechanisms* covering different bypass
modes. Two *copies of the same parameter* in one mechanism is a race
between them, and the loser is whichever one the auditor greps last.
This is `infrastructure_self_exempt` in its subtlest form: the
gate-truth FR audited every surface except the precedence rule joining
them.

## Heuristic

When auditing overlapping enforcement, classify each overlap as
*mechanism redundancy* (different rings, different bypass modes — keep)
or *parameter duplication* (same threshold/pattern copied across
surfaces — collapse to one source and let precedence carry it). The
first is defense in depth; the second is a drift generator. The grep
that ends the audit is not "where is this rule enforced" but "how many
places hold this rule's *value*, and which copy wins."

## Seed:

Could a pre-commit check assert single-sourcing of gate parameters —
grep for known threshold flags (`cov-fail-under`, radon `-n`, bandit
severity, jscpd `--threshold`) across pyproject/workflows/pre-commit
and fail when the same flag appears with two different values? The
FR-714 drift was mechanically detectable the day it was introduced.
