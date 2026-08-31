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
