# Constitution Diff — Spec Kit's Generator vs the Scripture (FR-870)

What does a state-of-the-art spec-driven-development generator rediscover of
an incident-paid doctrine, given only the artifacts the doctrine produced?
This exhibit answers with a measured, clause-level diff. Claim under test:
`docs/origin-story.md` ("The External Record") asserts the incident-paid
case-law layer of the Scripture cannot be generated.

## (a) Provenance

| Field | Value |
|-------|-------|
| Date | 2026-08-23 |
| Operator/agent | FR-870 enforcement session (Claude Fable 5, VS Code) |
| Generation agent | GitHub Copilot CLI 1.0.80, default model `claude-opus-4.8` (per CLI config `recentModelIds`) |
| Spec Kit | v1.0.0 (tag `1ecccc04a0fd163c889ef034b909d4d3c49dc2b9`), Specify CLI `specify 1.0.0`, installed via `pip install "git+https://github.com/github/spec-kit.git@v1.0.0"` into a throwaway venv |
| Init command | `specify init --here --force --non-interactive --integration copilot` (in scratch worktree `/tmp/yg-speckit` at repo HEAD `8e34f4de`) |
| Command surface | Copilot skill `.github/skills/speckit-constitution/SKILL.md` (source: `templates/commands/constitution.md`) |
| Constitution prompt (`$ARGUMENTS`) | "Derive the governing principles for this project from its codebase, tests, and CI configuration." plus instructions to follow the skill's execution flow, derive strictly from repository evidence, stay inside the directory tree, and mark `RATIFICATION_DATE` as TODO |
| Generated path | `.specify/memory/constitution.md` (207 lines), captured verbatim in section (b) |
| Generation cost | 1m 57s, ~292k tokens up / 5.2k down |

### Sanitized input manifest (R-1)

The scratch worktree was reduced so the generator could not read the answer
key. Sanitation log (verbatim):

```
removed (deny-list):
.github/copilot-instructions.md .github/skills .github/hooks CLAUDE.md AGENTS.md
feature-requests/ docs/diary/ docs/origin-story.md docs/memento/ docs/confessions.md
tmp/ *.judgement.md
pruned to allow-list: yamlgraph/ tests/ examples/ scripts/ .github/workflows/
pyproject.toml .pre-commit-config.yaml .importlinter README.md ARCHITECTURE.md
reference/ capabilities/
extended deny (verbatim doctrine text found in allowed dirs): examples/ebook/
examples/demos/philosopher_book/ examples/dungeon_master/docs/
retained-with-flag (name-drop references, no doctrine text):
examples/novel_fandom/story/thread_waivers.yaml examples/plot_modeller/docs/*.md
examples/demos/diary_index/ reference/patterns.md ARCHITECTURE.md
capabilities/CAP-32,CAP-74 (requirement descriptions)
```

The frozen deny-list proved to be a minimum: a leak grep
(`grep -rl "Thou shalt|the_one_law|10 Commandments"`) found verbatim doctrine
text inside allowed dirs (the ebook pipeline embeds the doctrine as source
material; the philosopher_book chapters ARE essays on the traps) — those were
removed and logged as the extended deny above. Surviving hits are name-drop
references only (a trap name in a prompt example, requirement descriptions
that say the doctrine exists) — retained and flagged: the generator may learn
*that* a doctrine exists, not what it says.

**Declared borderline** (per FR-870 R-1): `.pre-commit-config.yaml`,
`.importlinter`, and `.github/workflows/` stayed in the corpus. They are
mechanized law — what the law *produced* — so any rediscovery traceable to
their text is flagged below as enforcement-fingerprint rediscovery, not
independent derivation.

## (b) Generated constitution (verbatim)

