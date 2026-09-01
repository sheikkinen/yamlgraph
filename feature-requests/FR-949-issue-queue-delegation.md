# Feature Request: GitHub-Issues delegation via self-hosted runner (channel C, coexists with FR-948)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed (rev 3, 2026-09-01: second-judgement R-1..R-7 folded — canonical worker bundle, typed request boundary, checkout credential isolation, Windows-only v1 with Job Object process ownership, total lifecycle/publication ordering, bounded output contract, CAP-258/REQ-YG-637 allocated)
**Effort:** 3 days (re-estimated per R-7: canonical bundle + deployment drift check + Windows Job Object launcher + Windows service witnesses)
**Requested:** 2026-09-01
**Traceability:** CAP-258 / REQ-YG-637 (allocated per R-7; unused after CAP-257/REQ-YG-636)
**First consumer / first event:** the control device (mac) that has just merged a Proposed FR to `sheikkinen/yamlgraph` runs `submit.sh --task judge --payload feature-requests/FR-XXX.md`; the Huutokauppakone Windows service runner claims the triggered workflow within seconds, runs `scripts/judge.sh` in a SHA-pinned checkout, and the complete judgement appears as comments on the delegation issue. **First event:** the next FR judgement that would otherwise saturate the iMac during a supervised enforcement run.
**Research:** [spike-evidence-fr949-gha-runner.md](spike-evidence-fr949-gha-runner.md) (empirical channel C record, 2 live witnesses, 2026-09-01; macOS spike is channel validation ONLY — Windows behavior explicitly unwitnessed there) + the dispositioned alternatives table in § Alternatives Considered. [FR-948.research.md](FR-948.research.md) is shared-pain/channel-A precedent only; it contains no issue-queue candidate.
**Prior art:**
- [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md) [Enforcing] — channel A: WinRM push + SMB return. **NOT superseded**; operator decision 2026-09-01: both channels run until survival evidence decides (§ Coexistence Experiment). FR-949 reuses its SHA-pin, credit-diagnostic, and no-orphan contracts. CAP-257 not modified.
- [FR-949-issue-queue-delegation.judgement.md](FR-949-issue-queue-delegation.judgement.md) — current (second-round) advisory judgement whose R-1..R-7 this revision folds; the first-round judgement (rendered against the channel-B poller design) is in git history at 410db0b1 and its R-1..R-8 dispositions are recorded below.
- First-round judgement dispositions (channel-B round, historical): R-3 claim-recovery state machine deleted (GitHub owns run state), R-7 heartbeat deleted (runner status is a platform API), R-4 collapsed to scoped step credentials, R-6 reduced then re-expanded by the second round into the Windows Job Object contract, R-2 one-repo v1 kept, R-1/R-5/R-8 kept and refit.
- [FR-243-github-issues-remote-inbox.md](FR-243-github-issues-remote-inbox.md) / [FR-251-harden-remote-inbox.md](FR-251-harden-remote-inbox.md) (CAP-106/109) [Implemented] — label lifecycle, author allowlist, body cap precedent. Differs: inbox imports proposals into the local pipeline; FR-949 exports workloads to a remote executor and the issue is the result surface.
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) [Implemented] — channel A precondition; not consumed here (optional diagnostics only).
- [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) [Retired] — SSH+WSL2 design, dismissed per FR-948.
- [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md) [Proposed] — orthogonal (LM Studio inference channel).
- CAP-101/104/105 (A2A) — **retired** capabilities (surfaces deleted after four months without a consumer). Historical precedent; dismissed: inbound listener, no queue durability, no live implementation to reuse.

## Summary

Delegation channel C: a private **comms-only** GitHub repository (`sheikkinen/yamlgraph-delegation`, standing since spike) receives one `delegate`-labeled issue per workload; a **GitHub Actions self-hosted runner on Huutokauppakone (Windows service)** executes an issue-triggered workflow that checks out `sheikkinen/yamlgraph` at the issue-pinned SHA, runs the payload (v1 closed enum: `judge`, `research`) under the workflow's static 30-minute `timeout-minutes` cap with a **Windows Job Object owning the full payload process tree**, and posts the typed run summary plus verified artifact (or bounded redacted failure tail) as comments on the issue. Queue, claim recovery, wall-clock kill, logs, and worker liveness are GitHub platform primitives. The reviewed source of truth for everything the worker executes is one canonical bundle in this repository; the comms repo carries a byte-verified deployed mirror.

