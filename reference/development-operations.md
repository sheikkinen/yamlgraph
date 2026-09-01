# Development Operations Reference

Operational reference relocated from `CLAUDE.md` by FR-942 (instruction
context diet). This file is **not** injected into agent turns — it is
consulted on demand via pointers from `CLAUDE.md`.

## Dependency Governance (FR-761)

### Reproducible dependency environment

`constraints/dev-py312.txt` is the FR-761 Python 3.12 reproducibility
artifact — a pinned resolved environment for the
`.[dev,digest,websearch,fsm,verify]` install. Since FR-918 moved CI's
single-version jobs to Python 3.13 (matrix: 3.11 + 3.13), this artifact
no longer mirrors the exact CI interpreter; regenerating an equivalent
`dev-py313.txt` is a follow-up, out of scope for FR-918. It remains
useful for reproducing a clean 3.12 environment:

```bash
# Regenerate the constraints artifact (Python 3.12)
python3.12 -m venv .venv312 && source .venv312/bin/activate
pip install --upgrade pip
pip install -e ".[dev,digest,websearch,fsm,verify]"
python -m pip freeze --exclude-editable > constraints/dev-py312.txt

# Reproduce a clean environment from the committed artifact
python3.12 -m venv .venv312 && source .venv312/bin/activate
pip install --upgrade pip
pip install -c constraints/dev-py312.txt -e ".[dev,digest,websearch,fsm,verify]"

# Run the same dependency CVE scan the CI `security` gate runs
pip-audit --desc --skip-editable --ignore-vuln CVE-2026-3219
```

`pip-audit` is declared in the `dev` extra (FR-761) so this command matches
`.github/workflows/security.yml` byte-for-byte without installing anything
undeclared. The constraints file targets the tested editable dev/security
environment only — it does not pin runtime-only installs.

### Direct-Import Dependency Scan (FR-761)

```bash
# Strict mode: fails on any undeclared core direct import
python scripts/direct_import_scan.py --strict

# Report-only: also lists examples/scripts/tests findings without failing
python scripts/direct_import_scan.py
```

## Branch Protection

**Default flow (FR-889): ALL changes route worktree → PR → squash merge.**
The main checkout keeps governed roots (`yamlgraph/`, `tests/`, `scripts/`,
`capabilities/`, `.github/hooks/`, `docs/`, `feature-requests/`) OS-locked
(`chmod -R u-w` via `scripts/worktree.sh lock-main`) — the filesystem, not
a command grammar, is the write barrier. Agents have no business writing
to main; only runtime lanes (`tmp/`, `logs/`, `changelog/`) stay open.
Operator maintenance on main uses `scripts/worktree.sh sync` (pull +
relock) or an explicit `unlock-main` / `lock-main` pair — the `now.py`
board flags an unlocked main with its age.

### Rules actually enforced on `main` (verified 2026-08-30)

| Rule | Setting | Applies to |
|------|---------|-----------|
| Require pull request | Enabled (0 approvals) | Non-admin pushes and bots |
| Squash merge only | Merge commits and rebase disabled | All PRs; PR title = commit message (Conventional Commits) |
| Required status checks | `commitlint`, `test (3.11)`, `test (3.13)` | Report on both `pull_request` and `merge_group` events |
| Require up to date | Enabled (strict) | PRs must be current with `main` |
| `enforce_admins` | **Disabled** | Admin direct pushes bypass everything |

**Merge queue: BLOCKED BY PLATFORM (FR-934, 2026-08-30).** The
`merge_queue` ruleset rule is only available on organization-owned
repositories; this repo is user-owned, and the API rejects the rule
(422) after validating every parameter. The `merge_group` wiring in
both required workflows is correct and dormant — it activates unchanged
if the repo is ever transferred to an org (pinned by
tests/unit/test_fr934_merge_queue_workflows.py). Operator decision:
stay on the strict up-to-date regime; blocker recorded in FR-934.

### Emergency bypass

Admin overrides are the default single-dev flow, not an emergency measure.
For bypasses of a *failing required check* on automation PRs, document per
[`reference/break-glass.md`](break-glass.md).

## CI Checks

`commitlint` and `test` (both Python versions) are required contexts; the
rest run in CI on PRs but are NOT in the required-contexts set — they
report, and the human (or automation policy) decides:

