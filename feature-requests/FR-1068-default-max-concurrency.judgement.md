# Judgement: FR-1068 Default max concurrency

**Prior art:** `FR-1068-default-max-concurrency.md` is the FR this judgement governs. FR-984 (Enforced) added the setting this FR would default; FR-985 (Shelved) is FR-984's sibling and supplies the width-2 quota evidence. Both are cited by the FR; FR-030 (Won't Fix) is dispositioned there.

**Verdict:** REJECTED — host-dependent width is real, but the research gate is unmet and the proposed provider-wide default of eight is an unapproved spend/rate-limit decision.

**Reviewed against:** `feature-requests/FR-1068-default-max-concurrency.md`; `docs/issues-2026-09-24.md`; `yamlgraph/cli/graph_run_helpers.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The FR-984 run-config path leaves `max_concurrency` unset without an override (`yamlgraph/cli/graph_run_helpers.py:144-151`), so host width can change the number of concurrent calls. One run-level bound reused by CLI and API callers is architecturally narrower than a per-map setting (FR-1068:16-20, 40-53). Classification: a correction to the existing execution primitive with many graph consumers, not a new primitive.

## Required revisions

### R-1: Re-file with substantive research

Compare four to six solution classes, including a fixed run default, provider-specific quota policy, explicit per-graph setting, and concurrency admission at the provider boundary; give precedent, dissent and `is_this_a_graph`. FR-1068:65-70 rejects only three numbers/status quo and does not address how many requests a provider can actually accept (plan section 2 D6).

### R-2: Obtain a human default-risk decision

Ask the operator: **May the runtime impose width eight across all providers and API callers, or must the safe width be explicit per deployment/provider?** The cited 429 witness at width 12 and quota two (FR-1068:11-14) does not establish eight is safe; the timeout run at 16 does not establish eight is globally optimal (FR-1068:65-70). Specify behavior for `run_graph`, `run_graph_async` and streaming entry points, override precedence, and positive-int errors in the replacement; assert actual peak in-flight branches rather than only the config dict.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Rejected FR-1068 disposition; researched replacement and explicit operator decision |

Not authorized: changing defaults, adding environment knobs or throttling providers under FR-1068.

## Revised acceptance criteria

- [ ] AC-01: Replacement cites four to six researched classes with precedent, dissent and graph-fit answer.
- [ ] AC-02: Human records a default/provider-specific concurrency decision with the observed quota risk.
- [ ] AC-03: RED fixture measures peak branch count on CLI, sync and async calls at patched CPU counts and checks override priority plus invalid env values.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation under FR-1068 without a researched replacement and human risk/default decision. | GATE |

Authority granted: none under FR-1068.
