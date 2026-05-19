# Reflection: FR-410 watcher author identity gate

## Context

FR-410 fixed a recurrent authorship defect where watcher-generated commits used placeholder identity (`Test <test@test.com>`). The implementation enforced identity at runtime and at merge boundary in CI.

## Cognitive Process

1. The first trap was file-name anchoring: FR number 407 already existed for an unrelated rejected topic, so creating a new FR file was required instead of mutating historical FR-407.
2. The second trap was partial remediation: adding only the runtime fix would have left merge-boundary exposure. The dual-boundary design (runtime + CI) avoided that.
3. The third trap was test illusion: existing retry tests silently assumed no extra subprocess calls. Identity enforcement introduced new `git config` calls, so existing fakes had to be upgraded before meaningful assertions.

## What Worked

1. Exact-match blocklist (`name == Test`, `email == test@test.com`) kept v1 deterministic and low-risk.
2. Strict env propagation assertions (`GIT_AUTHOR_*` and `GIT_COMMITTER_*`) validated behavior rather than trusting intent.
3. Running a focused regression slice (`test_commitlint_workflow.py`) after gate changes prevented accidental CI workflow drift.

## Trap and Heuristic

- Trap: `partial_remediation`.
- Heuristic: "Identity policy must be enforced at both creation boundary and merge boundary; a single boundary is an advisory, not a guardrail."

## Seed

Seed: Can author identity blocking be driven by a single repository-owned policy file consumed by both watcher runtime and CI gates to eliminate drift between enforcement layers?