- **`commitlint`** (`.github/workflows/commitlint.yml`): Validates PR title follows Conventional Commits format. `feat` PRs must include `FR-XXX` reference.
- **`test`** (`.github/workflows/workflow.yml`): Runs `pytest` with 85% coverage threshold (measured 90.36% on 2026-07-12; gate raised from 70 by FR-714) and `ruff` linting.
- **`conflict-check`** (`.github/workflows/commitlint.yml`): Fails when unresolved merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) are found in tracked files (excluding `.github/`). Complements the local `check-merge-conflict` pre-commit hook which is bypassed by server-side squash merges.
- **`copilot-trailer-gate`** (`.github/workflows/commitlint.yml`): Blocks PRs when any `Co-authored-by:` trailer identities appear in PR commit messages or PR body text.
- **`wip-gate`** (`.github/workflows/commitlint.yml`): Blocks PRs when any commit subject in `BASE_SHA..HEAD_SHA` contains standalone `wip` (case-insensitive).
- **`changelog-gate`** (`.github/workflows/commitlint.yml`): Blocks `feat`/`fix` PRs unless a changelog fragment exists in `changelog/unreleased/` (FR-179).
- **`changelog-req-gate`** (`.github/workflows/commitlint.yml`): Validates changelog fragment `req:` front-matter references valid REQ-YG-XXX IDs in the capabilities registry. Mechanical pre-filter for single-REQ CAPs; multi-REQ CAPs deferred (FR-247).
- **`diary-gate`** (`.github/workflows/commitlint.yml`): Blocks `feat`/`fix` PRs with `FR-XXX` reference unless a diary reflection file exists in the diff.
- **`demo-gate`** (`.github/workflows/commitlint.yml`): Blocks `feat`/`fix` PRs that modify files under `examples/demos/<name>/` unless a `demo-output.log` is included in the diff, proving the demo was executed (FR-206).
- **`security`** (`.github/workflows/security.yml`): Validates installed dependencies have no known vulnerabilities (CVEs) via `pip-audit`.

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic authentication |
| `GOOGLE_API_KEY` | Google/Gemini authentication |
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex AI (`provider: vertex`) |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region (default: `us-central1`) |
| `VERTEX_MODEL` | Default model for Vertex AI provider (default: `gemini-2.0-flash`) |
| `VERTEX_API_KEY` | Vertex AI Express mode API key; when set, skips project/location (ADC) and authenticates via key only |
| `INCEPTION_API_KEY` | Inception Labs Mercury authentication |
| `MISTRAL_API_KEY` | Mistral authentication |
| `OPENAI_API_KEY` | OpenAI authentication |
| `REPLICATE_API_TOKEN` | Replicate authentication |
| `RUNPOD_API_KEY` | RunPod authentication |
| `RUNPOD_ENDPOINT` | Full OpenAI-compatible base URL (`https://api.runpod.ai/v2/<slug-or-id>/openai/v1`); serverless cold starts can take tens of seconds — use per-node `timeout`/`on_error: retry` |
| `RUNPOD_MODEL` | Served model name (required; no default — an endpoint serves exactly one deployment) |
| `DEEPSEEK_API_KEY` | DeepSeek authentication |
| `XAI_API_KEY` | xAI Grok authentication |
| `LMSTUDIO_BASE_URL` | LM Studio local server URL |
| `LAN_RECON_USER` | Bare Windows local-account username for the LAN recon skill (FR-945). Recon qualifies as `<COMPUTERNAME>\<user>` before the WinRM handshake; already-qualified or domain-shaped values are refused in v1. |
| `LAN_RECON_PASS` | Password for `LAN_RECON_USER`. Scrubbed from every recon exception, log record, and JSON artifact. |
| `GH_TOKEN` | GitHub personal-access token minted for the remote `copilot` account, used by the `.github/skills/lan-delegate/` skill (FR-948). Forwarded as a bound wrapper parameter, exported to the remote `copilot` CLI subshell as `$env:GH_TOKEN`, and redacted from every captured stdout/stderr byte and every artifact before the summary leaves the remote. Never printed. |
| `AZURE_AI_ENDPOINT` | Azure AI Foundry endpoint URL |
| `AZURE_AI_API_KEY` | Azure AI API key |
| `AZURE_MODEL` | Default Azure model/deployment name (default: `gpt-4o`) |
| `YAMLGRAPH_OTEL_DIR` | Optional directory for per-node copilot OTel files (`<dir>/<node_name>.otel.jsonl`); when set, `_execute_cli` exports `COPILOT_OTEL_FILE_EXPORTER_PATH` per node |
| `YAMLGRAPH_OTEL_EXPORT` | OpenTelemetry span export (FR-759): `otlp` enables graph-run/node-execution spans (requires `pip install "yamlgraph[otel]"`; fails fast if extra missing). Unset = true no-op. See `reference/otel-observability.md` |
| `YAMLGRAPH_ROUTE_LOG` | Route decision log opt-in (FR-723): `1` emits one JSON line per routing decision on the public `yamlgraph.route` logger; a file path also appends raw JSONL for `graph export --overlay` |
| `PROVIDER` | Default LLM provider (anthropic/azure/deepseek/google/inception/mistral/openai/replicate/runpod/xai/lmstudio) |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith observability (true/false) |
| `LANGCHAIN_API_KEY` | LangSmith API key |
| `LANGCHAIN_PROJECT` | LangSmith project name |

