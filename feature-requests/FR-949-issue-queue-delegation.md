# Feature Request: GitHub-Issues delegation queue (channel B, coexists with FR-948)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-09-01
**First consumer / first event:** the control device (mac) that has just merged a Proposed FR to the main repo posts one `delegate`-labeled issue to the private comms repo ("judge feature-requests/FR-XXX.md at SHA `<sha>`"); within one poll interval Huutokauppakone claims it, runs `scripts/judge.sh` in a detached worktree at that SHA, and the full judgement text appears as comments on that issue. **First event:** the next FR judgement that would otherwise saturate the iMac during a supervised enforcement run.
**Research:** [FR-948.research.md](FR-948.research.md) (delegation-channel alternatives, shared arc) + the in-body dispositioned alternatives table in § Alternatives Considered (FR-889 style) — channel B was proposed by the operator after FR-948's third judgement round; the table dispositions it against every channel class already evaluated.
**Prior art:**
- [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md) [Enforcing] — channel A: WinRM push + SMB artifact return. **NOT superseded.** Operator decision 2026-09-01: run both channels concurrently and let survival evidence decide (§ Coexistence Experiment). FR-949 deliberately reuses FR-948's SHA-frozen-worktree, credit-parsing, and wall-clock-cap contracts.
- [FR-243](FR-243-github-issues-remote-inbox.md) / [FR-251](FR-251-harden-remote-inbox.md) (CAP-106/109, `.chaplain/lib/watcher/inbox_sync.sh`) [Implemented] — the proven label-lifecycle + author-allowlist + body-cap + audit-header pattern this FR transplants. Differs: inbox imports proposals INTO the local pipeline; FR-949 exports workloads OUT to a remote executor, and the issue itself is the result surface.
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) [Implemented] — channel A's precondition. FR-949 does not consume the recon receipt; recon demotes to optional diagnostics for this channel.
- [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) [Retired, superseded by FR-948] — SSH+WSL2 design; dismissed, same rationale as in FR-948.
- [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md) [Proposed] — orthogonal (LM Studio inference, not workload delegation).
- [CAP-101](../capabilities/CAP-101-a2a-call-node.yaml) / [CAP-104](../capabilities/CAP-104-a2a-server-reference-docs.yaml) / [CAP-105](../capabilities/CAP-105-a2a-consumer-phase2.yaml) — A2A HTTP delegation exists as framework capability. Dismissed for this channel: requires an inbound listener on the Windows box (same exposure class WinRM already covers via channel A); the point of channel B is zero inbound surface.

## Summary

A private GitHub repository used **for comms only** (no code): the control device posts one issue per delegated workload; a poller service on Huutokauppakone (2-min interval) claims the issue, checks out the **target repo** (default `yamlgraph`, configurable) at the issue-pinned SHA in a disposable detached worktree, runs the named payload (v1: `judge`, `research`) under a wrapper-owned wall-clock deadline, and posts **all agent output as comments on the originating issue**. Pull-only: no inbound port, no token in transit, no SMB.

## Value Statement

Agents and the operator delegate judge/research workloads off the saturated iMac through a durable, observable, zero-inbound-surface queue whose entire run history lives on the issue — while channel A (FR-948) runs in parallel until survival evidence retires one of them.

## Problem

- Same pain as FR-948: iMac freezes under concurrent full workloads (operator report 2026-09-01).
- Channel A defends a token crossing an ad-hoc transport with ceremony (byte-scan, in-memory redaction, PS 5.1 job PID capture); one real leak already occurred during bootstrap ([diary](../docs/diary/2026-09-01-incident-fr948-token-in-git-config.md)). A pull model deletes that problem class instead of defending it: no credential ever leaves either machine.
- Channel A is synchronous — a network partition mid-run yields ambiguous state. A queue is durable across partitions, reboots, and either end being offline.
- Which trade-off wins (latency + a stateful poller vs. transport ceremony + synchronous fragility) is an empirical question. Both channels must run against real workloads to answer it.

## Ideal Result

The operator (or an agent on the control device) merges a Proposed FR to the main repo, runs one command that posts a `delegate` issue pinning task, repo, SHA, payload path, timeout, and credit cap — and walks away. Within ~2 minutes Huutokauppakone claims the issue (comment: host, start time, SHA verified), executes the payload in a throwaway worktree, and posts the complete judgement/research artifact as issue comments, closing the issue with a `done` label. On any failure the issue stays open with `failed`, a typed reason, and the log tail — nothing to ssh into, nothing to mount. A stale poller is visible from the control device via a heartbeat timestamp older than 3 poll intervals. `GH_TOKEN`/PAT bytes appear in no issue, comment, or committed file.

## Proposed Solution

### 1. Comms repo (new, private, no code)

