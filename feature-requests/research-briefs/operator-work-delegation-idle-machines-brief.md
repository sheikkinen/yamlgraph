# Problem brief: the development machine is saturated while idle machines sit on the LAN

**Prior art:** `feature-requests/FR-766-runpod-provider.md` establishes the
pattern for offloading *LLM inference* to a remote OpenAI-compatible
endpoint (`ChatOpenAI + base_url`, lmstudio precedent) — it delegates
tokens, not tests or agent work; distinguished. The `lmstudio` provider
(`yamlgraph/utils/llm_providers.py`, `LMSTUDIO_BASE_URL`) is the only
existing LAN-delegation surface in the repo, and it covers inference only.
`.github/copilot-instructions.md` `one_session_one_repo` documents that
parallel agent sessions sharing one repo corrupt each other — the current
cure is worktrees on the SAME machine, which multiplies local load instead
of distributing it. No FR or capability addresses delegating compute
(tests, CI, agent sessions) to other devices; the absence is the gap.

## Problem statement

The primary development machine — an iMac, Intel i5-10500, 6 cores / 12
threads, 8 GB RAM — runs at capacity. Multiple concurrent Copilot agent
sessions each operate in their own git worktree, and each routinely starts
the unit test suite (~6000 tests, `pytest -n auto` spawning 12 workers).
Two or three concurrent suite runs more or less freeze the system: 24–36
pytest workers plus editor, browser, and agent processes contend for 12
hardware threads and 8 GB. Test-suite optimization is explicitly NOT the
primary approach sought — the operator wants the load moved off the box.

Idle machines exist on the same LAN (192.168.50.0/24, ASUS RT-AX88U
router). Verified 2026-09-01:

- **Huutokauppakone** (192.168.50.172, Windows by TTL=128) — a machine
  that has previously served LM Studio at port 1234. Today NOTHING is
  listening: ports 22, 1234 (LM Studio), 11434 (Ollama) all closed. The
  repo's `.env` still points `LMSTUDIO_BASE_URL` at a stale link-local
  address `169.254.142.62` from a previous direct-cable epoch; the current
  reachable address is 192.168.50.172 via mDNS name `Huutokauppakone.local`.
- An HP device (hp53e813, likely a printer) and consumer devices; no other
  general-purpose computers currently answer, though more can be powered on.

The question is: what software and what skills (in the repository sense —
`.github/skills/` workflow contracts and agent capabilities) are needed so
that agents working on this repo can delegate heavy work to other devices
instead of saturating the local machine? Three delegation classes matter,
in descending frequency:

1. **Test execution** — the dominant load. ~6000 unit tests, currently
   run locally by every agent session before every commit (pre-commit
   hooks run checks too). Candidate mechanisms to evaluate: pytest-xdist
   over SSH/execnet gateways (`--tx ssh=...`), self-hosted GitHub Actions
   runners on LAN machines (CI already runs the matrix on push), a
   remote-exec wrapper (rsync/git push to remote + ssh pytest + fetch
   junit XML), or a job queue. Each has environment-reproducibility
   costs on a Windows host (WSL2? native Python? Docker?).
2. **LLM inference** — already partially solved by the `lmstudio`
   provider, but the endpoint is down and its address management is
   manual and stale. What is needed to make LAN inference a reliable,
   discoverable, health-checked resource (static DHCP lease or mDNS
   resolution in `.env`, LM Studio headless service mode with JIT model
   load, `lms server start` on boot, multiple hosts)?
3. **Whole agent sessions / graph runs** — research.sh, judge.sh,
   author.sh runs take minutes of local CPU. Could a remote machine host
   entire sessions (VS Code Remote-SSH, copilot CLI on the remote, or a
   worktree rsynced to the remote), honoring `one_session_one_repo` by
   giving each remote its own clone?

## Classification

judgement/analysis/generation

## Constraints

- The operator programs shell/C#/JS but not Python; all Python work is
  done by agents. Delegation tooling must be operable by agents through
  skills, not by hand-tuned human ritual.
- The fleet is heterogeneous: macOS dev box, at least one Windows box,
  possibly more machines powered on later. Solutions requiring identical
  OS images are disqualified unless they bring their own layer (Docker,
  WSL2, VM).
- The LAN is a home network behind an ASUS router; machine addresses
  drift (the stale `.env` entry is the witness). Name-based discovery
  (mDNS) or pinned DHCP leases are preconditions, not afterthoughts.
- GitHub Actions already runs the test matrix on push; a self-hosted
  runner registered to the repo would reuse the entire existing CI
  contract for free, but puts repo secrets on a LAN Windows box —
  security posture must be assessed.
- Doctrine requires tests run before commit (TDD, pre-commit hooks);
  any remote-test mechanism must return results fast enough (<~2 min)
  and reliably enough to sit inside that loop, or it will be bypassed.

## Witnessed incidents

- 2026-09-01 (operator report): concurrent agent sessions each starting
  the ~6000-test suite "more or less freeze the system" on the 12-thread
  / 8 GB iMac; the operator explicitly redirected from test optimization
  to delegation as the primary approach.
- 2026-09-01 (verified this session): `LMSTUDIO_BASE_URL` in `.env`
  points at 169.254.142.62 — dead link-local address; the actual host
  Huutokauppakone answers at 192.168.50.172 but with LM Studio not
  serving (port 1234 closed). The one existing delegation surface has
  silently rotted with zero health-checking to notice.
- 2026-05-25 (`.github/hooks/logs/audit.jsonl`): agent sessions used the
  LM Studio endpoint for judge-model evaluation (`lmstudio-gemma4`),
  proving LAN inference delegation worked when the endpoint was up —
  demand exists, supply is unmanaged.

The deliverable sought from this research: a ranked set of viable
delegation architectures with named software, the skills/scripts the repo
would need, the failure modes (network partition, remote env drift, secret
exposure), and the minimal first increment — presumably reviving
Huutokauppakone as a managed resource — each stated with enough precision
to become one or more feature requests.
