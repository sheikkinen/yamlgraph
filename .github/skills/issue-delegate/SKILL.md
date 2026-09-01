---
name: issue-delegate
description: "Submit ONE committed-and-pushed judge or research workload to the FR-949 issue-queue delegation channel (private comms repo sheikkinen/yamlgraph-delegation, self-hosted Windows service runner). Use when: a judge/research payload would otherwise saturate the local machine AND the payload is committed at a pushed HEAD AND the delegate-labeled runner is online AND the deployed comms bundle matches the canonical bundle. Not a fleet manager; not a general remote-exec channel; refuses recursive delegation, dirty trees, unpushed HEADs, and bundle drift."
argument-hint: "task + payload, e.g. `--task judge --payload feature-requests/FR-XXX-name.md` (or `--check-worker`)"
---

# Issue-queue delegation skill (FR-949, REQ-YG-637)

Channel C: delegation via GitHub Issues in the private comms repo
`sheikkinen/yamlgraph-delegation`, executed by Huutokauppakone's labeled
Windows **service** runner in a SHA-pinned, credential-isolated disposable
checkout. Coexists with channel A (FR-948 LAN/WinRM) until a separate
disposition FR — see the coexistence record in the FR.

## Submitting

```bash
.github/skills/issue-delegate/submit.sh --task judge \
  --payload feature-requests/FR-XXX-name.md
# optional: --repo owner/name (free-form, default sheikkinen/yamlgraph — O-1)
# optional: --max-credits N (0 < N <= 60; worker max is authoritative)
.github/skills/issue-delegate/submit.sh --check-worker   # health + drift, never submits
```

Typed refusals (non-zero, actionable stderr): usage(2), recursion via
`YAMLGRAPH_DELEGATED=1`(3), dirty tree(4), HEAD not on freshly fetched
remote default(5), invalid/uncommitted payload — same normalizer as the
worker(6), runner offline(7), bundle drift(8).

## Issue contract

Exactly one fenced YAML mapping per issue (`extra=forbid`, duplicate keys
refused), parsed by `models.DelegationRequest` before any checkout:

```yaml
schema_version: 1
task: judge                # judge | research
repo: sheikkinen/yamlgraph # optional; free-form owner/name — PAT grant set is the boundary
sha: <lowercase 40-hex>    # ancestor of the target's fetched default branch
payload: feature-requests/FR-XXX-name.md
max_reported_credits: 60   # optional; worker max 60 authoritative
```

## Lifecycle and truth

- Authorization is read-only and precedes ALL mutation: `delegate` label +
  committed allowlist; `github-actions` and the worker service identity are
  excluded (recursion guard). A refused author leaves only a skipped
  workflow run — no issue mutation, no status.
- Two-tier timeout: 25-minute inner deadline in `windows_job.ps1` (typed
  `TIMEOUT` only when the Job Object is empty AND every recorded PID is
  absent, else `PROCESS_TREE_KILL_FAIL`); the workflow's static
  `timeout-minutes: 30` is the outer platform kill switch —
  `PLATFORM_CANCELLED`, never typed `TIMEOUT`.
- Full redacted output is published on success AND failure (operator
  override O-2 — no trimming); chunking is mechanical, ≤ 60 000 UTF-8
  bytes, never splitting a code point, byte-identical reassembly.
- `DelegationStatus` and `PublicationStatus` are separate closed enums;
  all comments post before one atomic terminal mutation; a comment
  failure can never close an issue as `done`.
- Stranded `claimed` issues (runner loss / platform cancellation) point to
  the Actions run; recovery is an allowlisted operator re-adding
  `delegate` (new run ID).

## Deploying the worker bundle

The comms repo holds a deployed mirror, never an independent source:

```bash
.github/skills/issue-delegate/sync-worker.sh <comms-checkout-dir>
```

Frozen paths: `delegate.yml` → `.github/workflows/delegate.yml`;
`models.py`/`worker.py`/`windows_job.ps1` → `.github/delegate/`. The exact
deployed comms-repo diff receives separate human review before live use
(GATE C-2). Every submission fails closed on drift.

## Operational preconditions (human-owned, C-7/C-8)

Windows service runner registered on Huutokauppakone; service-account
preflight (restart survival, Git Bash runs `scripts/judge.sh` and
`scripts/research.sh`, Copilot CLI authenticated, Python deps resolve);
`DELEGATE_CHECKOUT_PAT` secret (Contents-read; its grant set is the sole
target authorization boundary per amended O-1). Live witnesses: AC-16
(real judge run), AC-17 (inner-timeout with test-only deadline override).

Reference: `reference/development-operations.md` → Issue-queue delegation.