## Value Statement

Agents and the operator move judge/research workloads off the saturated iMac through a durable, zero-inbound-surface, platform-supervised queue whose run history lives on the issue — while channel A (FR-948) runs in parallel until the coexistence experiment's separate disposition FR retires one channel.

## Problem

- iMac freezes under concurrent full workloads (operator report 2026-09-01).
- Channel A (FR-948) defends a token crossing an ad-hoc transport with ceremony; one real leak occurred during bootstrap ([diary](../docs/diary/2026-09-01-incident-fr948-token-in-git-config.md)). Pull-only channels delete that problem class — but the second judgement is right that "no token in transit" was too broad: the worker still authenticates outbound to GitHub, and the checkout credential must be provably isolated from the delegated agent (§ 4).
- The channel-B poller design was judged at 24 ACs, most reimplementing platform primitives. The spike proved the runner delivers queue, timeout, and liveness natively — and also falsified the platform-kills-everything assumption (surviving grandchild), which is why process-tree ownership stays in scope.

## Ideal Result

The operator merges a Proposed FR, runs one `submit.sh` command, and walks away. The command itself refuses to submit if the deployed comms bundle has drifted from the reviewed canonical bundle or the Windows runner is offline. Within seconds the runner claims the run, posts a claim comment carrying full identity (target SHA, comms workflow SHA, bundle hash, run ID, runner, UTC), executes the payload in a SHA-pinned disposable checkout whose credentials are removed before the agent starts, and — after cleanup and verification complete — posts the verified artifact and typed machine-readable summary, closing the issue `done`. Failures and timeouts leave the issue open with `failed`, a typed status, and a bounded redacted output tail; recovery is an allowlisted operator re-adding `delegate`. No credential appears in any log, comment, artifact, or the payload environment. Worker health is `gh api .../actions/runners`.

## Proposed Solution

### 1. Canonical worker bundle (R-1)

Source of truth is `.github/skills/issue-delegate/` in THIS repository:

| File | Role |
|---|---|
| `delegate.yml` | the workflow (deployed to comms repo `.github/workflows/delegate.yml`) |
| `models.py` | Pydantic `DelegationRequest`, `DelegationResult`, closed `DelegationStatus`/error models |
| `worker.py` | typed worker entrypoints the workflow steps call (parse/validate, artifact verify, redact, chunk, status resolution) — unit tests invoke these same entrypoints, not duplicated shell |
| `windows_job.ps1` | Job Object launcher (§ 5) |
| `sync-worker.sh` | copies the bundle to frozen comms-repo paths, verifies byte equality after deployment; never copies credentials |
| `submit.sh` + `SKILL.md` | control side (§ 6) |

The comms repository holds a **deployed mirror, not an independent source**. Every submission (not just `--check-worker`) fails closed before issue creation when comms workflow/helper hashes differ from the canonical bundle or the Windows runner is offline. The FR records the deployed comms commit and bundle hash at each deployment. **The exact deployed comms-repo diff receives separate human review (GATE C-2)** — instruction-boundary doctrine: the workflow is CI-like execution infrastructure in another repository.

### 2. Issue contract (R-2)

Exactly one fenced YAML mapping per issue; duplicate-key detection; `extra="forbid"`; parsed by `models.DelegationRequest` in a validation step **before any target checkout**:

```yaml
schema_version: 1
task: judge                     # closed enum: judge | research
sha: <lowercase 40-hex>         # must be an ancestor of freshly fetched origin/main
payload: feature-requests/FR-XXX-name.md
max_reported_credits: 60        # 0 < value <= worker-configured max (60); worker max is authoritative
```

Payload grammar, mechanical: `judge` accepts only committed repo-relative `feature-requests/FR-*.md` excluding `*.judgement.md`; `research` accepts only a committed regular `.md` brief that passes `scripts/research_preflight.py`. Both reject absolute paths, `..`, backslashes, control characters, leading `-`, non-regular files, escaping symlinks, and absence at the requested SHA — all before launch. Target repo **fixed to `sheikkinen/yamlgraph`** in v1; wall-clock cap is the workflow's static `timeout-minutes: 30`; per-issue timeout deferred (recorded decision).

### 3. Workflow lifecycle (R-5 ordering)

Job gate runs **read-only authorization before any mutation**: label == `delegate` AND author in the committed allowlist (excludes `github-actions` and the worker service identity — the recursion guard). A non-allowlisted author produces a workflow-run audit line and **no issue mutation, claim, payload, or `DelegationStatus`**.

