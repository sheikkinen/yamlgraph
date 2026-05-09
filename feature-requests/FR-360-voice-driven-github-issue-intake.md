# Feature Request: FR-360 Voice-driven GitHub issue intake via incaller

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1-2 days
**Requested:** 2026-05-09

## Summary

Add a `github_issue_intake` mode to `projects/incaller` so an inbound caller can describe an idea, confirm a recap, and create a GitHub issue via `gh issue create`, with optional `chaplain` labeling and spoken URL/error readback.

## Value Statement

Developers can capture ideas in-flow by voice and immediately persist them as structured GitHub issues without switching to browser/manual issue entry.

## Problem

Issue #360 asks for a voice-first issue filing flow. `projects/incaller` already supports probe-recap interviewing and confirmation, but there is no post-confirmation issue-creation side effect.

Current evidence in this repository:

1. `projects/incaller/graph.yaml` already runs structured probe/recap collection (`phase`, `extracted`, `recap_analysis`).
2. `projects/incaller/prompts/extract_answers.yaml` already extracts structured fields from transcript.
3. `.chaplain/lib/watcher/inbox_sync.sh` already defines `chaplain` label semantics for intake into Chaplain pipeline.
4. No current `projects/incaller` node or tool executes `gh issue create`.

## Research: Existing Patterns and Prior Art

1. **Probe-recap interview pattern exists and should be reused.**
   `projects/incaller/graph.yaml` already routes `parse_targets -> check_missing -> generate_probe/generate_recap -> analyze_recap_response`.
2. **Typed extraction path already exists.**
   `projects/incaller/prompts/extract_answers.yaml` and `analyze_recap_response.yaml` already provide structured data needed to assemble issue payload.
3. **Chaplain label behavior already exists in watcher intake.**
   `.chaplain/lib/watcher/inbox_sync.sh` imports issues labeled `chaplain`; this FR can reuse that by optional label at creation time.
4. **Condition syntax supports narrow, explicit routing guards.**
   `yamlgraph/utils/conditions.py` supports compound `and` expressions for edge conditions.
5. **Gap: issue creation side effect is missing.**
   Repo-wide search found no implementation of `gh issue create` outside this FR draft.

## Objectives

1. Add one explicit mode: `mode == "github_issue_intake"` in `projects/incaller`.
2. Create issue only after positive recap confirmation.
3. Support deterministic optional `chaplain` labeling.
4. Return explicit success (`issue_url`, `issue_number`) or explicit failure (`issue_create_error`) to state for spoken feedback.

## Constraints

1. **Single responsibility:** only issue-intake behavior for `projects/incaller`.
2. **Architecture alignment:** orchestration and routing in YAML graph; side effect (`gh`) in Python tool node.
3. **No new GitHub SDK dependency:** use existing `gh` CLI.
4. **No watcher/FSM redesign:** integration point is label compatibility only.
5. **Preserve existing modes:** non-`github_issue_intake` behavior remains unchanged.

## Proposed Solution

### In scope

1. Extend `projects/incaller/graph.yaml` with issue-intake state keys:
   - `mode`
   - `issue_url`
   - `issue_number`
   - `issue_create_error`
2. Add `projects/incaller/nodes/create_issue.py` Python tool node that:
   - reads structured fields from `extracted` (minimum: title/type/summary + chaplain opt-in),
   - normalizes opt-in at boundary (deterministic truthy/falsey mapping),
   - executes `gh issue create` with explicit argv (no shell interpolation),
   - returns success identifiers or explicit error text.
3. Add prompt templates for spoken readback:
   - `projects/incaller/prompts/speak_issue_url.yaml`
   - `projects/incaller/prompts/speak_issue_error.yaml`
4. Narrow existing confirmation routing so non-intake flows remain unchanged:
   - Current edge: `analyze_recap_response -> generate_goodbye` with `recap_analysis.is_confirmed == True`
   - Planned guard: `recap_analysis.is_confirmed == True and mode != "github_issue_intake"`
   - Add intake-specific confirmed edge to issue creation path.
5. Update `projects/incaller/README.md` with mode usage and `gh` auth prerequisite.

### Out of scope

1. Twilio/ElevenLabs runtime changes.
2. Watcher/Chaplain pipeline behavior changes.
3. Direct GitHub REST client integration.

### Example invocation contract

```bash
yamlgraph graph run projects/incaller/graph.yaml \
  --var 'mode=github_issue_intake' \
  --var 'targets=issue_title:Issue title|issue_type:feat fix docs chore|issue_summary:Problem and expected outcome|chaplain_opt_in:yes or no' \
  --full
```

## Requirement IDs (planned)

| REQ ID | Maps to |
| --- | --- |
| REQ-YG-333 | AC-01: issue-intake state keys exist in `projects/incaller/graph.yaml` |
| REQ-YG-334 | AC-02: confirmed recap routes to create-issue only in intake mode |
| REQ-YG-335 | AC-03: create-issue node executes `gh issue create` and records URL/number on success |
| REQ-YG-336 | AC-04: `chaplain_opt_in` normalization is deterministic and labeling is opt-in only |
| REQ-YG-337 | AC-05: failure path sets explicit `issue_create_error` and does not set success URL |
| REQ-YG-338 | AC-06: URL/error readback nodes route to goodbye |
| REQ-YG-339 | AC-07: README documents `github_issue_intake` mode and `gh` prerequisite |

