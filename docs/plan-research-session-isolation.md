# Research: Session Isolation — Worktrees, Containers, VMs, Cloud

**Date:** 2026-08-30
**Trigger:** operator question after FR-927 (lane-guard retirement): can a
session's worktree be OS-owned by the session and nothing else? Extended to:
what is the industry practice for isolating parallel agent workloads, given
that vendors have moved agent execution to the cloud?
**Sources (fetched 2026-08-30):** Claude Code docs (sandboxing,
sandbox-environments, best-practices), GitHub Copilot cloud agent concepts,
firecracker-microvm.github.io, gvisor.dev, learn.chatgpt.com/docs/cloud
(Codex cloud).

## The industry isolation ladder

Every major vendor now ships the same layered ladder; the rungs differ only
in what owns the boundary.

| Rung | Boundary owner | What it isolates | Industry instances |
|---|---|---|---|
| 1. Git worktree | git index/HEAD per tree | Collision (index, WIP), NOT security | Claude Code worktrees doc + `/batch` (each subagent gets own worktree + PR); our `tmp/worktrees/` |
| 2. OS-primitive sandbox on host | kernel (Seatbelt on macOS, bubblewrap + seccomp on Linux) | Per-command or per-process FS writes + network egress | Claude Code sandboxed Bash tool; `@anthropic-ai/sandbox-runtime` (wraps the WHOLE agent process incl. file tools, MCP, hooks) |
| 3. Container | namespaces/cgroups (+ gVisor userspace kernel for hardening) | Full dev environment | devcontainer with default-deny iptables firewall (Anthropic's published pattern for unattended runs); custom OCI images on CI runners |
| 4. microVM / VM | hypervisor (KVM) | Full OS, kernel-level separation | Firecracker (<125 ms boot, <5 MiB/VM, "purpose-built for AI agents" — used by E2B, Fly.io, Docker Sandboxes, AWS Lambda MicroVMs); Docker Sandboxes = microVM + own Docker daemon + workspace sync |
| 5. Cloud-hosted session | vendor infrastructure | Everything incl. the host | GitHub Copilot cloud agent (ephemeral Actions env, one branch, one PR, 59-min cap); Claude Code on the web (Anthropic-managed VM per session); OpenAI Codex cloud (per-task environments, configurable egress) |

## Convergent best practices (what all three vendors independently do)

1. **Session = ephemeral environment, not a directory.** One task → one
   fresh environment → one branch → one PR. The environment is disposable;
   the branch is the only surviving artifact. Nobody isolates sessions by
   *ownership* of a shared filesystem — they isolate by *not sharing* one.
   The answer to "worktree owned by the session" is: session = principal is
   realized as session = VM/container/runner, never as per-session `chown`.

2. **Enforcement by construction at the resource's own boundary.** Kernel or
   hypervisor for writes, egress proxy for network, credential proxy for
   secrets. Claude Code's docs state it directly: the OS "holds regardless of
   what the model chose to run and even if an allowed command does more than
   its name suggests" — the exact FR-888→FR-889 lesson. Command-string
   classification survives only as a *pre-run review* (auto-mode classifier),
   explicitly paired with an isolation boundary, never as the boundary.

3. **Credentials never live inside the boundary.** Claude Code masks env
   vars/files with per-session sentinels and substitutes the real value at a
   TLS-terminating proxy only for allowlisted hosts (SigV4 re-signing for
   AWS). Claude on the web holds the GitHub token *outside* the sandbox and
   issues scoped credentials inward. Normalize-at-boundary, applied to
   secrets.

4. **Self-modification is the canonical escape and gets dedicated denies.**
   The sandbox denies writes to its own config even inside writable
   directories: `.claude/settings`, hooks dirs, `.mcp.json`, shell rc files,
   and — notably — `.git/hooks` and `.git/config`, with no exemption
   possible. Our FR-889 lock covering `.github/hooks/` is the same move.

5. **Git worktrees get explicit sandbox support.** When the cwd is a linked
   worktree, Claude Code's sandbox allows writes to the shared `.git` dir
   (refs, index) but keeps `hooks/` and `config` denied. That is the
   industry's disposition of the "shared refs residue": allow ref plumbing,
   deny the two files that execute code.

6. **Network egress is default-deny with a domain allowlist** for anything
   unattended; known residual risk (domain fronting) is documented, cure is
   a TLS-terminating inspecting proxy. Filesystem and network isolation are
   explicitly co-dependent: either alone is bypassable through the other.

7. **The escape hatch is audited and centrally disableable.**
   `dangerouslyDisableSandbox` exists but `allowUnsandboxedCommands: false`
   kills it fleet-wide; managed settings pin the policy against local
   widening. FR-888's audited-escape shape is industry-consonant.

8. **The merge boundary stays the human gate.** Every cloud agent terminates
   at a PR under branch protection; commits are the audit trail. Cloud
   agents cannot bypass rulesets (GitHub blocks the agent when rules are
   incompatible rather than exempting it).

## Analysis: what this means for this repo

- **Rung 1 + FR-889 lock is a coherent local tier, not a poor man's
  anything.** Worktree-per-session kills the witnessed collision class
  (shared index/WIP); the OS lock states the main-checkout invariant. This
  matches vendor guidance for *attended* local sessions. No hook should be
  added to this tier — the industry left command parsing behind.
- **The residual inter-session surface (shared refs, `git worktree remove`,
  `.git/hooks`/`config`) has a precedented disposition**: deny the two
  executable files (FR-889 already locks `.github/hooks`; a `.git/hooks` +
  `.git/config` deny is the industry-standard addition), tolerate ref
  plumbing. A narrow R-2-style verb fence on `git worktree remove|prune`
  against foreign lanes is defensible; anything wider is the condemned class.
- **"OS-owned by the session" exists as a product tier, not a chmod trick:**
  Docker Sandboxes (free, microVM + workspace sync, runs agents on any
  Docker host) and `sandbox-runtime` (whole-process wrap, no Docker) are the
  local rungs; Copilot cloud agent is the zero-infrastructure rung already
  available on this repo's platform — chaplain-class autonomous tasks are
  its exact intended workload (ephemeral env, one branch, one PR, hooks and
  MCP configurable, 59-min cap per task).
- **Unattended = boundary required.** Vendor consensus: never run an
  unattended agent outside rung 3+. Our chaplain FSM currently runs
  unattended on the host — by industry practice it is the first workload
  that belongs in a container/microVM or the platform's cloud agent.
- **FR-902's orphaned intents map onto the ladder:** intent 1 (inter-session
  immunity) = rung 1 done + the narrow residue above; intent 2 (per-turn
  loss prevention) is delivered by ephemeral-env + branch-per-session at
  rungs 3–5 (the environment is disposable BECAUSE the branch survives);
  intent 3 (provenance) is read-side in the industry (commit/log audit
  trails on the platform), not write-side trailers.

## Verdict ladder for the operator

1. **Now (no new mechanism):** worktree-per-session by convention +
   locked main + merge gates. Add `.git/hooks`+`.git/config` to the
   protected set if any fence is wanted — precedented, two files, zero
   grammar.
2. **Next (unattended workloads):** move chaplain runs into a container
   (devcontainer + default-deny firewall) or Docker Sandboxes microVM;
   evaluate Copilot cloud agent for issue-labeled chaplain proposals — the
   remote-inbox path (CAP-106) already speaks its language.
3. **Later (full session=principal):** one microVM/container per
   interactive session with only the lane mounted. Real, purchasable,
   changes the operating model; justified when parallel-session count or
   untrusted-code exposure grows.

**Seed:** the platform this repo runs on (VS Code Copilot) already has the
cloud tier (Copilot cloud agent) wired to the same merge boundary our
doctrine enforces. What is the smallest chaplain task class that could be
routed there tomorrow as an experiment — and does its 59-minute cap fit the
plan→judge→enforce cycle, or only the enforce leg?