Then, in order: claim (label swap + identity comment) → validate (typed refusal path) → checkout (§ 4) → payload under Job Object (§ 5) with incremental redacted capture → **payload termination, checkout removal, volatile credential cleanup, artifact verification, redaction, credit interpretation, and status precedence ALL complete → only then terminal publication** (comments, labels, close). `CLEANUP_FAIL` can therefore affect the published result. `COMMENT_POST_FAIL` is observable in the Actions log/step summary when issue publication itself is down; the issue stays open and never carries `done`.

Platform-failure truth (R-5): a runner loss or platform cancellation can leave an issue open with `claimed` and no terminal comment; the Actions run URL is the durable record; recovery is a documented allowlisted-operator re-label creating a new run ID. No poller, no heartbeat, no custom claim-recovery machinery is reintroduced.

### 4. Checkout credential isolation (R-3)

The single-repo Contents-read PAT is used **only** in the checkout step with `persist-credentials: false`; checkout-created auth headers/helpers are removed before payload launch. The payload step's live preflight proves: no PAT bytes in worktree or env, no `http.*.extraheader`, no credential helper, no askpass, `gh auth status` **fails**, sanitized `git config --show-origin` recorded. One redaction function is applied at every publication boundary: workflow logs, step summaries, comments, tails, artifacts. A literal configured secret anywhere → `TOKEN_LEAK_DETECTED`, artifact not posted. Transformed/encoded exfiltration is a documented residual risk, not claimed impossible.

### 5. Windows process-tree ownership (R-4)

v1 worker is **Huutokauppakone's labeled Windows service runner only**; the macOS spike runner is evidence, not production; no OS-agnostic claim. `windows_job.ps1`: create a Job Object with kill-on-close → launch the payload process **suspended** → assign to the job → resume → record root and descendant identities → close/terminate the job in unconditional cleanup. `TIMEOUT` is valid only with absence proof for root and every recorded descendant; otherwise `PROCESS_TREE_KILL_FAIL` outranks it. Before any live payload, a **service-account preflight** proves: runner survives service restart; Git Bash executes `scripts/judge.sh` and `scripts/research.sh`; Copilot CLI authenticated for that account; Python/project dependencies resolve.

### 6. Control-side `submit.sh`

Refusals (typed, non-zero, actionable stderr): dirty tree; HEAD absent from a **freshly fetched** remote default branch; invalid/missing payload (same normalizer as the worker); malformed options; `YAMLGRAPH_DELEGATED=1`; runner offline; bundle drift. On pass: fill `sha` from `git rev-parse HEAD`, post via `gh issue create`, print issue URL, exit. Mocked test asserts exact argv/body/label/SHA. `--check-worker`: runner status + drift report, never submits.

### 7. Output and artifact identity (R-6)

Success posts a typed run summary + the verified fresh task artifact (`judge`: non-empty `tmp/draft-judgement.md` with a verdict line; `research`: `tmp/draft-alternatives.md` passing the committed verifier). Failure posts the typed summary + a bounded redacted stdout/stderr tail (defined byte limit; defined invalid-UTF-8 and unterminated-line behavior; incremental Windows capture so timeout tails are non-empty — spike finding). Missing/stale/malformed/task-mismatched artifacts fail even on exit 0. Artifact comments: ≤ 60 000 UTF-8 bytes including headers, never splitting a code point, carrying `run <id>`, target SHA, workflow SHA, bundle hash, artifact SHA-256, `part i/N`; ordered reassembly byte-identical to the recorded hash. Terminal machine-readable fields: queue/execution/end-to-end durations, credits (or typed unparseable), task class, final status.

### 8. Statuses

Closed enum, each with a witness, precedence high-to-low: `TOKEN_LEAK_DETECTED` > `PROCESS_TREE_KILL_FAIL` > `TIMEOUT` > `CHECKOUT_FAIL` > `SHA_UNREACHABLE` > `INVALID_REQUEST` > `ARTIFACT_MISSING` > `ARTIFACT_INVALID` > `PAYLOAD_NONZERO` > `CREDIT_FAIL_HIGH` > `CREDIT_FAIL_UNPARSEABLE` > `COMMENT_POST_FAIL` > `CLEANUP_FAIL` > `OK`. (`UNTRUSTED_AUTHOR` removed per R-5: authorization skip precedes delegation and yields no status.) Per-status invariants (payload ran?, absent fields, observability surface, final labels/open-close, relabel validity) are documented and asserted.

