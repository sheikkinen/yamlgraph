## 2026-03-12: FR-187 — CI Dependency Security Scan Reflection

**Context:** Added `pip-audit` as a CI gate in a dedicated `security.yml` workflow. The project had comprehensive runtime security controls (REQ-YG-055–062: loop limits, timeouts, shell injection prevention) but zero supply-chain scanning. A vulnerable transitive dependency in langchain, pydantic, or jinja2 would pass CI undetected.

**Trap:** `framework_costume` — The initial instinct was to add the `pip-audit` step to the existing `workflow.yml`. But that workflow triggers on version tags for release — adding `pull_request` trigger there would fire `build`, `publish`, and `create-release` on every PR. The "it's all CI" mental model disguised fundamentally different trigger requirements. A security scan on PRs and a release pipeline on tags are different workflows wearing the same "CI" costume.

**Heuristic:** When a new CI concern has different trigger conditions than an existing workflow, create a separate workflow file rather than gating with `if:` conditionals. Workflow files are the boundary — keep each one's trigger matrix simple and composable. The cost of an extra `.yml` file is negligible; the cost of accidentally firing a release job on a PR is not.

**Seed:** `pip-audit` scans installed packages against the OSV database — but only at CI time, when the PR is open. What about drift between merge and deploy? A scheduled weekly scan on `main` would catch newly disclosed CVEs in already-merged dependencies. Could the Philosopher pattern (periodic scan → proposal → Chaplain review) be generalized to security advisories?
