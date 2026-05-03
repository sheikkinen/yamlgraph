# Diary: FR-311 — Hook-Fix Retry and Unanchored Prompts

**Date:** 2026-05-03
**FR:** FR-311 (git_commit retry), judge prompt fix
**Theme:** Boundary normalization failures at two levels

## Traps Encountered

### 1. Unanchored Prompt Reference (judge.yaml)
The judge prompt said "Examine the feature request in feature-requests/" without specifying
which FR. In v2 pipeline (fresh session, no plan context), copilot picked FR-274 from the
worktree name instead of FR-311. The variable `fr_path` was passed to the graph but never
rendered in the prompt template.

**Classification:** `instruction_boundary` + `downstream_fix` — the prompt was an instruction
boundary where external data (the FR path) enters the LLM. Failing to normalize at this
boundary meant the LLM improvised a target.

### 2. Recoverable Failure Treated as Fatal (git_commit_action.py)
Pre-commit hooks auto-fix files (trailing whitespace, ruff format) and return exit 1.
The git_commit action treated any non-zero as fatal, killing the pipeline. The fix was
already demonstrated in `precommit_action.py` (retry loop) but never applied to
`git_commit_action.py`.

**Classification:** `partial_remediation` — the retry pattern existed in one action but
wasn't applied to the analogous action.

## Heuristic

> When a prompt references a collection ("feature-requests/"), the LLM will pick. When it
> references a specific path (`{fr_path}`), the LLM will obey. Template variables that exist
> but aren't rendered in the prompt are silent bugs — they pass all schema checks.

## Seed

Could we add a lint rule that warns when a graph passes variables to a copilot node but the
prompt template doesn't reference them? Unused variables in prompt templates are the prompt
equivalent of dead code — they signal a disconnect between the graph contract and the prompt
contract.