## Acceptance Criteria

- [x] **AC-01 (REQ-YG-333):** `projects/incaller/graph.yaml` declares `mode`, `issue_url`, `issue_number`, `issue_create_error`.
- [x] **AC-02 (REQ-YG-334):** confirmed recap routes to issue creation only when `mode == "github_issue_intake"`; non-intake confirmed path still routes to normal goodbye.
- [x] **AC-03 (REQ-YG-335):** `projects/incaller/nodes/create_issue.py` executes `gh issue create` and returns `issue_url` + `issue_number` on success.
- [x] **AC-04 (REQ-YG-336):** `chaplain` label is attached only when normalized `chaplain_opt_in` resolves to true.
- [x] **AC-05 (REQ-YG-337):** `gh` missing/auth/create failures return explicit `issue_create_error` and never a success URL.
- [x] **AC-06 (REQ-YG-338):** caller hears either issue URL or explicit error before final goodbye.
- [x] **AC-07 (REQ-YG-339):** `projects/incaller/README.md` documents `github_issue_intake` mode and prerequisites.

## Failing Acceptance Tests (RED plan)

Planned RED test module:

- `tests/unit/test_fr360_voice_issue_intake_red.py`

Planned RED tests:

1. `test_ac01_graph_declares_issue_intake_state_keys`
2. `test_ac02_confirmed_recap_routes_to_create_issue_only_in_issue_mode`
3. `test_ac03_create_issue_executes_gh_and_returns_issue_identifiers`
4. `test_ac04_chaplain_label_applied_only_when_opted_in`
5. `test_ac05_create_issue_failure_sets_explicit_error_without_url`
6. `test_ac06_issue_url_or_error_readback_nodes_route_to_goodbye`
7. `test_ac07_readme_documents_github_issue_intake_mode`

RED command:

```bash
pytest tests/unit/test_fr360_voice_issue_intake_red.py -q --no-cov
```

Each test will include `@pytest.mark.req(...)` markers mapped to REQ-YG-333..339.

## Judge's Amendments (AMEND — must resolve before APPROVE)

Two gaps prevent test authoring and must be resolved explicitly in the spec:

### AMEND-01: `recap_count >= 3` timeout path in intake mode is unspecified

The existing graph has:
```yaml
- from: analyze_recap_response
  to: generate_goodbye
  condition: "recap_count >= 3"
```
In `github_issue_intake` mode, when the recap loop times out (3 rounds without confirmation), the caller hangs up without issue creation. The FR does not acknowledge this case.

**Required resolution:** Add an explicit statement to the Constraints and to AC-02:
- If `recap_count >= 3` in intake mode, the flow proceeds to `generate_goodbye` **without** creating an issue (caller never confirmed).
- The timeout edge must be guarded (same as the confirmed edge) so it only exits to the normal goodbye, not to `create_issue`.
- Add a corresponding sub-case in AC-02: *"timeout path (`recap_count >= 3`) in intake mode routes to `generate_goodbye`, not `create_issue`."*

### AMEND-02: Readback node names and types are underspecified

The FR adds two prompt templates (`speak_issue_url.yaml`, `speak_issue_error.yaml`) but does not specify:
- The graph node names (required by AC-06 tests to check routing edges).
- The node type: LLM-generated natural speech (`type: llm`) or deterministic formatting (`type: python`).

**Required resolution:** In the "In scope" list and in AC-06, explicitly state:
- Node names (suggested: `speak_issue_url`, `speak_issue_error`) as `type: llm` nodes that read from `issue_url` / `issue_create_error` and write `next_utterance`.
- Both nodes must have a downstream edge to the existing `speak` tool node, then to `end_call` via the normal `call_done` path.
- AC-06 test must name these nodes so the graph YAML edge assertions are deterministic.

### AMEND-03: REQ-YG-333..339 not yet registered

These requirement IDs must be added to `ARCHITECTURE.md` and to a new `capabilities/CAP-XX-voice-issue-intake.yaml` before GREEN. Not a blocker for planning, but must be part of the implementation checklist.

---

## Alternatives Considered

1. **Manual/browser issue filing**
   Rejected: does not solve in-flow voice capture.
2. **Write to `.chaplain/inbox/*.md` directly from call**
   Rejected: bypasses GitHub issue lifecycle and immediate URL acknowledgment.
3. **Use GitHub REST SDK instead of `gh`**
   Rejected for this FR: larger auth/dependency surface than existing CLI-based workflow.

## Related

- Topic intent: GitHub issue #360 — <https://github.com/sheikkinen/yamlgraph/issues/360>
- `projects/incaller/graph.yaml`
- `projects/incaller/prompts/extract_answers.yaml`
- `projects/incaller/prompts/analyze_recap_response.yaml`
- `projects/incaller/README.md`
- `yamlgraph/utils/conditions.py`
- `.chaplain/lib/watcher/inbox_sync.sh`
- `feature-requests/FR-243-github-issues-remote-inbox.md`
- `feature-requests/FR-251-harden-remote-inbox.md`

## Topic Source Note

Requested source `.chaplain/processing/gh-360.md` is not present in this worktree snapshot; planning source used was GitHub issue #360 plus in-repo artifacts above.
