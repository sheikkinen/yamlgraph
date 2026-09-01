# Feature Request: GitHub-Issues delegation via self-hosted runner (channel C, coexists with FR-948)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed (refit 2026-09-01: executor changed from custom poller to GHA self-hosted runner after spike evidence; first judgement round R-1..R-8 folded where they survive the redesign)
**Effort:** 1.5 days
**Requested:** 2026-09-01
**First consumer / first event:** the control device (mac) that has just merged a Proposed FR to `sheikkinen/yamlgraph` runs `submit.sh --task judge --payload feature-requests/FR-XXX.md`; the self-hosted runner on the worker box claims the triggered workflow within seconds, runs `scripts/judge.sh` in a SHA-pinned checkout, and the complete judgement appears as comments on the delegation issue. **First event:** the next FR judgement that would otherwise saturate the iMac during a supervised enforcement run.
**Research:** [spike-evidence-fr949-gha-runner.md](spike-evidence-fr949-gha-runner.md) (empirical channel C record, 2 live witnesses, 2026-09-01) + the dispositioned alternatives table in § Alternatives Considered — declared per first-judgement R-1 as this FR's committed research record. [FR-948.research.md](FR-948.research.md) is shared-pain/channel-A precedent only; it contains no issue-queue candidate.
**Prior art:**
- [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md) [Enforcing] — channel A: WinRM push + SMB return. **NOT superseded**; operator decision 2026-09-01: both channels run until survival evidence decides (§ Coexistence Experiment). FR-949 reuses its SHA-pin, credit-diagnostic, and no-orphan contracts.
- [FR-949 first judgement](FR-949-issue-queue-delegation.judgement.md) [advisory, rendered against the channel-B poller design] — R-1..R-8 folded as follows: R-1 research/prior-art corrections kept; R-2 one-repo v1 kept; R-3 claim-recovery state machine **deleted** (GitHub owns run state — spike table row 1); R-4 kept, collapsed to per-step `env:` scope (witnessed); R-5 kept for >64 KiB artifacts only; R-6 kept in reduced form (process-group cleanup — spike's orphan finding); R-7 heartbeat **deleted** (runner online status is a GitHub API primitive); R-8 deliverable table kept, refit below.
- [FR-243-github-issues-remote-inbox.md](FR-243-github-issues-remote-inbox.md) / [FR-251-harden-remote-inbox.md](FR-251-harden-remote-inbox.md) (CAP-106/109) [Implemented] — label lifecycle, author allowlist, body cap precedent. Differs: inbox imports proposals into the local pipeline; FR-949 exports workloads to a remote executor and the issue is the result surface.
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) [Implemented] — channel A precondition; not consumed here (optional diagnostics only).
- [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) [Retired] — SSH+WSL2 design, dismissed per FR-948.
- [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md) [Proposed] — orthogonal (LM Studio inference channel).
- CAP-101/104/105 (A2A) — **retired** capabilities (server/client surfaces deleted after four months without a consumer, per first-judgement R-1 correction). Historical precedent for LAN delegation; dismissed: inbound listener, no queue durability, no live implementation to reuse.

## Summary

Delegation channel C: a private **comms-only** GitHub repository (`sheikkinen/yamlgraph-delegation`, exists since spike) receives one `delegate`-labeled issue per workload; a **GitHub Actions self-hosted runner** on the worker box executes an issue-triggered workflow that checks out `sheikkinen/yamlgraph` at the issue-pinned SHA, runs the payload (v1 closed enum: `judge`, `research`) under GitHub's native `timeout-minutes` cap, and posts **all agent output as comments on the issue**. Queue, claim recovery, wall-clock kill, logs, and worker liveness are GitHub platform primitives, not our code. Spiked end-to-end 2026-09-01: happy path 26 s job / ~40 s issue-to-closed; timeout kill exact at the cap.

## Value Statement

Agents and the operator move judge/research workloads off the saturated iMac through a durable, zero-inbound-surface, platform-supervised queue whose entire run history lives on the issue — with an order of magnitude less custom code than the judged channel-B poller — while channel A (FR-948) runs in parallel until the coexistence experiment retires one channel.

## Problem

