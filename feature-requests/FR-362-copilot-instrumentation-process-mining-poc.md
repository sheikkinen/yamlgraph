# Feature Request: FR-362 Copilot Instrumentation Process-Mining POC

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Rejudged — Approved with scope reduction
**Effort:** 1 day
**Requested:** 2026-05-10

## Summary

Instrument the established Minesweeper Copilot smoke test as a two-phase `plan` / `implement` execution and determine what evidence can be extracted for process mining and repeatable workflow generation.

## Value Statement

YAMLGraph maintainers can convert successful Copilot executions into observable process traces, revealing which agent behaviors are stable enough to become reusable YAMLGraph workflow nodes.

## Problem

Copilot can complete implementation smoke tests, but the durable workflow is currently hidden inside session state, free-form responses, tool calls, terminal output, and git diffs. This makes it difficult to answer:

- Which steps did Copilot actually perform?
- Did implementation follow the plan?
- Which files, commands, tests, and retries appeared?
- Which parts of the work should remain `type: copilot`, and which can become deterministic YAMLGraph tools or `type: agent` / `type: llm` nodes?
- Does session continuation reduce repeated context gathering between plan and implementation?

Minesweeper is a useful POC target because it has known acceptance criteria, a clear implementation shape, and has already served as a Copilot smoke test.

## Proposed Solution

Create a local instrumentation procedure for a two-phase Copilot run:

1. **Plan phase**: Copilot reads `feature-requests/FR-082-minesweeper-game.md` and current repository state, then produces an implementation plan without editing files.
2. **Implement phase**: Copilot resumes the plan session and performs the implementation or validation work.
3. **Collect artifacts** for both phases:
   - rendered prompt
   - stdout JSONL
   - stderr log
   - `--share` markdown session file
   - OpenTelemetry JSONL trace
   - Copilot debug logs
   - git status before/after
   - git diff before/after
   - recent git log after implementation
4. **Normalize raw artifacts** into process-mining events.
5. **Analyze conformance** between plan and implementation.
6. **Report candidate YAMLGraph workflow skeletons** that could be generated from the mined trace.

Example run layout:

```text
outputs/copilot-instrumentation/minesweeper-001/
├── manifest.json
├── plan/
│   ├── prompt.txt
│   ├── stdout.jsonl
│   ├── stderr.log
│   ├── session.md
│   ├── otel.jsonl
│   ├── logs/
│   ├── git-status-before.txt
│   ├── git-status-after.txt
│   ├── diff-before.patch
│   └── diff-after.patch
└── implement/
    ├── prompt.txt
    ├── stdout.jsonl
    ├── stderr.log
    ├── session.md
    ├── otel.jsonl
    ├── logs/
    ├── git-status-before.txt
    ├── git-status-after.txt
    ├── diff-before.patch
    ├── diff-after.patch
    └── git-log-after.txt
```

Example instrumentation command:

```bash
COPILOT_OTEL_FILE_EXPORTER_PATH="$PHASE/otel.jsonl" \
COPILOT_OTEL_EXPORTER_TYPE=file \
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true \
copilot \
  --name "minesweeper-poc-plan" \
  --output-format json \
  --log-dir "$PHASE/logs" \
  --log-level debug \
  --share "$PHASE/session.md" \
  --allow-all-tools \
  --allow-all-paths \
  -p "$(cat "$PHASE/prompt.txt")" \
  > "$PHASE/stdout.jsonl" \
  2> "$PHASE/stderr.log"
```

The implement phase should resume the plan session ID extracted from `plan/session.md`:

```bash
copilot \
  --resume "$SESSION_ID" \
  --name "minesweeper-poc-implement" \
  --output-format json \
  --log-dir "$PHASE/logs" \
  --log-level debug \
  --share "$PHASE/session.md" \
  --allow-all-tools \
  --allow-all-paths \
  -p "$(cat "$PHASE/prompt.txt")"
```

### Event Extraction Model

Normalize artifacts into typed events such as:

```json
{
  "case_id": "minesweeper-001",
  "phase": "implement",
  "event_type": "run_command",
  "tool": "bash",
  "args": {"command": "pytest projects/minesweeper/tests/ -q"},
  "success": true,
  "timestamp": "...",
  "duration_ms": 4210
}
```

Target event types:

| Event Type | Detection Source |
|---|---|
| `read_requirement` | OTel tool call or log entry reading the Minesweeper FR |
| `search_codebase` | OTel/log tool call for search, grep, rg, glob, or file listing |
| `read_file` | OTel/log tool call reading source, tests, docs, prompts, or graphs |
| `write_test` | Diff changes under test files |
| `edit_code` | Diff changes under Python implementation files |
| `edit_graph` | Diff changes to YAML graphs or prompt files |
| `run_targeted_test` | Shell command running a focused pytest target |
| `run_full_test` | Shell command running a broad test suite |
| `lint_graph` | Shell command running `yamlgraph graph lint` |
| `smoke_run` | Shell command running `yamlgraph graph run projects/minesweeper/graph.yaml` |
| `failure` | Nonzero command/tool result or error span |
| `retry` | Repeated command or edit after a failure |
| `commit` | Git commit command or git log delta |

### Process-Mining Questions

The POC should answer:

1. Did implementation follow the plan?
2. Which plan events repeated during implementation despite `--resume`?
3. Which validation gates were run?
4. Which failures caused retries?
5. Which observed steps are stable workflow phases?
6. Which steps are deterministic enough to become YAMLGraph tools?
7. Which steps still require `type: copilot` because they need IDE-level editing and shell access?

## Acceptance Criteria

- [ ] A documented local run procedure exists for the Minesweeper `plan` / `implement` instrumentation POC.
- [ ] The procedure captures `--share`, `--output-format json`, Copilot debug logs, OTel JSONL, git status, and git diffs for both phases.
- [ ] The implement phase resumes the plan phase via the session ID extracted from `plan/session.md`.
- [ ] A sample mined event log is produced from one instrumented run.
- [ ] The event log includes at least: requirement reads, code searches, file reads, code/test edits, test commands, graph lint or smoke run, failures, and retries when present.
- [ ] A short conformance report compares planned steps against observed implementation steps.
- [ ] The report identifies candidate YAMLGraph node types for each durable phase: `llm`, `agent`, `python`, `tool`, `map`, `router`, or `copilot`.
- [ ] Sensitive-content handling is documented: OTel content capture is local-only and must not be uploaded to third-party collectors.

## Alternatives Considered

1. **Use only Copilot `--share` markdown** — Rejected for the POC. It is useful for session ID and human audit, but too coarse for tool-call process mining.
2. **Use only git diffs** — Rejected. Diffs show products, not the sequence of reasoning, commands, failures, or retries.
3. **Use remote OTel collector immediately** — Rejected. File-based OTel JSONL is safer for local experiments, especially when content capture is enabled.
4. **Instrument YAMLGraph `type: copilot` node first** — Deferred. The POC can prove extraction value with a shell wrapper before changing framework code.
5. **Mine arbitrary Copilot sessions** — Rejected for the first POC. Minesweeper provides a known workflow shape and acceptance criteria, making conformance analysis easier.

## Related

- `feature-requests/FR-082-minesweeper-game.md` — Minesweeper smoke-test target
- `feature-requests/FR-168-cross-graph-session-continuity.md` — Session ID handoff across graph runs
- `feature-requests/FR-274-copilot-session-id-extraction.md` — Empirical `--share` session ID extraction
- `examples/demos/session-continuation/graph.yaml` — Two-phase Copilot session continuation pattern
- `examples/bugfix/graph.yaml` — Multi-phase Copilot workflow with session continuation
- `yamlgraph/node_factory/copilot_node.py` — Existing `type: copilot` implementation

## Judgement (v1)

**Verdict: Approved with amendments.**

### Assessment

The proposal is valuable and well aligned with YAMLGraph's direction: observe real agent execution, normalize it at the boundary, then decide which parts are durable workflow structure versus incidental model behavior. Minesweeper is the right first target because it has a known scope, concrete acceptance criteria, and historical use as a Copilot smoke test.

The core shape is sound: two Copilot phases (`plan` then resumed `implement`), local artifact capture, event normalization, and a conformance report. However, the proposal must be tightened before enforcement so the POC is safe, reproducible, and testable without requiring live Copilot execution in CI.

### Required Amendments

#### 1. Run in an isolated disposable worktree

The FR currently implies running against the active repository. That is too risky because the implement phase may edit, test, or commit files. The POC must create or require a disposable worktree/branch for the Minesweeper run and write instrumentation artifacts outside tracked source paths unless explicitly sanitized.

**Amendment:** The run procedure must include an isolation step:

```bash
git worktree add ../yamlgraph-minesweeper-poc -b poc/minesweeper-instrumentation
```

or an equivalent documented disposable clone/worktree. The procedure must also include cleanup instructions. The POC must not push, open PRs, or alter `main`.

#### 2. Separate raw sensitive artifacts from committed outputs

The FR correctly warns that OTel content capture is sensitive, but acceptance criteria still require a "sample mined event log" without distinguishing raw from sanitized artifacts.

**Amendment:** Raw artifacts (`otel.jsonl`, debug logs, session markdown, stdout/stderr, diffs containing code) are local-only and must not be committed. Committable outputs must be sanitized derivatives only:

- `events.sample.jsonl` with secrets/code content redacted or synthetic
- `conformance-report.sample.md` summarizing event classes and phase order
- documentation explaining where raw local artifacts are written

If a real raw artifact is needed for local analysis, it must live under an ignored directory such as `outputs/copilot-instrumentation/`.

#### 3. Add a deterministic extractor with synthetic tests

The FR currently describes event extraction but does not require an executable extractor. A POC that only documents manual inspection will not prove process-mining feasibility.

**Amendment:** Add a small deterministic extractor script or module that reads a run directory and emits normalized JSONL events. It may start with OTel JSONL, git status, and diff-derived events; it does not need full transcript semantics in the first POC.

Minimum contract:

```bash
python scripts/extract_copilot_process_events.py \
  outputs/copilot-instrumentation/minesweeper-001 \
  > outputs/copilot-instrumentation/minesweeper-001/events.jsonl
```

Add unit tests using synthetic fixture artifacts. CI must not require live Copilot, OTel, API keys, or a real Minesweeper implementation run.

#### 4. Define the event schema as the boundary contract

The proposed JSON example is useful but insufficient as a contract. Without a schema, the extractor can drift into ad hoc dictionaries and the conformance report becomes hard to test.

**Amendment:** Define a minimal Pydantic model or documented schema for extracted process events with at least:

- `case_id`
- `phase`
- `event_type`
- `source`
- `timestamp` or `sequence`
- `success`
- `summary`
- `details`

Use tolerant optional fields for tool-specific data, but keep the top-level shape stable.

#### 5. Conformance report must be mechanical before interpretive

The FR asks whether implementation followed the plan, but it does not define how this is determined. LLM interpretation alone would reproduce the same self-certification problem the instrumentation is meant to avoid.

**Amendment:** The first conformance pass must be mechanical:

- list planned step headings or checklist items extracted from the plan output
- list observed event types in implementation order
- mark expected validation gates observed/missing
- count repeated context-gathering events after `--resume`
- count failures and retries

An optional LLM/agent summary may interpret the report afterward, but the raw conformance table must be deterministic.

#### 6. Tighten scope: no framework `type: copilot` changes in this FR

The alternatives section defers framework instrumentation, which is correct. Keep that boundary.

**Amendment:** This FR may add local scripts, docs, sanitized sample artifacts, and tests for extraction. It must not modify `yamlgraph/node_factory/copilot_node.py` or the runtime `CopilotResult` model. If the POC proves useful, a follow-up FR can integrate durable run-journaling into `type: copilot`.

### Revised Acceptance Criteria

In addition to the existing acceptance criteria, enforcement must satisfy:

- [ ] The run procedure uses a disposable worktree or equivalent isolated environment.
- [ ] Raw Copilot/OTel artifacts are written only to an ignored local output directory.
- [ ] Any committed sample event log or report is sanitized or synthetic.
- [ ] A deterministic extractor script/module emits normalized JSONL process events from a run directory.
- [ ] The process event shape is documented or represented by a Pydantic model.
- [ ] Unit tests cover event extraction using synthetic artifacts; no live Copilot run is required in CI.
- [ ] The conformance report includes a deterministic table before any interpretive narrative.
- [ ] No changes are made to `yamlgraph/node_factory/copilot_node.py` or `CopilotResult` in this FR.

---

## Judgement (v2 — Rejudgement)

**Verdict: Approved with scope reduction.**

### Motivation for Rejudgement

The v1 judgement amendments are individually correct but collectively inflated a 1-day POC into a multi-day deliverable. The original FR proposed 8 acceptance criteria; the judgement added 8 more. Sixteen acceptance criteria for a proof-of-concept is scope creep from the judge, not the author. A POC must prove one thing — *can we extract process-minable events from Copilot runs?* — not deliver a polished pipeline.