### 9. What this FR does NOT do

No retirement of FR-948; no second repo/host; no concurrency > 1; no per-issue timeout; no progress streaming; no automatic retry/recovery; no fleet; no worker write access to code repos; no `remote:` copilot-node key; no automation of human-operated preconditions (runner registration, service-account Copilot auth, PAT creation, comms secrets, bundle deployment — C-7).

## Coexistence Experiment (survival criteria)

Both channels live until each has **10 eligible real runs or 30 UTC days from the first eligible channel-C run** (eligible = real workload on the Windows service runner; deliberate timeout witnesses excluded from success rates). Channel C terminal comments carry the machine-readable fields of § 7; channel A records per FR-948's result JSON. A separate human-reviewed disposition FR compares success rate, babysitting interventions, and durations by task class, then retires one channel by subtraction (C-8). FR-949 collects evidence but may not declare the winner.

## Acceptance Criteria

Adopted verbatim from the second judgement (AC-01..AC-20):

- [ ] AC-01 FR retains the substantive spike record, five genuine solution classes with dissent, every cited prior-art disposition, retired CAP-101/104/105 status, the "channel is not a graph" answer, and Contrib/example classification.
- [ ] AC-02 V1 fixes `sheikkinen/yamlgraph`, Huutokauppakone's labeled Windows service runner, one payload at a time, static 30-minute workflow timeout, and `judge|research`; the macOS runner is evidence only.
- [ ] AC-03 Canonical worker bundle committed (D-2); deterministic sync proves the deployed comms copy byte-identical; every submission refuses offline runner or drift before issue creation; claim/terminal records carry target SHA, comms workflow SHA, bundle hash, run ID, runner, UTC.
- [ ] AC-04 Pydantic models validate the closed request/result/status boundaries; exactly one YAML block, unknown/duplicate keys, schema/task/SHA/credit errors, malformed bodies fail before checkout or launch.
- [ ] AC-05 Task-specific normalization rejects absolute, traversing, backslash, control-character, option-like, wrong-directory, wrong-type, missing, and escaping-symlink payloads; research briefs pass the committed preflight before launch.
- [ ] AC-06 `submit.sh` rejects dirty trees, HEAD absent from freshly fetched remote default, invalid/missing payload, recursion, malformed options, runner unavailability, bundle drift — actionable stderr, non-zero; mocked test asserts exact `gh issue create` argv/body/label/SHA.
- [ ] AC-07 Authorization runs read-only before claim: non-allowlisted authors, `github-actions`, and the worker service identity produce a workflow audit but no issue mutation, payload, or `DelegationStatus`.
- [ ] AC-08 Checkout verifies SHA ancestry against freshly fetched `origin/main` and `HEAD == sha`; PAT is single-repo Contents-read; `persist-credentials: false`; payload preflight proves no PAT bytes, auth header/helper, askpass, GitHub CLI auth, or usable configured GitHub credential.
- [ ] AC-09 One redaction boundary covers logs, step summaries, comments, tails, artifacts; configured-secret fixtures leave zero secret bytes; literal artifact leak yields `TOKEN_LEAK_DETECTED` and no artifact publication; transformed exfiltration documented residual risk.
- [ ] AC-10 Windows service-account preflight proves runner restart survival, Git Bash execution of both launchers, Copilot authentication, Python/project dependencies, and static timeout before live delegation.
- [ ] AC-11 `windows_job.ps1` assigns the suspended payload to a kill-on-close Job Object before resume, records root/descendant identities, cleans up unconditionally; `TIMEOUT` requires absence proof; kill failure yields `PROCESS_TREE_KILL_FAIL` with higher precedence.
- [ ] AC-12 Incremental capture preserves a bounded redacted failure tail at timeout; success publishes only typed summary + verified fresh artifact; failure publishes typed summary + bounded tail; chunks ≤ 60 000 UTF-8 bytes with identity headers, byte-identical reassembly against recorded SHA-256.
- [ ] AC-13 Cleanup and artifact/status resolution precede terminal publication; every status has a direct witness and documented invariants; `COMMENT_POST_FAIL` is visible in Actions and can never close an issue as `done`.
- [ ] AC-14 Runner-loss/platform-cancellation behavior documented and witnessed without custom recovery: stranded `claimed` issue points to the Actions run, remains open; allowlisted operator relabel creates a distinct run ID.
- [ ] AC-15 Offline tests use no network, real `gh`, real runner, real secret, or host mutation; they invoke the same typed helper entrypoints as the workflow; every test carries `@pytest.mark.req("REQ-YG-637")`.
- [ ] AC-16 Real Windows judge witness under the service account: committed Proposed FR at pinned SHA → complete verified judgement with identity/timing/credit fields → `done`+closed, no checkout/credential residue, promoted by the control device.
- [ ] AC-17 Real Windows timeout witness: named long-lived descendant, root/descendant identities recorded, all absent after Job Object cleanup, `failed`+`TIMEOUT`+bounded tail, no residue, excluded from experiment success counts.
- [ ] AC-18 Coexistence record defines eligible runs and records task class, queue/execution/end-to-end duration, credits, status, babysitting interventions for 10 eligible runs or 30 UTC days; FR-949 neither selects nor retires a channel.
- [ ] AC-19 CAP-258/REQ-YG-637, strict requirement coverage, generated architecture, skill and operations docs, changelog fragment, implementation status, sanitized cross-repo/live evidence, diary reflection committed.
- [ ] AC-20 Current-repo diff changes no file outside D-1..D-8; the exact deployed comms-repo diff receives separate human review before live use.