- e.g. `sheikki/yamlgraph-delegation` — issues + labels only. Created manually by the operator (one-time; out of enforcement scope, documented as precondition).
- Labels: `delegate` (queued) → `claimed` → `done` | `failed`. One workload = one issue.
- A single pinned `heartbeat` issue whose body the poller edits each cycle with `last_poll_utc`, host, poller version SHA (body edits generate no notifications).

### 2. Issue contract (control → remote)

Issue body = YAML in a fenced block; poller parses only the block, ignores prose:

```yaml
task: judge                     # v1 closed enum: judge | research
repo: sheikki/yamlgraph         # target repo; default main repo, CONFIGURABLE
sha: <40-hex>                   # must be reachable from the target repo's default branch
payload: feature-requests/FR-XXX-name.md   # path at that SHA (judge: FR file; research: brief)
timeout_s: 1800                 # wall-clock cap, poller-owned kill (operator cap mechanism)
max_reported_credits: 60        # post-run acceptance threshold, FR-948 semantics
```

Flow for the primary payload (remote judge): control device drafts the FR, **merges it to the target repo's default branch** (Status: Proposed), then posts the issue with the merge SHA. The remote never needs write access to the target repo — read-only fetch is sufficient, and the verdict returns via issue comments. The control device promotes the verdict comment to the committed `.judgement.md` (authorship boundary stays on the control side).

### 3. Control-side helper: `.github/skills/issue-delegate/`

Thin skill (sibling of `lan-delegate`): `submit.sh --task judge --payload feature-requests/FR-XXX.md [--repo OWNER/NAME] [--timeout 1800]`:

1. Refuse if local tree dirty (`git status --porcelain` non-empty) or HEAD not pushed to the default branch (`git merge-base --is-ancestor HEAD origin/<default>`).
2. Refuse if payload path absent at HEAD.
3. Fill `sha:` from `git rev-parse HEAD`; post via `gh issue create --repo <comms-repo> --label delegate`.
4. Print the issue URL; exit. No polling, no waiting — the issue IS the tracking surface.
5. Recursion guard: refuse if `YAMLGRAPH_DELEGATED=1` in env (a delegated run must not enqueue further delegations).

### 4. Remote poller service (versioned in main repo, runs on Huutokauppakone)

