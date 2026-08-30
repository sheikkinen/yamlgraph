# Judgement: FR-926 Research Route Failure Must Cite the Recorded Cause

**Verdict:** APPROVED WITH REVISIONS — the bug is real and the gather-boundary fix is the smallest sound route, but authority activates only after the FR requires the formatter to handle the repository's actual `PipelineError` objects and makes the operator-facing witness mechanically precise.

**Prior art:** dispositioned in the parent FR's own prior-art record (FR-890 research sole route, CAP-08 error handling); verified against the cited artifacts below. No competing or rejected precedent proposes surfacing recorded errors at the `gather_findings` boundary.

**Reviewed against:** `feature-requests/FR-926-research-failure-cites-recorded-cause.md`; `feature-requests/FR-926.research.md`; `feature-requests/FR-925-lane-delivery-agent-context.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`; `examples/demos/research-route/nodes/research_tools.py`; `examples/demos/research-route/graph.yaml`; `scripts/research.sh`; `scripts/research_preflight.py`; `tests/unit/test_fr890_research_route.py`; `capabilities/CAP-08-error-handling.yaml`; `yamlgraph/models/schemas.py`; `yamlgraph/error_handlers.py`; `yamlgraph/node_factory/llm_execution.py`; `ARCHITECTURE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; repository Scripture supplied in project instructions.

## What is sound

The problem is evidenced and local. FR-926 records that the operator saw only `missing persona findings: yamlgraph_native_finding`, while the actual `ValidationError: rationale ... string_too_long` was already in `state["errors"]` and required a 47-child-run LangSmith drill to recover (`feature-requests/FR-926-research-failure-cites-recorded-cause.md:28-38`). The current gather boundary indeed raises only the missing keys and discards the adjacent error channel (`examples/demos/research-route/nodes/research_tools.py:270-273`).

The proposed fix is minimal and architecturally aligned. The research graph routes five persona branches through `gather_findings` before `reduce_findings` (`examples/demos/research-route/graph.yaml:201-229`), and the failing persona nodes already use retry semantics (`examples/demos/research-route/graph.yaml:86-117`). CAP-08 defines errors as first-class pipeline state and reporting surfaces (`capabilities/CAP-08-error-handling.yaml:1-31`), while the retry handler records a `PipelineError` when retries exhaust (`yamlgraph/error_handlers.py:123-136`; `yamlgraph/error_handlers.py:62-67`). Reading that existing state in `gather_findings` preserves the FR's boundaries: no schema-cap relaxation, no retry-semantics change, and no partial artifact (`feature-requests/FR-926-research-failure-cites-recorded-cause.md:68-73`).

The research evidence satisfies the substance requirement despite one lineage blemish. The committed research record exists and preserves five persona rows, with four converging on boundary-enforcement at the gather step and one heavier LangGraph error-handler alternative (`feature-requests/FR-926.research.md:1-13`). The dangling brief filename in the header is not essential to judging this already self-contained bug, but it must be corrected or explicitly marked unavailable before enforcement.

Strategic classification: **contrib/example bug fix**. This hardens the FR-890 research-route example and wrapper surface; it is not a framework primitive because the generic error contract already exists in CAP-08, and it is not mere documentation because the current raise site demonstrably hides recorded state.

## Required revisions

### R-1: Require formatting of actual `PipelineError` objects, not only dicts

Replace the illustrative `isinstance(e, dict)` filtering in the Proposed Solution with an explicit contract: `gather_findings` must surface entries from `state["errors"]` whether they are `PipelineError`/Pydantic model instances or plain dicts. The emitted detail must include node, error category, human message, and `details.exception_type` when present. This is necessary because the retry path stores `PipelineError.from_exception(...)` objects, whose fields are `type`, `message`, `node`, and `details={"exception_type": ...}` (`yamlgraph/models/schemas.py:31-43`, `yamlgraph/models/schemas.py:77-83`), not guaranteed dicts.

### R-2: Make the operator-facing witness exact and non-LLM

Revise AC-04 to name the test shape: a wrapper/subprocess test must prove `scripts/research.sh` does not swallow the graph failure text. Use a deterministic fake `YAMLGRAPH_BIN` or equivalent non-LLM fixture that emits the enriched `gather_findings` failure text and exits without creating `tmp/draft-alternatives.md`; assert the combined operator-facing output includes the missing key and recorded node/type/message before the wrapper's artifact-contract failure. This tests the shell propagation boundary shown by `scripts/research.sh:62-69` without spending tokens or depending on provider behavior.

### R-3: Repair the dangling research brief citation or downgrade it to metadata

The `**Research:**` line cites `research-briefs/fr-926-error-surfacing-problem-brief.md` (`feature-requests/FR-926-research-failure-cites-recorded-cause.md:9`), and the promoted research record repeats that filename (`feature-requests/FR-926.research.md:3`), but that path is not present in the repository. Fold one of these mechanically: either commit the brief at the named path, or change both headers to make clear that the committed evidence is `feature-requests/FR-926.research.md` and the brief filename is informational, not a cited artifact. Do not let a dangling evidence path remain in a newly judged FR.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-926-research-failure-cites-recorded-cause.md` revision folding R-1 through R-3 |
| D-2 | `examples/demos/research-route/nodes/research_tools.py` only at `gather_findings` and private helper(s) needed to format recorded errors |
| D-3 | Research-route unit test covering missing persona key with populated `state["errors"]` containing a `PipelineError` object and, if desired, a dict-form equivalent |
| D-4 | Research-route unit test covering absent/empty `state["errors"]` preserving the existing `missing persona findings: ...` message |
| D-5 | Wrapper/operator-surface test proving the enriched graph failure text is visible in `scripts/research.sh` output |
| D-6 | Changelog fragment and diary reflection |

