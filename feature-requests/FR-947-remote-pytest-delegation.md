# Feature Request: Remote pytest delegation via pytest-xdist SSH gateway

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-09-01
**First consumer / first event:** the next agent about to run the full unit suite when another agent's suite is already in flight on the same iMac. **First event:** the next pre-commit run that would push the box past load average 8 on 12 threads — witnessed today with the operator reporting "concurrent agent sessions … more or less freeze the system."
**Research:** [FR-945.research.md](FR-945.research.md)
**Prior art:**
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) — recon foundation this FR reads before delegating; distinguished: 945 inspects, this executes.
- [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md) — reuses its WinRM-bootstrap pattern for OpenSSH + WSL2 install; distinguished: 946 delegates inference, this delegates test execution.
- [FR-902-session-worktree-lifecycle.md](FR-902-session-worktree-lifecycle.md) [Enforced] — delegates concurrent agent work to worktrees on the *same* machine; distinguished: this FR moves the work off-box.
- **`one_session_one_repo`** doctrine (`.github/copilot-instructions.md`) — cited to explain the design: the remote gets its OWN clone per session, no shared index across the SSH boundary.

## Summary

Install OpenSSH Server + WSL2 + a matching Python venv on Huutokauppakone. Ship `scripts/remote-pytest.sh` that rsyncs the current worktree to the remote and runs `pytest --tx ssh=agent@Huutokauppakone.local -n auto` via pytest-xdist's remote gateway, returning results to the local `junit.xml`. Fall back to local pytest on any remote failure within 5 s so the pre-commit loop never blocks on remote unavailability.

## Value Statement

Concurrent agent sessions stop competing for the same 12 hardware threads; the iMac stays responsive while ~6000 tests run on an idle Windows box.

## Problem

- ~6000 unit tests × ~3 concurrent agent sessions × `pytest -n auto` (12 workers) = up to 36 pytest workers on a 6-core / 12-thread / 8 GB box. Operator reports concurrent runs "more or less freeze the system."
- Test-suite optimization has been explicitly ruled out by the operator as the primary approach.
- Huutokauppakone (192.168.50.172) sits idle. SSH port 22 is closed today; there is no test-delegation channel at all.

## Ideal Result

An agent runs `scripts/remote-pytest.sh` (or `PYTEST_REMOTE=1 pytest ...`) and gets the same JUnit XML as `pytest -n auto` locally — same pass/fail, same failure details — only the CPU load lives on Huutokauppakone. If the remote is unreachable, the same command falls back to local pytest transparently, so no pre-commit hook ever hangs on a network partition.

## Proposed Solution

1. **Remote bootstrap** — extend FR-946's WinRM revival to also (idempotently):
   - `Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0`; start `sshd`; open TCP 22 on LAN subnet only. (Witnessed 2026-09-01: `OpenSSH.Server` capability is `NotPresent` on Huutokauppakone; this install step will run for real.)
   - WSL2 is already present (Docker Desktop provisioned `docker-desktop-data` as default distro, version 2 — witnessed 2026-09-01). Install a dedicated Ubuntu distro for the agent workload so it stays independent of Docker Desktop state; create user `agent`; install `pyenv` + Python 3.11 and 3.13 to match the CI matrix (`.github/workflows/tests.yml`) since native Windows Python is 3.10.11 (witnessed) and won't match.
   - Provision `~/agents/.venv` from repo constraints (`constraints/*.txt` — the FR-761 dependency governance artifact).
   - Install rsync inside WSL2 (Ubuntu default).
   - Distribute an SSH key: private key on the iMac at `~/.ssh/huutokauppakone_ed25519`, public in `agent`'s `~/.ssh/authorized_keys`. Key never enters the repo.
2. **`scripts/remote-pytest.sh`** — the delegation entrypoint:
   - Resolve `PYTEST_REMOTE_HOST` (default `agent@Huutokauppakone.local`).
   - `rsync -az --delete --exclude .git --exclude __pycache__ --exclude .venv "$PWD/" "$PYTEST_REMOTE_HOST:~/agents/$(git rev-parse --short HEAD)/"` — each commit gets its own remote dir, honoring `one_session_one_repo` across the SSH boundary.
   - `ssh $PYTEST_REMOTE_HOST 'cd ~/agents/<sha> && ~/.venv/bin/pytest -n auto --junitxml=junit.xml "$@"'` (args passthrough).
   - `scp $PYTEST_REMOTE_HOST:~/agents/<sha>/junit.xml ./junit.xml`.
   - Overall wall-clock ceiling: 180 s; on timeout kill remote and fall back.