`scripts/delegation_poller.py` (Python; matches remote's existing runtime) + a documented Windows Scheduled Task (2-min interval, single-instance). Config file `delegation-poller.toml` on the remote names: comms repo, target-repo allowlist (default `sheikki/yamlgraph`), canonical clone path, poll interval, default timeout. Per cycle:

1. **Heartbeat**: edit the heartbeat issue body with `last_poll_utc`.
2. List open `delegate` issues, oldest first, **claim at most one** (v1 concurrency = 1): swap label `delegate`→`claimed`, comment `claimed by <host> at <utc>, poller sha <sha>`.
3. **Author allowlist** (CAP-109 transplant): only issues authored by logins in the config allowlist are claimed. The poller's own service account is NOT on the allowlist — this makes the allowlist double as the recursion guard (a remote-created issue is never claimed).
4. **Body cap** (CAP-109): YAML block > 10 000 chars → `failed` with typed reason.
5. Validate the YAML block (closed task enum, 40-hex SHA, repo in allowlist, payload path grammar, timeout bounds). Any violation → comment typed reason, label `failed`, never executed.
6. Fetch target repo (read-only PAT), verify SHA is reachable from default branch, `git worktree add --detach <runs>\<issue-num> <sha>` (FR-948 § 5 contract, minus WinRM).
7. Run the payload with a **poller-owned process-tree deadline** (`subprocess` + `timeout_s` + `taskkill /T /F` on the directly-owned PID — no PID guessing): `judge` → `scripts/judge.sh <payload>`; `research` → `scripts/research.sh <payload>`. Child env gets `YAMLGRAPH_DELEGATED=1`.
8. **All output to the issue**: final artifact (judgement md / research record) posted as comment(s), chunked at 60 000 chars each, `part i/N` headers. On failure/timeout: typed status + last 100 log lines as a comment. Credit line parsed per FR-948 semantics; over-threshold → `failed` even on exit 0.
9. **Redaction at the print boundary, unconditional**: every comment body passes one redaction function (PAT patterns + literal configured token values) before `gh` is invoked — not per-callsite opt-in.
10. Label `done` + close, or `failed` + leave open. Worktree removed in `finally`; removal failure → `failed` comment (visible, not silent).

### 5. What this FR does NOT do

- No retirement of FR-948 (explicit operator decision — coexistence experiment).
- No fleet/multi-host, no concurrency > 1, no `remote:` copilot-node key (diary seed stays a seed).
- No progress streaming beyond claim + final + failure comments (v1).
- No write access from remote to any code repo; comms repo is the only surface the remote writes.
- No auto-creation of the comms repo or the Scheduled Task (documented preconditions with verification commands, per FR-948's precedent for remote-side preconditions).

## Coexistence Experiment (survival criteria)

Both channels stay live until **10 real delegations per channel or 30 days**, whichever first. Ledger: channel B's issue labels are self-recording; channel A's runs recorded per FR-948's result JSON. Disposition FR then compares: success rate, operator babysitting interventions (count), end-to-end wall clock overhead vs. local run, and incident count. The losing channel is retired by a subtraction FR; a split verdict (each wins a payload class) must be argued explicitly, not defaulted to keeping both.

## Acceptance Criteria

- [ ] AC-1 `submit.sh` refuses: dirty tree, unpushed HEAD, missing payload, `YAMLGRAPH_DELEGATED=1` — each with actionable stderr, non-zero exit.
- [ ] AC-2 `submit.sh` posts a well-formed issue (label, YAML block, HEAD SHA) — mocked `gh` unit test asserting exact argv.
- [ ] AC-3 Poller claims oldest allowlisted `delegate` issue only; non-allowlisted author skipped with label retained (CAP-109 semantics).
- [ ] AC-4 Poller validation rejects: bad task, non-40-hex SHA, repo outside allowlist, oversized body, SHA unreachable from default branch — each → `failed` + typed comment, payload never executed.
- [ ] AC-5 Deadline: mocked long-running child killed at `timeout_s` via directly-owned PID; status `TIMEOUT` commented; no orphan process (unit: kill called with the tracked PID).
- [ ] AC-6 Output chunking: artifact > 60 000 chars → N comments with `part i/N` headers, byte-identical reassembly.
- [ ] AC-7 Redaction: fixture comment containing a configured token value → posted body contains zero token bytes (single boundary function, tested directly).
- [ ] AC-8 Recursion: issue authored by the poller's own service account never claimed.
- [ ] AC-9 Heartbeat body updated every cycle; control-side `submit.sh --check-poller` reports stale if older than 3 intervals.
- [ ] AC-10 Worktree removed on success, failure, and timeout paths (unit fixtures for all three).
- [ ] AC-11 Live witness 1 (judge): a real Proposed FR judged remotely; full judgement appears on the issue; `done` + closed; verdict promoted to committed `.judgement.md` by control device. Recorded in this FR body.
- [ ] AC-12 Live witness 2 (timeout): `timeout_s=5` against a long prompt; `failed` + `TIMEOUT` comment + log tail; no surviving process (follow-up query); no token bytes anywhere on the issue. Recorded in this FR body.
- [ ] AC-13 Unit tests offline (no network, no `gh`, no git remotes); `@pytest.mark.req` tags on all tests.
- [ ] AC-14 Docs: skill SKILL.md + remote preconditions (comms repo, PAT scopes: comms-repo read/write issues, target-repo read-only; Scheduled Task registration) with verification commands.

## Alternatives Considered

| # | Solution class | Verdict | Dissent preserved |
|---|---|---|---|
| A | WinRM push + SMB return (FR-948) | **Coexists** (operator decision) | Immediate dispatch, no queue latency, no stateful remote service. Loses on: token transit ceremony, synchronous partition fragility, PS 5.1 PID capture. Survival experiment decides. |
| B | **Private comms repo + issue queue + 2-min poller** | **Chosen (this FR)** | ~2 min latency; one stateful service needing a heartbeat. Wins on: zero inbound surface, no token in transit, durable queue, issue = full audit trail, CAP-106/109 pattern proven in-repo. |
| C | Self-hosted GitHub Actions runner on the comms/private repo | Rejected v1, **named revisit trigger** | GitHub's own long-poll, native `timeout-minutes`, artifacts, logs — strictly less custom code than B. Rejected: heavier remote install, runner supervision opaque vs. a 200-line poller we own, and FR-948's D-rejection (secret surface) only partially neutralized. Revisit if B's poller requires > 2 babysitting interventions in the experiment window. |
| D | A2A server on remote (CAP-101/104/105) | Rejected | Inbound HTTP listener on the Windows box — the exposure class channel B exists to avoid; A2A adds framework coupling for no queue durability. |
| E | Do nothing (channel A only) | Rejected | Leaves the token-transit ceremony as the sole path; forfeits the empirical comparison the operator asked for. |

## Open Questions (for the Judge)

1. Poll interval 2 min fixed vs. config-only — is a `--once` mode required for testability? (Proposed: yes, `--once` is the unit-test entry point.)
2. Should `failed` issues auto-retry once on transient classes (fetch failure), or is v1 strictly one-shot? (Proposed: one-shot; retry = operator re-labels `delegate`.)