Not authorized: graph topology changes; prompt/schema hard-cap changes; retry-count or retry-handler changes; changing `state["errors"]` shape; adding a LangGraph `error_handler` node; implementing retry-with-error-feedback; producing partial `tmp/draft-alternatives.md` artifacts on failure; changing generic YAMLGraph CLI exception rendering beyond what the wrapper-surface test proves necessary.

## Revised acceptance criteria

- [ ] AC-01: A direct unit test calls `gather_findings` with at least one missing `PERSONA_KEYS` entry and a populated `state["errors"]` containing a `PipelineError`; the raised `ValueError` contains the missing state key, recorded node, error category, human validation message, and exception type from `details.exception_type`.
- [ ] AC-02: A direct unit test calls `gather_findings` with a missing persona key and an empty or absent error channel; the raised message remains exactly `missing persona findings: <comma-separated missing keys>`.
- [ ] AC-03: Dict-form error entries in `state["errors"]` are handled without type assertions or `as any`-style casts; malformed/non-structured entries are ignored rather than inventing details.
- [ ] AC-04: `gather_findings` success behavior is unchanged: with all five persona keys present, it returns the same `{"findings": [...]}` shape and still normalizes each persona finding.
- [ ] AC-05: `scripts/research.sh` operator output preserves graph failure details: a deterministic subprocess/wrapper test using a fake graph runner or equivalent fixture observes the enriched failure text in stdout/stderr before the existing artifact-contract failure.
- [ ] AC-06: Existing FR-890 research-route tests continue to pass without weakening graph topology, schema caps, retry config, artifact verification, or librarian citation checks.
- [ ] AC-07: The FR and research record no longer contain a dangling cited brief path, unless that brief is committed at the named path.
- [ ] AC-08: A changelog fragment in `changelog/unreleased/`, FR implementation-status update, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-3 are folded into FR-926. | GATE |
| C-2 | The change must remain a gather-boundary visibility fix and must not alter retry semantics, graph topology, schema caps, or error-channel state shape. | GATE |
| C-3 | Tests must exercise the real recorded-error shape used by the retry path (`PipelineError`), not only a hand-built dict. | GATE |
| C-4 | Absence of recorded errors must preserve the existing terse missing-key message; no synthetic cause text is authorized. | GATE |
| C-5 | No partial research artifact may be emitted as a substitute for hard failure. | GATE |

Authority granted: after the required revisions are folded into FR-926, implement the narrow `gather_findings` error-surfacing change, its direct and wrapper-surface tests, and the standard changelog/diary/FR status updates within the frozen scope above.
