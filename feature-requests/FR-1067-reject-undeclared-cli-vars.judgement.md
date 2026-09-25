# Judgement: FR-1067 Reject undeclared CLI variables

**Prior art:** the only hit is `FR-1067-reject-undeclared-cli-vars.md`, the FR this judgement governs; its own prior-art line dispositions FR-677 and REQ-YG-069.

**Verdict:** REJECTED — boundary validation is a sound fix, but the newly filed FR lacks the research record required for authority.

**Reviewed against:** `feature-requests/FR-1067-reject-undeclared-cli-vars.md`; `docs/issues-2026-09-24.md`; `yamlgraph/cli/graph_commands.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The domain input disappearing is witnessed (plan section 1.1). Checking provided keys at the CLI entry is narrow and avoids changing expression evaluation repo-wide (FR-1067:31-62). It is a correction to the existing CLI contract, not a new framework primitive; the concrete consumer is the innovation-matrix invocation (FR-1067:8-12).

## Required revisions

### R-1: Re-file with substantive alternatives

Supply a committed four-to-six-class disposition with cited precedent, dissent and `is_this_a_graph`; the three tactics in FR-1067:75-80 are not a research record under the prospective local gate. Disposition FR-677's E-level-lint claim against actual opt-in `--gate` behavior in the replacement itself rather than claiming that a separate note will resolve it (FR-1067:16-23).

### R-2: Specify the runtime accepted-key source

Prove compiled input channels correspond to the initial state keys accepted by both synchronous and asynchronous run modes. FR-1067:59-61 asserts this without a test; add a fixture with declared `state:`, inferred node state keys, graph `variables`, `--var-file`, and an unknown key. Keep imported state exempt only if the run demonstrably preserves its expected fields (FR-1067:52-70). The census criterion cannot allow known failures to be merely "listed as defects" while asserting every documented invocation passes (FR-1067:69-70); choose remediation or an explicit excluded set with a reason.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Rejected FR-1067 disposition; research-backed replacement input-validation FR |

Not authorized: runtime key rejection, lint-gate changes or expression strictness under FR-1067.

## Revised acceptance criteria

- [ ] AC-01: Replacement carries a committed four-to-six-class research disposition, dissent, precedent and graph-fit answer.
- [ ] AC-02: A RED fixture shows undeclared `--var`/`--var-file` keys fail before an LLM call while declared keys, graph variables and imported state retain intended behavior.
- [ ] AC-03: Documented CLI invocations pass, or each excluded invocation has a named reason and separately filed defect; no contradictory blanket-pass claim remains.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation under FR-1067; judge a newly researched replacement. | GATE |
| C-2 | Do not turn this CLI-input check into a global missing-expression error. | GATE |

Authority granted: none under FR-1067.