- iMac freezes under concurrent full workloads (operator report 2026-09-01).
- Channel A (FR-948) defends a token crossing an ad-hoc transport with ceremony (byte-scan, in-memory redaction, PS 5.1 job PID capture); one real leak occurred during bootstrap ([diary](../docs/diary/2026-09-01-incident-fr948-token-in-git-config.md)). Pull-only channels delete that problem class.
- The channel-B poller design was judged (AWR) at 24 ACs, most reimplementing what GitHub Actions ships natively — queue recovery, wall-clock cap, heartbeat, idempotent retry. The spike proved the runner delivers those as platform primitives with one ~60-line workflow.

## Ideal Result

The operator merges a Proposed FR, runs one `submit.sh` command, and walks away. Within seconds the runner claims the workflow run, posts a claim comment, executes the payload in a SHA-pinned disposable checkout, and posts the complete judgement/research artifact to the issue, closing it `done`. Failures and timeouts leave the issue open with `failed`, a typed reason, and the captured output tail; retry is the operator re-adding the `delegate` label. No credential leaves either machine; the delegated agent's environment contains no usable GitHub token. Worker health is `gh api .../actions/runners` — no bespoke heartbeat. The channel's per-run record (queue delay, execution duration, credits) accumulates on the issues as machine-readable evidence for the A-vs-C disposition FR.

## Proposed Solution

### 1. Surfaces (already partially standing from the spike)

- **Comms repo** `sheikkinen/yamlgraph-delegation` (private): labels `delegate`/`claimed`/`done`/`failed`; workflow `.github/workflows/delegate.yml` — source of truth lives in the comms repo; a reviewed canonical copy is committed in this repo under `.github/skills/issue-delegate/delegate.yml` with a documented sync step (drift between the two is a witnessed failure class, checked by `submit.sh --check-worker`).
- **Worker**: v1 target is Huutokauppakone (runner as Windows service, single-instance); the spike's macOS runner (`imac-spike`) remains registered as the fallback/witness host. The workflow is OS-agnostic except the process-group cleanup step, which has macOS and Windows variants.
- **Control side**: `.github/skills/issue-delegate/` — `SKILL.md` + `submit.sh`.

### 2. Issue contract (control → worker)

Fenced YAML block, single block per issue, unknown/duplicate keys rejected (first-judgement R-2 typed boundary, enforced by a validation step in the workflow before any checkout):

```yaml
schema_version: 1
task: judge                     # closed enum: judge | research
sha: <40-hex>                   # must be reachable from origin/main of the target repo
payload: feature-requests/FR-XXX-name.md
max_reported_credits: 60        # post-run diagnostic threshold (FR-948 semantics)
```

Target repo is **fixed to `sheikkinen/yamlgraph` in v1** (first-judgement R-2). Operator's configurability requirement is recorded as the named follow-up FR trigger: the first real delegation need from a second repo. Wall-clock cap is the workflow's static `timeout-minutes: 30` (platform-enforced); per-issue timeout variation is out of v1 (recorded decision — `timeout-minutes` cannot read issue input; an inner `timeout(1)` wrapper is deferred until a real need).