## LAN recon (WinRM) — FR-945, REQ-YG-635

The `.github/skills/lan-recon/` skill probes a single LAN Windows host over WinRM 5985 and returns a Pydantic-validated `LanHostInventory` at `tmp/lan/<safe-slug>.json`. It is **read-only, non-admin**; it never mutates the target host.

### Prerequisites on the target Windows host

1. `Enable-PSRemoting -Force` (opens TCP 5985 + starts the WinRM service).
2. Create a local non-admin account for recon (e.g. `copilot`).
3. Add it to the built-in Remote Management Users group **by SID**:
   ```powershell
   Add-LocalGroupMember -SID S-1-5-32-580 -Member <user>
   ```
   Do NOT reference the group by its localized name — on a Finnish install it is `Etähallinnan käyttäjät`. SID `S-1-5-32-580` is universal.

### Client-side environment

`LAN_RECON_USER` and `LAN_RECON_PASS` in your `.env` (never committed). The username must be bare — recon qualifies it as `<COMPUTERNAME>\<user>` before the handshake.

### Invocation

```bash
# DNS/mDNS target (leftmost label derives COMPUTERNAME)
python .github/skills/lan-recon/recon.py Huutokauppakone.local

# IP literal target (--computer-name required)
python .github/skills/lan-recon/recon.py 192.168.50.172 \
    --computer-name HUUTOKAUPPAKONE
```

### Transport contract (Option A)

- HTTP 5985 + `auth="negotiate"` + `encryption="always"` (WSMan message encryption over Negotiate).
- Pinned resolved LAN address (RFC1918 / CGN / link-local / IPv6 ULA / IPv6 link-local only).
- Basic and CredSSP auth are structurally absent from the client kwargs.
- Explicit finite `connection_timeout` (5 s) and `operation_timeout` (30 s).

### Security boundaries

- Non-admin: recon refuses if the probed account returns `admin=True`.
- Password redaction: `LAN_RECON_PASS` is scrubbed from exceptions, log records, and the JSON artifact.
- `tmp/lan/*.json` is git-ignored.

Option B (HTTPS 5986 + certificates) is the correct end state; it requires a separate FR to provision the listener + certificate and is not in this skill's scope.

## LAN Copilot delegation (WinRM) — FR-948, REQ-YG-636

The `.github/skills/lan-delegate/` skill hands off a self-contained Copilot task to a pre-provisioned Windows host over WinRM 5985 and returns a Pydantic-validated `LanDelegationResult`. It **mutates** the remote host (git worktree add, `copilot` CLI subprocess, artifact write to SMB drop) — treat every knob as a load-bearing security boundary.

### Preconditions

1. FR-945 recon receipt at `tmp/lan/<host-slug>.json` no older than `RECON_MAX_AGE_MIN_DEFAULT` (10 min) with `admin=False`, `remote_management_user=True`.
2. Pre-provisioned remote runtime (Node 24 LTS, `@github/copilot` on `PATH`, canonical clone at `C:\Users\copilot\yamlgraph`). Delegation itself does **not** install anything.
3. Local worktree clean (`git status --porcelain` empty). Delegation refuses on a dirty tree so the remote SHA matches something reproducible.
4. Not already inside a delegation (`YAMLGRAPH_LAN_DELEGATED` unset) — recursive delegation is refused.

### Client-side environment

`LAN_RECON_USER` and `LAN_RECON_PASS` (shared with recon) plus `GH_TOKEN` (see Key Environment Variables above). All three must be present at invocation.

### Invocation

```bash
python .github/skills/lan-delegate/delegate.py \
    --host Huutokauppakone.local \
    --prompt-file tmp/analyze.md \
    --run-id analyze-20260901T120000Z-abc1234 \
    [--max-reported-credits 60] \
    [--timeout-s 300]
```

`--run-id` must match `^[A-Za-z0-9._-]+$` (safe for both POSIX paths and SMB shares). `--prompt-file` is capped at 32 KiB.

### Risk envelope

- **Tool authority**: the remote invocation uses `--allow-all-tools --add-dir <run-worktree>`; the remote `copilot` process can read/write anywhere the `copilot` account can. Do not point delegation at a host that also stores personal state.
- **Token exposure**: `GH_TOKEN` is bound as a wrapper parameter (never on the command line), exported to the CLI subshell as `$env:GH_TOKEN`, and byte-scanned out of stdout/stderr and every emitted artifact before the summary crosses the wire. A `TOKEN_LEAK_DETECTED` result means a leak reached the local cache (revoke immediately).
- **Deadline**: `--timeout-s` is a wrapper-owned deadline enforced by `Wait-Job` + `taskkill /PID <root> /T /F`. WinRM's own `operation_timeout` (deadline + 60 s cleanup margin) is a safety net, not the killer.
- **Cleanup**: outer `finally` in the wrapper always removes the per-run worktree and clears `GH_TOKEN`, `YAMLGRAPH_LAN_DELEGATED`, and `COPILOT_ALLOW_ALL` from the session. A `WORKTREE_CLEANUP_FAIL` status is a bug to fix, not a warning to ignore.