### Empirical Verification

Verified against `copilot help monitoring` (2026-05-10):

1. **OTel file export is real and documented.** `COPILOT_OTEL_FILE_EXPORTER_PATH` writes JSONL locally. Span tree: `invoke_agent → chat <model> → execute_tool <tool>`. Content capture via `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`. The FR's proposed env vars are correct.
2. **`--output-format json`** emits structured JSONL to stdout. Combined with OTel spans, this gives two complementary views of the same run.
3. **`--share` session ID extraction** is empirically proven (FR-274). The `--resume` flag accepts session ID or name. The two-phase pattern is already demonstrated in `examples/demos/session-continuation/graph.yaml`.
4. **Minesweeper is implemented** (FR-082 status: Implemented). It is a valid, concrete target.
5. **No implementation artifacts exist yet** — `outputs/copilot-instrumentation/` is empty. This is a fresh start.

### Assessment of v1 Amendments

| v1 Amendment | Verdict | Rationale |
|---|---|---|
| 1. Disposable worktree | **Retain** | Non-negotiable safety. Copilot will edit files. |
| 2. Sensitive artifact separation | **Retain** | Non-negotiable. Raw OTel with content capture must stay local-only. |
| 3. Deterministic extractor with tests | **Reduce** | An extractor script is correct, but demanding full synthetic test fixtures for a POC is premature. The first run *is* the test. Require the script and a smoke test against its own output, not fabricated fixtures. |
| 4. Pydantic event schema | **Retain** | Commandment 5. But allow the schema to be minimal — `case_id`, `phase`, `event_type`, `timestamp`, `summary`. Additional fields optional. |
| 5. Mechanical conformance report | **Reduce** | Requiring a deterministic conformance *table* before interpretation is correct in principle, but over-specified for a POC. Require a structured event sequence listing. The "did implementation follow plan" question can be answered by visual inspection of the event log for the first run. A follow-up FR can formalize conformance checking. |
| 6. No `copilot_node.py` changes | **Retain** | Correct scope boundary. |

### Revised Scope

The POC delivers exactly three things:

1. **A run script** (`scripts/copilot_instrument.sh`) that executes a two-phase Copilot run in a disposable worktree with full artifact capture (OTel JSONL, stdout JSONL, stderr, `--share` session file, git diffs, debug logs). Raw artifacts go to `outputs/copilot-instrumentation/<run-id>/`.

2. **An extractor** (`scripts/extract_copilot_events.py`) that reads a run directory and emits normalized JSONL events conforming to a minimal Pydantic schema. The extractor must handle OTel span data and git diff data at minimum. It is tested by running it against a real (or manually created) run directory and asserting the output parses and contains expected event types.

3. **A findings document** committed as `docs/copilot-instrumentation-poc.md` summarizing: what was captured, what event types appeared, which phases are stable, which steps are candidates for YAMLGraph nodes, and what the next FR should address.

### What Is Explicitly Out of Scope

- Synthetic test fixtures for the extractor (the first real run provides the fixture)
- Automated conformance checking (visual inspection of event log suffices for POC)
- Sanitized sample JSONL committed to the repo (the findings doc summarizes without raw data)
- Changes to `yamlgraph/node_factory/copilot_node.py` or `CopilotResult`
- Any CI integration (this is a local-only procedure)

### Revised Acceptance Criteria (Replaces Both Original and v1 Criteria)

- [ ] `scripts/copilot_instrument.sh` exists and documents usage for a two-phase Copilot run
- [ ] The run script creates a disposable worktree and captures all artifacts to `outputs/copilot-instrumentation/<run-id>/`
- [ ] Raw artifacts (`otel.jsonl`, logs, diffs, session markdown) are written only to gitignored output directories
- [ ] `scripts/extract_copilot_events.py` reads a run directory and emits JSONL events
- [ ] Events conform to a Pydantic model with at minimum: `case_id`, `phase`, `event_type`, `timestamp`, `summary`
- [ ] The extractor handles at least OTel span data and git diff data
- [ ] `docs/copilot-instrumentation-poc.md` summarizes findings and identifies candidate YAMLGraph node types
- [ ] No changes to `yamlgraph/node_factory/copilot_node.py` or `CopilotResult`

### Effort Estimate

**1 day** is now realistic with the reduced scope: ~3h for the run script and first execution, ~3h for the extractor and schema, ~2h for the findings document.