## Alternatives Considered

| # | Solution class | Verdict | Dissent preserved |
|---|---|---|---|
| A | WinRM push + SMB return (FR-948) | **Coexists** (operator decision) | Immediate dispatch, no GitHub dependency for execution. Loses on token transit ceremony, synchronous partition fragility, PID-capture race. Experiment decides. |
| B | Private comms repo + custom 2-min poller | **Rejected after first judgement + spike** | Judged at 24 ACs, most reimplementing runner primitives (claim recovery, heartbeat, wall-clock kill). Preserved dissent: B owns every failure mode, no runner install; revisit only if GitHub Actions availability becomes the observed bottleneck. |
| C | **Self-hosted GHA runner on comms repo** | **Chosen (this FR)** | Spiked: 26 s happy path, native timeout, per-step credential scope. Costs: runner install/supervision, deepest vendor coupling, process-tree ownership still ours (witnessed orphan), cross-repo workflow identity must be mechanically enforced (R-1). |
| D | `act` (nektos) local workflow execution | Rejected | No queue (needs a poller to invoke it — reintroduces B); Linux-container execution hides host Copilot CLI/auth. CI-debug tool, wrong class. |
| E | A2A server on worker (CAP-101/104/105, retired) | Rejected | Inbound listener; capabilities retired without consumer; no queue durability. |
| F | Do nothing (channel A only) | Rejected | Forfeits the empirical comparison; leaves token-transit ceremony as the sole path. |

**Not a graph** (substantive disposition): the channel is a process boundary between machines; its payloads invoke the existing graph-backed launchers (`scripts/judge.sh`, `scripts/research.sh`). No YAMLGraph graph or prompt changes; no map/fan-out shape exists here to express in YAML.

## Deliverables (frozen, second judgement D-1..D-8)

| D | Surface |
|---|---|
| D-1 | `.github/skills/issue-delegate/SKILL.md` and `submit.sh` (submission, mandatory pre-submit worker/bundle checks, `--check-worker`, recursion refusal) |
| D-2 | `.github/skills/issue-delegate/delegate.yml`, `models.py`, `worker.py`, `windows_job.ps1`, `sync-worker.sh` — canonical reviewed worker bundle |
| D-3 | `tests/unit/test_issue_delegate.py` + sanitized fixtures (request parsing, submit argv/body, drift, credentials, Windows process ownership, capture, artifacts, statuses, API failures, lifecycle) |
| D-4 | `capabilities/CAP-258-issue-delegation-runner.yaml`, `REQ-YG-637` markers, strict coverage, generated `ARCHITECTURE.md` traceability |
| D-5 | `reference/development-operations.md` issue-delegation subsection (runner-service, PAT-scope, deployment, recovery, verification commands) |
| D-6 | `changelog/unreleased/fr-949-issue-delegation-runner.md` |
| D-7 | This FR: folded revisions, implementation status, comms commit/bundle identity, sanitized Windows witnesses |
| D-8 | `docs/diary/2026-09-XX-fr949-runner-delegation.md` with a `Seed:` |