Payload grammar (first-judgement R-2, kept): `judge` accepts only normalized repo-relative `feature-requests/FR-*.md` excluding `*.judgement.md`; `research` accepts only committed brief paths accepted by `scripts/research.sh`. Absolute paths, `..`, `\`, control characters, leading `-`, or missing-at-SHA files fail typed before payload launch.

### 3. Workflow contract (worker side)

Job gate: label == `delegate` AND issue author in the committed allowlist (CAP-109 transplant; the allowlist excludes `github-actions` and any worker service account — this is the recursion guard). Steps:

1. **claim**: swap label `delegate`→`claimed`; comment `claimed by <runner> — run <id> — <utc>` (`github.token`, issues-write only).
2. **validate**: parse + validate the YAML block (typed refusals as `failed` comment; no checkout on refusal).
3. **checkout**: target repo at `sha` via a fine-grained PAT repo secret (Contents read-only, single repo); verify `git merge-base --is-ancestor <sha> origin/main` and `HEAD == sha`.
4. **payload** (credential-scrubbed step): env contains `YAMLGRAPH_DELEGATED=1` and **no** `GH_TOKEN`/`GITHUB_TOKEN`/askpass (witnessed in spike: `scrub-ok`); child launched in its own **process group**; stdout/stderr captured incrementally via `tee` (spike finding: redirect-only loses output on kill). Runs `scripts/judge.sh <payload>` or `scripts/research.sh <payload>`.
5. **artifact check**: `judge` requires non-empty `tmp/draft-judgement.md` with a verdict line; `research` requires verified `tmp/draft-alternatives.md` (launcher contracts, first-judgement R-5). Missing/malformed → `failed` even on exit 0. Credit line parsed; over `max_reported_credits` → `failed` with `CREDIT_FAIL_HIGH`.
6. **post output** (`if: always()`): redact (single boundary function: PAT patterns + configured literals) → post typed summary + artifact as comments, UTF-8-byte-safe chunks ≤ 60 000 bytes with `run <id> artifact sha256 <hash> part i/N` headers; label `done`+close or `failed`+leave-open.
7. **cleanup** (`if: always()`): kill the payload **process group** (spike's paid lesson: GitHub's cancel does not kill grandchildren — witnessed orphan `sleep 600`); remove checkout; cleanup failure posts visibly, never silent.

### 4. Control-side `submit.sh`

Refusals (typed, non-zero, actionable stderr): dirty tree; HEAD not an ancestor of `origin/main`; payload missing at HEAD; malformed options; `YAMLGRAPH_DELEGATED=1` in env. On pass: fill `sha` from `git rev-parse HEAD`, post via `gh issue create --repo sheikkinen/yamlgraph-delegation --label delegate`, print issue URL, exit. `--check-worker` mode: reports runner online/offline via `gh api .../actions/runners` and comms-repo workflow vs. canonical copy drift; never submits in check mode.

### 5. Statuses

Closed enum, each with a witness, precedence high-to-low: `TOKEN_LEAK_DETECTED` > `PROCESS_GROUP_KILL_FAIL` > `TIMEOUT` > `CHECKOUT_FAIL` > `SHA_UNREACHABLE` > `INVALID_REQUEST` > `UNTRUSTED_AUTHOR` > `ARTIFACT_MISSING` > `ARTIFACT_INVALID` > `PAYLOAD_NONZERO` > `CREDIT_FAIL_HIGH` > `CREDIT_FAIL_UNPARSEABLE` > `COMMENT_POST_FAIL` > `CLEANUP_FAIL` > `OK`. (Down from channel B's 18: `INTERRUPTED`, `FETCH_FAIL` reconciliation, and heartbeat classes are GitHub-owned.)

### 6. What this FR does NOT do

- No retirement of FR-948 (coexistence experiment).
- No second target repo, no fleet, no concurrency > 1 (`concurrency:` group serializes), no per-issue timeout, no progress streaming, no `remote:` copilot-node key.
- No worker write access to any code repo; the comms repo is the only surface the workflow writes.
- No automation of one-time preconditions: comms repo (exists), runner registration on Huutokauppakone, PAT secrets — documented with verification commands (first-judgement C-6).

## Coexistence Experiment (survival criteria)

Both channels live until each has **10 eligible real runs or 30 UTC days from the first eligible channel-C run**, whichever first. Deliberate timeout witnesses excluded from success rates. Per-run machine-readable fields in channel C's terminal comments: queue delay, execution duration, end-to-end duration, credits, status. Channel A records per FR-948's result JSON. A separate disposition FR compares success rate, babysitting interventions, and duration by task class, then retires one channel by subtraction; a split verdict must be argued, not defaulted. FR-949 collects evidence but may not declare the winner.

## Acceptance Criteria

- [ ] AC-1 FR records the corrected research/prior-art record: spike evidence declared as research, A2A capabilities as retired, contrib/example classification, substantive not-a-graph disposition (channel = process boundary; payloads invoke existing graph-backed launchers).
- [ ] AC-2 `submit.sh` refusals (dirty tree, unpushed HEAD, missing payload, recursion, malformed options) each witnessed with actionable stderr + non-zero exit; mocked `gh` test asserts exact issue argv/body/label/SHA.
- [ ] AC-3 Workflow validation rejects: unknown/duplicate keys, multiple/missing YAML blocks, bad task, non-40-hex SHA, payload grammar violations, SHA unreachable from `origin/main` — each → `failed` + typed comment, no payload launch.
- [ ] AC-4 Author allowlist gates the job; non-allowlisted author leaves the issue unmodified except a skip audit; worker service account and `github-actions` are excluded (recursion witness).
- [ ] AC-5 Credential isolation witnessed live: payload step env has no `GH_TOKEN`/`GITHUB_TOKEN`/askpass; `gh auth status` fails in the payload step; checkout PAT is Contents-read-only on one repo and appears in no log, comment, or artifact.
- [ ] AC-6 Redaction boundary tested directly: fixture with configured token → posted bodies contain zero token bytes; literal leak in artifact → `TOKEN_LEAK_DETECTED`, artifact not posted.
- [ ] AC-7 Artifact posting: >60 000-byte artifact → byte-safe chunks with hash headers, reassembly byte-identical; artifact-missing/invalid and credit-threshold failures typed even on exit 0.
- [ ] AC-8 Process-group cleanup witnessed: timeout run leaves no surviving payload descendants (the spike's orphan class); kill failure → `PROCESS_GROUP_KILL_FAIL` outranks `TIMEOUT`.
- [ ] AC-9 Every status enum member has a witness (offline mock or live); precedence deterministic; label/close invariants per status documented and asserted.
- [ ] AC-10 Offline tests: no network, no real `gh`, no runner; `@pytest.mark.req` with the allocated REQ ID.
- [ ] AC-11 Live witness 1 (judge): real Proposed FR judged remotely; complete judgement on the issue; `done`+closed; verdict promoted to committed `.judgement.md` by the control device. Recorded in this FR.
- [ ] AC-12 Live witness 2 (timeout): long payload killed at the cap; `failed`+`TIMEOUT`+output tail on the issue; no surviving process group; recorded and excluded from experiment success counts.
- [ ] AC-13 Windows-worker witness on Huutokauppakone (runner as service) before channel C runs count toward the experiment; until then macOS runner witnesses are channel-validation only.
- [ ] AC-14 Docs: SKILL.md, canonical workflow copy + sync check, preconditions with verification commands, CAP/REQ allocation, changelog fragment, diary reflection.

## Alternatives Considered

| # | Solution class | Verdict | Dissent preserved |
|---|---|---|---|
| A | WinRM push + SMB return (FR-948) | **Coexists** (operator decision) | Immediate dispatch, no GitHub dependency for execution. Loses on token transit ceremony, synchronous partition fragility, PID-capture race. Experiment decides. |
| B | Private comms repo + custom 2-min poller | **Rejected after judgement + spike** | First judgement priced it honestly: 24 ACs, R-3 claim-recovery state machine, R-7 heartbeat — all reimplementing runner primitives. Preserved dissent: B owns every failure mode and adds no runner install; revisit only if GitHub Actions availability becomes the observed bottleneck. |
| C | **Self-hosted GHA runner on comms repo** | **Chosen (this FR)** | Spiked: 26 s happy path, native timeout, per-step credential scope. Costs: runner install/supervision, deepest vendor coupling, grandchild-orphan cleanup is still ours (witnessed). |
| D | `act` (nektos) local workflow execution | Rejected | No queue (needs a poller to invoke it — reintroduces B), Linux-container execution hides host Copilot CLI/auth. CI-debug tool, wrong class. |
| E | A2A server on worker (CAP-101/104/105, retired) | Rejected | Inbound listener; capabilities retired without consumer; no queue durability. |
| F | Do nothing (channel A only) | Rejected | Forfeits the empirical comparison; leaves token-transit ceremony as sole path. |

## Deliverables (refit of first-judgement R-8)

| D | Surface |
|---|---|
| D-1 | `.github/skills/issue-delegate/SKILL.md`, `submit.sh` (submit / `--check-worker` / recursion refusal) |
| D-2 | `.github/skills/issue-delegate/delegate.yml` canonical workflow copy + comms-repo sync documentation |
| D-3 | `tests/unit/test_issue_delegate.py` + fixtures (submit refusals, validation, redaction, chunking, status precedence) |
| D-4 | `capabilities/CAP-*-issue-delegation-runner.yaml` + REQ markers + generated traceability |
| D-5 | `reference/development-operations.md` delegation subsection (runner preconditions, PAT scopes, verification commands) |
| D-6 | Changelog fragment |
| D-7 | This FR updated with implementation status + sanitized witnesses |
| D-8 | `docs/diary/2026-09-XX-fr949-runner-delegation.md` with a `Seed:` |
