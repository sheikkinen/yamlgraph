# Diary: Sandboxing Is a Deployment Concern, Not a Framework Feature

**Date:** 2026-05-31
**Context:** Evaluating a "Declarative Sandboxing for Agent Tools" proposal — YAML-configured Docker/WASM isolation for tool calls

## The Proposal

"A zero-code container orchestration tool for agents. Developers define ephemeral sandbox environments in YAML (Docker container or WASM instance) for specific tool calls, ensuring autonomous AI actions are securely isolated from the host."

## The Empirical Answer

Three Fly.io deployments already run yamlgraph in production:

| App | VM | Workers | Tools executed unsandboxed |
|-----|-----|---------|--------------------------|
| ninchat-voice | 1GB Firecracker microVM | 3 | voice_speak, yamlgraph_async, ninchat_connect, call_cleanup |
| marketing-questionnaire | 1GB Firecracker microVM | 3 | Same Dockerfile, different graph |
| csap-staging | 1GB Firecracker microVM | 5 | +monitor-ui, +metrics-server |

Fly.io runs each app in a Firecracker microVM. The process inside has no access to other apps, other customers, or the host. If `yamlgraph_async` goes rogue, it can trash its own 1GB VM — and nothing else. The VM restarts on crash. State lives in external systems (Twilio, Ninchat, LangSmith, Tigris S3).

The proposal is containers-inside-containers. The Fly microVM is already the sandbox.

## Two Separate Concerns

| Concern | Layer | Solution | Status |
|---------|-------|----------|--------|
| **Process isolation** (protect host from tool) | Infrastructure | Deployment platform (Fly/Firecracker, Docker, k8s) | Already solved |
| **Tool permission** (which tools an agent can call) | Application | Graph config: guard pattern, tool declarations, loop_limits | Partially solved |

The proposal conflates them. Docker-in-Docker adds latency (500ms–2s cold start) for isolation already provided by the deployment platform. The real gap — "agent calls dangerous tool" — is an application concern. An agent that calls `kubectl delete` is equally dangerous whether it runs in WASM or bare metal. The fix: don't give the agent the tool, or gate it with approval.

## The Graduated Security Path

| Level | Mechanism | Effort | What it blocks |
|-------|-----------|--------|----------------|
| **0** (done) | `shlex.quote()` on variables | Done | Shell injection via user input |
| **1** | Tool permission declarations in YAML | ~2 days | Undeclared filesystem/network access |
| **2** | LLM-as-gate before tool execution | Exists (guard pattern) | Semantically dangerous commands |
| **3** | Process-level sandboxing (seccomp/landlock) | ~3 days | Syscall-level isolation |
| **4** | Container sandboxing (Docker/WASM) | ~5 days | Full host isolation |

Levels 1+2 cover 95% of the risk. Level 4 is only justified for untrusted third-party graphs — a marketplace model that doesn't exist today.

## Trap

`vendor_default_as_help` inverted — the deployment platform already provides strong isolation, but because it's invisible (no YAML to configure), it doesn't feel like a "feature." The proposal invents a visible YAML-configured sandbox because visibility = feeling of control. The Firecracker VM is stronger isolation than anything Docker-in-Docker would provide, but it has no YAML knob to turn.

## Heuristic

**Before adding isolation infrastructure, enumerate what the deployment platform already provides.** Fly/Firecracker, ECS/Fargate, GKE/gVisor — all provide VM-level or container-level isolation. Framework-level sandboxing duplicates what the platform does, at higher latency and lower strength. The framework's job is *permission* (what tools can be called), not *isolation* (what syscalls can execute).

Corollary: when a security proposal makes you feel safe because it has a YAML config, check whether the actual isolation is provided by an invisible layer below. Security that you can see isn't necessarily stronger than security you can't.

## Seed

When does the untrusted-graph marketplace scenario arise? If yamlgraph graphs are ever distributed as packages (npm-style), the trust boundary shifts from "author = operator" to "author ≠ operator." At that point, Level 4 sandboxing becomes justified — but so does a complete supply chain model (signing, permissions manifest, audit trail). The sandbox alone is necessary but not sufficient.