3. **`.github/skills/remote-pytest/`** — SKILL.md documents when an agent should invoke this over local pytest (trigger: `os.getloadavg()[0] > NCPU * 0.75` OR another worktree currently running pytest per `pgrep`).
4. **Fallback on any failure** in the first 5 s of remote connection: log a single line naming the reason (unresolved / connection refused / auth failure / rsync error), invoke local `pytest "$@"` with the same args. This is measured — on failure the pre-commit hook never blocks on the LAN.
5. **Opt-in flag first**: `PYTEST_REMOTE=1` opt-in for the first 30 runs; graduate to default after those runs are recorded in `feature-requests/remote-pytest-runs.jsonl` (identical shape to `research-runs.jsonl`, FR-890 pattern).

## Acceptance Criteria

- [ ] OpenSSH Server + WSL2 + Python 3.11/3.13 + repo-constrained venv provisioned on Huutokauppakone via idempotent WinRM script (extends FR-946's `revive-lmstudio.ps1`).
- [ ] `~/.ssh/huutokauppakone_ed25519` key on the iMac; documented in `reference/development-operations.md`, never committed.
- [ ] `scripts/remote-pytest.sh` end-to-end run: rsync → remote pytest → junit fetch, cold run under 180 s wall-clock on the ~6000-test unit suite.
- [ ] Fallback path verified by test: mock unreachable host → local pytest runs, single log line explains why.
- [ ] `PYTEST_REMOTE=1` opt-in flag documented; default off until 30 clean runs recorded.
- [ ] `feature-requests/remote-pytest-runs.jsonl` schema documented (host, sha, duration_s, passed, failed, fallback_reason).
- [ ] `.github/skills/remote-pytest/SKILL.md` describes the trigger (load-based).
- [ ] `reference/development-operations.md` "Remote Test Execution" section added, including how to add a second worker later.

## Alternatives Considered

- **Self-hosted GitHub Actions runner** on Huutokauppakone. Rejected initial: registering a self-hosted runner puts every repo secret on a LAN Windows host, expanding the trust boundary well beyond what today's LAN posture supports. Revisit if remote-pytest cannot reach 95 % delegation success in the first month.
- **Delete the pre-commit test requirement** (subtractionist option from the research). Rejected here but recorded honestly: this is the cheapest cure and it dissolves the problem class. Kept as the escape hatch if this FR hits a hard obstacle (e.g. WSL2 network partition proves too flaky). Would be its own FR.
- **Celery / RQ / Redis-backed job queue**. Rejected: adds a broker for zero benefit over pytest-xdist's native `--tx ssh=` remote gateway; broker itself becomes new infrastructure to manage.
- **Docker on the Windows host** for env parity. Deferred: WSL2 gives us Linux Python for free; Docker Desktop on Windows would add licensing and daemon overhead. Revisit if WSL2 env drift becomes a maintenance load.

## Witnessed evidence (2026-09-01 discovery session)

- **Delegation target vastly out-classes the iMac** for pytest workload: Ryzen 7 5800X 8C/16T vs Intel i5-10500 6C/12T; 24 GB vs 8 GB RAM; 41 GB / 112 GB disk free vs single-volume mac. A single suite run on the remote box uses <25% of what the iMac gives up locally.
- **OpenSSH.Server capability**: `NotPresent` on Huutokauppakone — confirms the bootstrap installs it for real, not into an already-provisioned host.
- **Docker Desktop / WSL2** already present (default distro `docker-desktop-data`, WSL v2) — the WSL2 install step reduces to "add a dedicated Ubuntu distro," saving the Hyper-V feature-enable reboot cycle.
- **Native Windows Python is 3.10.11** — does NOT match the CI matrix (3.11 / 3.13); rejects the tempting shortcut of running pytest against the native Python. WSL2 is mandatory, not a nice-to-have.
- **File-drop channel (SMB) proven** as a fallback path: `/Volumes/Images` on the mac maps to `C:\Images` on the remote; rsync isn't the only option — a plain `cp` into the mounted share works for one-shot artifact drops.
- **Test-suite reality re-checked**: pytest.ini/conftest currently spawn `pytest -n auto` = 12 workers on the iMac; on the 16-thread remote that becomes 16, which will fit in 24 GB comfortably.

## Related

- Depends on: FR-945 (recon), FR-946 (bootstrap pattern reused for OpenSSH + WSL2).
- Research: [FR-945.research.md](FR-945.research.md).
- Doctrine tie-in: `one_session_one_repo` (remote gets a per-commit clone; SSH boundary respected).
- Dependency governance: consumes `constraints/*.txt` (FR-761) to keep remote venv in lockstep with local.

## Judgement (pending)

To be rendered via `scripts/judge.sh` after FR-945 and FR-946 are committed.