### Post-run cost accounting

`copilot` prints an `AI Credits used: <n>` line to stderr. `--max-reported-credits` (default 60) is a **post-run policy check**, not a spend cap — the run is already billed by the time the wrapper sees the number. Compare `credit_status ∈ {OK, HIGH, UNPARSEABLE}` against the run intent.

### Transport contract

Identical to recon Option A (see above), plus:

- `operation_timeout = --timeout-s + 60 s` (WSMAN cleanup margin).
- Username is qualified to `<COMPUTERNAME>\<LAN_RECON_USER>` — the same qualification rule as recon.

### Safe invocation checklist

1. Recon receipt fresh and clean.
2. `.env` has `LAN_RECON_USER`, `LAN_RECON_PASS`, `GH_TOKEN`.
3. Local worktree clean; local HEAD SHA pushed to a ref the remote canonical clone can fetch (`git fetch --all` on the remote before invocation).
4. Prompt is self-contained — no relative paths outside the delegated worktree.
5. Expected `delegation_policy_status = OK`; any other value is an incident, not a warning.

## Issue-queue delegation (GitHub Issues + self-hosted runner) — FR-949, REQ-YG-637

Channel C. Skill: `.github/skills/issue-delegate/SKILL.md`. Coexists with the
FR-948 LAN/WinRM channel until a separate disposition FR; the coexistence
record (task class, queue/execution/end-to-end durations, credits, status,
babysitting interventions for 10 eligible runs or 30 UTC days) lives in the FR.

### Topology

- **Comms repo**: private `sheikkinen/yamlgraph-delegation` — carries only
  delegation issues and the deployed worker bundle mirror; never source.
- **Worker**: Huutokauppakone's labeled Windows **service** runner
  (`self-hosted`, `Windows`, `delegate`); one payload at a time
  (single-flight concurrency). The macOS spike runner is dev evidence only.
- **Target repo**: free-form per-issue `owner/name` (default
  `sheikkinen/yamlgraph`; operator override O-1). The checkout PAT's grant
  set is the sole authorization boundary — an unreadable repo fails typed as
  `CHECKOUT_FAIL`.

### Secrets and credential isolation

- `DELEGATE_CHECKOUT_PAT` (comms-repo Actions secret): checkout credential
  used ONLY by the target checkout step with `persist-credentials: false`.
  Provisioned scripted from the logged-in gh token
  (`install-runner.ps1`: `gh auth token | gh secret set`); the token's
  grant set is the sole target authorization boundary (O-1 as amended).
- Payload preflight proves no PAT bytes, extraheader, credential helper,
  askpass, or usable `gh auth` before launch — any failure is
  `CREDENTIAL_ISOLATION_FAIL` before the payload starts.
- One `worker.py` redactor mediates every worker-controlled byte before any
  publication API; a literal configured secret in output is
  `TOKEN_LEAK_DETECTED` and blocks artifact publication. Transformed
  exfiltration is a documented residual risk, not claimed impossible.

### Timeout truth

25-minute inner deadline (`windows_job.ps1`, Job Object, kill-on-close) is
the ONLY source of typed `TIMEOUT`, and only when the job reports zero
active processes and every recorded PID is absent (else
`PROCESS_TREE_KILL_FAIL`). The workflow's `timeout-minutes: 30` is the
outer platform kill switch — `PLATFORM_CANCELLED`, Actions-owned. Neither
value is issue-controlled.

### Operator runbook

```bash
# one-time host install: runner service + secret provisioning (run ON the worker host)
powershell -ExecutionPolicy Bypass -File .github/skills/issue-delegate/install-runner.ps1
# health + drift, never submits
.github/skills/issue-delegate/submit.sh --check-worker
# submit a judge payload from a clean, pushed HEAD
.github/skills/issue-delegate/submit.sh --task judge --payload feature-requests/FR-XXX-name.md
# deploy the canonical bundle to a comms checkout (then human-review the diff — GATE C-2)
.github/skills/issue-delegate/sync-worker.sh ../yamlgraph-delegation
```

Stranded `claimed` issue (runner loss / outer cancellation): inspect the
Actions run it links; recovery is an allowlisted operator re-adding the
`delegate` label, which creates a new run ID. Worker health:
`gh api repos/sheikkinen/yamlgraph-delegation/actions/runners`.
