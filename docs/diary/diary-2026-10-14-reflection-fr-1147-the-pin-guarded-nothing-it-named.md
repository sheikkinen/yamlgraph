# Reflection: FR-1147 — the pin guarded nothing it named

**Date:** 2026-10-14
**FR:** FR-1147 (remove CLI version pinning for Claude Code and opencode)

## What happened

Every `backend: claude` node refused in preflight: the host had Claude
Code `2.1.296`, the allowlist held `2.1.255`. Forty-one patch releases
had passed, and each one was an outage until someone made an
allowlist-only commit. For each risk the pin claimed to cover, I checked
which guard actually caught it. Payer drift is caught by the auth probe,
auth and envelope shape by Pydantic, and missing flags by the non-zero
exit. The only thing the version string guarded alone was "this binary
is Claude Code at all", and the product suffix of the banner already
says that. The fix kept the shape `X.Y.Z (Claude Code)` and dropped the
number.

The Copilot backend served as the control case. It has never had a
pin, and it has run judge and review through every Copilot CLI release.
That is the existence proof the FR leaned on.

## Traps

- **Pin as the default safety posture.** FR-1048 copied the pin "exactly
  as `CLAUDE_SUPPORTED_BANNERS` does". The second backend inherited the
  first one's outage pattern by imitation, not by evidence. A copied
  guard needs to restate what it guards in its new home.
- **The live witness met a different boundary.** On Windows, `claude` on
  PATH is an npm `.cmd` shim, and `subprocess.run(["claude", ...])`
  cannot launch it. The unit tests mock `subprocess`, so they never
  touch that layer. Only the live call reached the platform boundary.
- **Round-1 rejection was earned.** The first draft left two choices
  to the judge and called a design-alternatives table "research". The
  judge asked for precedent and dissent. The preserved dissent (flag
  *semantics* can drift silently) is the honest cost of the change.

## Heuristic

Before keeping any allowlist, list each risk it claims and the guard
that already catches that risk at the boundary. Keep only the risks
that have no other guard, and keep the narrowest check that covers them.

**Seed:** Which other exact-match guards in the repo (model ids, schema
versions, tool versions) would fail an audit of "what does this guard
catch that no typed boundary does"? And could a lint flag any
`frozenset({...})` of version strings that has only one member?