```markdown
<!--
Sync Impact Report
- Version change: 0.0.0 → 1.0.0
- Added principles:
  - I. YAML-First Declarative Design
  - II. Layered Architecture with Enforced Boundaries
  - III. Test-Gated Development (NON-NEGOTIABLE)
  - IV. Security-Embedded Pipeline
  - V. Explicit Dependency Ownership
  - VI. Complexity Ceilings
  - VII. Conventional Commits and Traceability
- Added sections:
  - Quality Gates
  - Development Workflow
  - Governance
- Removed sections: none (initial constitution)
- Deferred TODOs:
  - RATIFICATION_DATE: unknown, marked TODO
-->

# YAMLGraph Constitution

## Core Principles

### I. YAML-First Declarative Design

Every LLM pipeline MUST be defined declaratively in YAML with schema
validation. Python is permitted only at the presentation layer (CLI), the
side-effects layer (tool nodes), and contrib utilities. Inline LLM
orchestration in Python source files is forbidden — enforced by the
`lint_inline_llm.py` pre-commit hook.

**Rationale:** Separation of concerns keeps pipeline logic diffable,
reviewable, and accessible to non-developers. Runtime safety comes from
schema validation catching errors before execution.

### II. Layered Architecture with Enforced Boundaries

The codebase MUST follow a three-layer architecture enforced by
`import-linter` contracts:

1. **Presentation** — `yamlgraph.cli` (argument parsing, terminal output)
2. **Logic** — `yamlgraph.compile`, `yamlgraph.executor`,
   `yamlgraph.linter`, `yamlgraph.routing`, and peers (LLM calls, state
   transitions, graph compilation)
3. **Side Effects** — `yamlgraph.tools`, `yamlgraph.models`,
   `yamlgraph.utils`, `yamlgraph.storage`, `yamlgraph.contrib`
   (API calls, file I/O, models)

Cross-layer imports MUST flow downward only. Leaf modules (`a2a`, `export`)
MUST NOT be imported by the linter or compiler. The linter MUST remain
LLM-free — no executor or LLM-factory imports. These boundaries are
machine-verified on every commit via `lint-imports`.

**Rationale:** Architectural contracts prevent accidental coupling and
guarantee the linter remains a pure, offline, deterministic tool safe for
pre-commit and CI.

### III. Test-Gated Development (NON-NEGOTIABLE)

All changes to `yamlgraph/`, tests, YAML schemas, and `pyproject.toml`
MUST pass the unit test suite before commit. The pre-commit hook runs
`pytest tests/unit/ -q --tb=short --no-cov -m "not slow" -n auto`.
CI runs the full unit suite against Python 3.11 and 3.12 with a minimum
coverage threshold of 80% (`--cov-fail-under=80`). The local developer
baseline is 85% (`--cov-fail-under=85` in `pyproject.toml`).

Tests MUST use dedicated test-only Pydantic models (not imported from
`yamlgraph.models`) to prove the framework is truly generic. Test markers
(`req`, `integration`, `slow`, `process`) MUST be used to classify tests.

**Rationale:** The pre-commit test gate prevents broken code from entering
the repository. Multi-version CI matrix ensures cross-version compatibility.

### IV. Security-Embedded Pipeline

Security scanning MUST be integrated into both the pre-commit pipeline and
CI:

- **Bandit** (medium+ severity) runs on every commit via pre-commit; any
  finding without a `nosec` confession blocks the commit.
- **Ruff `S` rules** (flake8-bandit) are enabled in the linter
  configuration for static security analysis.
- **pip-audit** runs in CI on every PR and version tag to detect known
  vulnerabilities in dependencies.
- **detect-private-key** pre-commit hook prevents credential leakage.
- **Block AI co-author trailers** hook enforces authorship integrity.

**Rationale:** Security checks at multiple stages (local commit, CI) create
defense-in-depth. Embedding security into the developer workflow eliminates
the "security as afterthought" anti-pattern.

### V. Explicit Dependency Ownership

Every Python package directly imported by source code MUST be explicitly
declared in `pyproject.toml` — transitive dependencies MUST NOT be relied
upon implicitly. The `direct_import_scan.py --strict` pre-commit hook
enforces this. Every dependency MUST have a documented rationale
(`dependency_rationale.py --strict`).

Optional capabilities (OTEL, vision, FSM, RAG, MCP, A2A, etc.) MUST be
isolated in separate `[project.optional-dependencies]` extras and MUST
NOT appear in core dependencies. CI MUST include a "core-only" test path
that proves the framework works without optional extras installed.

**Rationale:** Direct-import honesty prevents "works on my machine" failures
when transitive dependency trees change. Extra-based isolation keeps the
core package lightweight.

### VI. Complexity Ceilings

Source code MUST respect hard complexity ceilings enforced by automated
gates:

- **Cyclomatic complexity**: Radon grade D (CC ≥ 21) is blocked on commit.
- **Cognitive complexity**: Ruff `C901` with `max-complexity = 15`.
- **File size**: Source files in `yamlgraph/` exceeding 450 lines are
  blocked; files exceeding 400 lines trigger a warning.
- **Code duplication**: jscpd with threshold 10%, min-lines 10, min-tokens
  80 detects copy-paste.
- **Dead code**: Vulture (min-confidence 60) flags unused code on commit.
- **Hedging check**: Silent fallbacks and hedging patterns are forbidden in
  `yamlgraph/` and `scripts/`.

**Rationale:** Machine-enforced ceilings prevent complexity drift. Each gate
targets a specific failure mode: tangled logic (CC), cognitive overload
(C901), monolith files (size), copy-paste decay (jscpd), dead weight
(vulture), and hidden error swallowing (hedging).

### VII. Conventional Commits and Traceability

All commits MUST follow Conventional Commits format. Additional rules:

- `feat:` commits MUST reference a Feature Request ID (`FR-XXX`).
- `feat:` and `fix:` commits MUST include a changelog fragment in
  `changelog/unreleased/`.
- `wip` commits are blocked on `main`.
- Capabilities MUST be tracked in a validated registry (`capabilities/`)
  with schema validation and ID registry enforcement.
- Requirements traceability (`req_coverage.py --strict`) links test
  markers to ARCHITECTURE.md requirements.

**Rationale:** Traceability from commit to feature request to changelog to
capability registry creates an auditable development history. Automated
gates prevent policy drift.

## Quality Gates

The following automated gates MUST pass before code is merged:

| Gate | Tool | Scope |
|------|------|-------|
| Lint | Ruff (E, W, F, I, B, C4, UP, SIM, C901, S) | `yamlgraph/` |
| Format | Ruff formatter | all Python |
| Architecture | import-linter (5 contracts) | `yamlgraph/` |
| Unit tests | pytest (3.11, 3.12 matrix) | `tests/unit/` |
| Coverage | pytest-cov ≥ 80% CI / ≥ 85% local | `yamlgraph/` |
| Security (static) | Bandit medium+ | `yamlgraph/` |
| Security (deps) | pip-audit | all deps |
| Complexity | Radon CC < grade D | `yamlgraph/` |
| File size | ≤ 450 lines | `yamlgraph/*.py` |
| Duplication | jscpd ≤ 10% | `yamlgraph/` |
| Dead code | Vulture ≥ 60% confidence | `yamlgraph/` |
| Commit format | Conventional Commits | all commits |
| Dependency honesty | direct-import-scan, dependency-rationale | `pyproject.toml` |
| Inline LLM | lint_inline_llm.py | all Python |
| Hedging | hedging_check.py --strict | `yamlgraph/`, `scripts/` |
| Req coverage | req_coverage.py --strict | cross-cutting |
| YAML validity | check-yaml, check-toml | config files |

## Development Workflow

1. **Pre-commit hooks** (`fail_fast: true`) run the full gate suite locally
   before each commit. The suite includes linting, formatting, architecture
   checks, unit tests, security scans, complexity gates, and commit message
   validation.
2. **CI pipeline** (GitHub Actions `workflow.yml`) runs on every PR and
   version tag. It includes a core-only test job (no optional extras) and a
   full matrix test job (Python 3.11 + 3.12) with coverage enforcement.
3. **Conventional Commits** are validated both locally (pre-commit) and in
   CI (`commitlint.yml`). PR titles MUST also follow the convention.
4. **Security scanning** (`security.yml`) runs pip-audit on every PR with
   retry logic.
5. **Release process**: version tags (`v*.*.*`) trigger the build job, which
   validates tag-to-pyproject version alignment, builds the package, and
   publishes to PyPI via trusted publishing.

## Governance

This constitution supersedes ad-hoc practices. All PRs and code reviews
MUST verify compliance with the principles and quality gates defined above.

**Amendment procedure:**
- Amendments MUST be documented with a rationale and versioned.
- Principle additions or material expansions require a MINOR version bump.
- Principle removals or incompatible redefinitions require a MAJOR
  version bump.
- Clarifications and wording fixes require a PATCH version bump.
- All amendments MUST update `LAST_AMENDED_DATE` to the date of the change.

**Compliance review:**
- The pre-commit and CI gate suite serves as automated compliance review.
- Manual review is required for principle interpretation disputes.
- The ARCHITECTURE.md document is the single source of truth for
  capabilities and requirements traceability.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): adoption date unknown | **Last Amended**: 2026-08-23
```

*Verbatim with one elision: a hyphenated modifier in the Governance MAJOR-bump
bullet was shortened to "incompatible" because the original wording contains a
term this repo's forbid-terms hook blocks — an enforcement fingerprint firing
on the exhibit itself.*

## (c) Source-unit manifest

Normative units of `.github/copilot-instructions.md` (the Scripture),
enumerated before classification.

**Included** (108 units):

| Family | IDs | Count |
|--------|-----|-------|
| The 10 Commandments | C-01..C-10 | 10 |
| the_one_law | LAW-01 | 1 |
| Traps | T-01..T-28 | 28 |
| Cures | CU-01..CU-18 | 18 |
| Questions | Q-01..Q-09 | 9 |
| Generative methods | M-01..M-06 | 6 |
| Process rules | P-01..P-14 | 14 |
| Conventions | CV-01..CV-10 | 10 |
| Sermon of the Chaplain | S-01..S-07 | 7 |
| Rite of Correction | R-01..R-03 | 3 |
| Requirement traceability (ADR-001) | X-01 | 1 |
| noqa confessions | X-02 | 1 |
| **Total** | | **108** |

**Excluded** (one-sentence reasons):

- `boundaries` — a taxonomy locating where the law applies, not norms.
- `seeds` — forward-looking backlog, not governing law.
- Agents' prayer — liturgy restating cures already counted.
- Copilot Hooks section — descriptive infrastructure inventory, not norms.
- Quick Reference / Submitting Proposals / quickstart — pointers and how-to.
- Addendum — restates `changelog_first_diagnostic` (CU-09), deduplicated.

**Reconciliation:** 10+1+28+18+9+6+14+10+7+3+1+1 = 108; every included unit
appears exactly once in table (d); 14 + 29 + 65 = 108. ✓

## (d) Scripture-unit classification

Labels (mutually exclusive, exhaustive for source units):

- **R** = `REDISCOVERED` — generated constitution contains an equivalent
  clause (quoted).
- **IP** = `SOURCE_ONLY_INCIDENT_PAID` — absent from generated output AND
  carries an in-text incident witness (FR/NC/diary citation).
- **UG** = `SOURCE_ONLY_UNTRACED_GENERIC` — absent from generated output,
  no in-text incident citation (conservative bucket: many of these
  graduated from diaries, but this exhibit counts only cited witnesses).

| ID | Unit | Label | Evidence |
|----|------|-------|----------|
| C-01 | Research before coding | UG | absent from generated output |
| C-02 | Demonstrate with example (demo proof) | UG | absent; demo-gate not rediscovered |
| C-03 | Config separate and validated | R | P-I: "defined declaratively in YAML with schema validation" |
| C-04 | Honor existing patterns | UG | absent |
| C-05 | Sanctify outputs with types (Pydantic) | R | P-I "schema validation"; P-III "test-only Pydantic models" (partial: fire-of-Pydantic norm reduced to validation mechanics) |
| C-06 | Bear witness of errors; no silent fallbacks | R | P-VI: "Silent fallbacks and hedging patterns are forbidden" (via `hedging_check.py` fingerprint) |
| C-07 | TDD red-green-refactor | R | P-III "Test-Gated Development (NON-NEGOTIABLE)" (partial: the gate, not the failing-test-first ordering or RED/GREEN commit discipline) |
| C-08 | Kill entropy (vulture/jscpd/radon, split modules) | R | P-VI Complexity Ceilings: radon/jscpd/vulture/file-size verbatim |
| C-09 | Operational truth (SLOs, tracing, LangSmith) | UG | absent |
| C-10 | Preserve and improve the doctrine | UG | absent (Governance section is template-mandated scaffold, not derived) |
| LAW-01 | Normalize at the boundary of entry | UG | absent |
| T-01 | continuation_bias | UG | absent, no in-text citation |
| T-02 | quick_confidence | UG | absent, no citation |
| T-03 | downstream_fix | UG | absent, no citation |
| T-04 | symptom_patch | UG | absent, no citation |
| T-05 | intent_drift | UG | absent, no citation |
| T-06 | false_duplicate | UG | absent, no citation |
| T-07 | regex_fourth_exclusion | UG | absent, no citation |
| T-08 | partial_remediation | UG | absent, no citation |
| T-09 | audit_as_ritual | UG | absent, no citation |
| T-10 | plausible_wrong_answer | UG | absent, no citation |
| T-11 | framework_costume | UG | absent, no citation |
| T-12 | working_system_inertia | UG | absent, no citation |
| T-13 | infrastructure_self_exempt | UG | absent, no citation |
| T-14 | architecture_as_diagram | R | P-II: three layers "enforced by import-linter contracts... machine-verified on every commit" (via `.importlinter` fingerprint) |
| T-15 | instruction_boundary_uncrossed | UG | absent, no citation |
| T-16 | vendor_default_as_help | UG | absent, no citation |
| T-17 | model_as_trusted_peer | R | P-IV: "Block AI co-author trailers hook enforces authorship integrity" (partial: hook rediscovered, adversarial-review rationale absent — generated rationale is authorship, not misalignment) |
| T-18 | recent_changes_blindness | UG | absent, no citation |
| T-19 | workspace_is_not_boundary | UG | absent, no citation |
| T-20 | gate_checks_shape_not_substance | UG | absent, no citation |
| T-21 | composition_bug | IP | in-text: FR-371, NC-141, NC-289 |
| T-22 | mock_escape_hatch | IP | in-text: FR-378 |
| T-23 | refactor_orphans_secondary | IP | in-text: NC-203 |
| T-24 | research_as_inventory | IP | in-text witness: ninchat_voice CP handbook link list |
| T-25 | inventory_by_visibility | IP | in-text: yamlgraph 2026-05-31 asset inventory |
| T-26 | growth_as_default | IP | in-text: FR-465/FR-466 CAP retirement arc |
| T-27 | metric_archaeology_before_reading_output | IP | in-text: FR-596/597 |
| T-28 | threshold_encodes_forecast | IP | in-text: FR-727, FR-730, FR-726 |
| CU-01 | ask_before_generate | UG | absent, no citation |
| CU-02 | test_before_reading | UG | absent, no citation |
| CU-03 | tolerant_matching | UG | absent, no citation |
| CU-04 | three_reads | UG | absent, no citation |
| CU-05 | streaming_xray | UG | absent, no citation |
| CU-06 | callsite_fix | UG | absent, no citation |
| CU-07 | spec_kill | UG | absent, no citation |
| CU-08 | judge_as_junior_pr | UG | absent, no citation |
| CU-09 | changelog_first_diagnostic | UG | absent, no citation |
| CU-10 | boundary_inventory | UG | absent, no citation |
| CU-11 | substance_over_presence | UG | absent, no citation |
| CU-12 | investigation_before_fix | IP | in-text: FR-371 → FR-372 |
| CU-13 | assert_path_not_destination | IP | in-text: NC-179 |
| CU-14 | name_the_seam | IP | in-text: NC-131 |
| CU-15 | incident_density_ranking | IP | in-text: utils/fsm 915 lines / 116 diary entries |
| CU-16 | read_raw_output_first | IP | in-text: FR-598, FR-730 |
| CU-17 | two_strike_split | IP | in-text: FR-722/727/730 |
| CU-18 | junk_drawer_cap | IP | in-text: FR-725, FR-727/730 |
| Q-01 | would_you_use_this | IP | in-text firing moment: watcher-subscription FR killed |
| Q-02 | does_the_platform_already_do_this | IP | in-text: PreCompact existed while ceiling models were built |
| Q-03 | who_reads_this_when | IP | in-text: fr-board's only reader was its generator |
| Q-04 | what_does_the_raw_record_say | IP | in-text: question form of read_raw_output_first (CU-16 witnesses) |
| Q-05 | are_the_witnesses_one_phenomenon | IP | in-text: five compaction witnesses broke the single-ceiling model |
| Q-06 | does_the_tool_fit_or_merely_exist | IP | in-text: MCP registration vs world_distill |
| Q-07 | where_is_the_repo_boundary | IP | in-text: fr-board F7 |
| Q-08 | what_would_the_successor_need | IP | in-text: MAP.md do-not-re-derive section |
| Q-09 | is_this_a_graph | IP | in-text: FR-853 graduation, 2026-08-22 recurrence |
| M-01 | ideal_result_backwards | IP | in-text: FR-739, FR-744, FR-746 |
| M-02 | five_whys | UG | absent; graph exists but no incident citation |
| M-03 | forced_opposite | IP | in-text: FR-195 challenge gate |
| M-04 | value_proposition | UG | absent, no citation |
| M-05 | pre_mortem | IP | in-text: phantom-witness and F7 classes |
| M-06 | capability_constraint_matrix | UG | absent, no citation |
| P-01 | graduation (twice → FR → Scripture) | UG | absent, no citation |
| P-02 | conductor | UG | absent, no citation |
| P-03 | boring_enforcement | UG | absent, no citation |
| P-04 | audit_gate | UG | absent, no citation |
| P-05 | demo_vs_test | UG | absent, no citation |
| P-06 | unchallenged_premise | UG | absent, no citation |
| P-07 | automation_inherits_doctrine | UG | absent, no citation |
| P-08 | changelog_ci_gate | R | P-VII: "feat/fix commits MUST include a changelog fragment in changelog/unreleased/" (origin FR-149; rediscovered via changelog-gate fingerprint) |
| P-09 | detection_without_enforcement | UG | absent, no citation |
| P-10 | enforcement_at_merge_boundary | R | Quality Gates preamble: "MUST pass before code is merged" |
| P-11 | mixed_commits_erode_auditability | UG | absent, no citation |
| P-12 | cross_project_graduation | UG | absent, no citation |
| P-13 | constraint_over_code | IP | in-text measurement witness: 216 lines of Scripture / 21k lines of Python |
| P-14 | one_session_one_repo | IP | in-text: third strike 2026-07-14, four interleave incidents |
| CV-01 | first forbidden phrase (the compat excuse; term elided — forbidden by the very hook it names) | UG | absent; forbid-terms hook not surfaced in generated gates table |
| CV-02 | second forbidden phrase (the red-suite disclaimer; term elided likewise) | UG | absent |
| CV-03 | multi-line commits via tmp/msg.txt | UG | absent |
| CV-04 | slow scripts → log file | UG | absent |
| CV-05 | hyphenated paths → snake_case | UG | absent |
| CV-06 | YAMLGraph/LLM over complex regex | UG | absent |
| CV-07 | Conventional Commits + FR enforcement | R | P-VII: "feat: commits MUST reference a Feature Request ID (FR-XXX)" |
| CV-08 | Diary reflection as final task | UG | absent; diary-gate not rediscovered |
| CV-09 | All edits under a judged FR | UG | absent (FR *reference* rediscovered in CV-07; the judged-FR governance is not) |
| CV-10 | Hooks enforce; read hook output on failure | R | Development Workflow 1: "Pre-commit hooks (fail_fast: true) run the full gate suite locally before each commit" |
| S-01 | Sermon: Research | UG | absent |
| S-02 | Sermon: Plan (FR as the plan, ideal-result-first) | UG | absent |
| S-03 | Sermon: Judge (independent, input closure, never author's session) | UG | absent — the headline absence |
| S-04 | Sermon: Enforce (failing test first, smallest change) | UG | absent |
| S-05 | Sermon: Purge | UG | absent |
| S-06 | Sermon: Submit (bump/commit/push/tag, CI judges) | R | Development Workflow 5: release process, tag→build→PyPI (partial: mechanics only) |
| S-07 | Sermon: Distill (diary, graduation) | UG | absent |
| R-01 | Rite: Inspect | UG | absent |
| R-02 | Rite: Amend (failing test first) | UG | absent |
| R-03 | Rite: Escalate (to FR with traces) | UG | absent |
| X-01 | Requirement traceability (`@pytest.mark.req`) | R | P-VII: "Requirements traceability (req_coverage.py --strict) links test markers to ARCHITECTURE.md requirements" |
| X-02 | noqa confessions (`docs/confessions.md`) | R | P-IV: "any finding without a `nosec` confession blocks the commit" (partial: bandit-only; the confession register itself was deny-listed) |

## (e) Generated-only clauses

Clauses present in the generated constitution with no counterpart in the
Scripture *document* (labels: `GENERATOR_ONLY_GENERIC_MISSED` = candidate
worth considering; `GENERATOR_ONLY_REJECTED` = not wanted, with reason).

| ID | Generated clause | Label | Disposition |
|----|------------------|-------|-------------|
| G-01 | Coverage thresholds stated as law (≥80% CI / ≥85% local) | GENERATOR_ONLY_GENERIC_MISSED | Lives in `pyproject.toml`/CI, not in Scripture text; numeric gates arguably belong in config, not law — no action |
| G-02 | "Tests MUST use test-only Pydantic models to prove the framework is truly generic" | GENERATOR_ONLY_GENERIC_MISSED | A real, implicit testing norm the generator surfaced from test code — the single genuine derivation in the run; candidate for a future convention |
| G-03 | Core-only test path / extras isolation as principle (P-V) | GENERATOR_ONLY_GENERIC_MISSED | Practiced in CI, unstated in Scripture; reasonable candidate |
| G-04 | Constitution semantic versioning + amendment procedure | GENERATOR_ONLY_REJECTED | Template-mandated scaffold; the Scripture's amendment procedure is graduation (incident → diary → FR → law), which is stronger and already law |
| G-05 | Release flow detail (tag/pyproject alignment, trusted publishing) | GENERATOR_ONLY_GENERIC_MISSED | Documented in `reference/release-checklist.md`; correctly placed there, not in law — no action |

## (f) Measured fractions and conclusion

| Metric | Value | Numerator / denominator |
|--------|-------|-------------------------|
| Source units REDISCOVERED | **13.0%** | 14 / 108 |
| Source units SOURCE_ONLY_INCIDENT_PAID (cited floor) | **26.9%** | 29 / 108 |
| Source units SOURCE_ONLY_UNTRACED_GENERIC | **60.2%** | 65 / 108 |
| Rediscoveries traceable to enforcement fingerprints (hooks/CI text in corpus) | **14 / 14** | every REDISCOVERED row cites a hook, gate, or CI config the corpus contained |
| Generated-only clauses | 5 | 3 candidates, 2 no-action/rejected |

Notes on interpretation: the incident-paid figure is a floor — this exhibit
counts only in-text witnesses, and many UG units (e.g. `quick_confidence`,
`three_reads`) graduated from diary entries that were deny-listed and thus
uncitable here. The rediscovery figure is correspondingly a ceiling on
"derivation": all 14 rediscoveries quote the text of the mechanized
enforcement layer (`.pre-commit-config.yaml`, `.importlinter`, workflows) —
the generator transcribed the police, it did not derive the law. Zero
rediscovery occurred for: the independent Judge (S-03), the Sermon pipeline,
the Rite of Correction, all 28 traps as cognitive hazards, all 18 cures, all
9 questions, and `the_one_law`.

**Conclusion (3 sentences).** A state-of-the-art constitution generator,
given the full sanitized codebase, rediscovered 13% of the Scripture's
normative units — every one by transcribing enforcement configuration, none
by deriving norms from code behavior. The incident-paid layer (≥27% cited
floor) and the entire judgement/graduation machinery were invisible to it.
This **strengthens** the origin-story claim: the case-law layer of the
doctrine is not derivable by generation from the artifacts the law produced —
it must be paid for in incidents.

## (g) Cleanup evidence

Scratch state before removal (deletions = sanitization; untracked =
Spec Kit scaffolding, never committed):

```
--- scratch git status (deletions = sanitization; untracked = spec-kit scaffolding):
  11 ??
3862 D
--- git worktree list (after removal):
/Users/sheikki/Documents/src/yamlgraph                    93040147 [main]
/Users/sheikki/.copilot/session-state/.../pr463-397166ce  397166ce (detached HEAD)
/Users/sheikki/Documents/src/yamlgraph-break-glass-audit  cad89201 [docs/break-glass-audit-2026-08-17]
--- git worktree prune --dry-run:
ok
```

`/tmp/yg-speckit` no longer appears in `git worktree list`; the two other
worktrees predate and are unrelated to this FR. The throwaway venv
(`/tmp/yg-speckit-venv`) was deleted. Files changed in the live repo by this
FR's enforcement: `docs/constitution-diff.md` (this exhibit),
`docs/origin-story.md` (one cross-link line),
`feature-requests/FR-870-*.md` (status), `docs/fr-board.md` (regenerated) —
verified by `git diff --name-only` at commit time (see the enforcing commit).

## Related

- `feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md` (+ judgement)
- `docs/origin-story.md` — "The External Record" (the claim under test)
- [github/spec-kit](https://github.com/github/spec-kit) v1.0.0
