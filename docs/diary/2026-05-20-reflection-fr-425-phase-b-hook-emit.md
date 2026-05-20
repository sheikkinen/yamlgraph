# Reflection: FR-425 Phase B — Separate Script Activation

**Date:** 2026-05-20
**FR:** FR-425 Phase B

## Cognitive Process

Phase B was originally designed with `YAMLGRAPH_CLASSIFIER=1` env flag gating inside `pre-command-guard.sh`. User revised: separate script with file-based activation (add/remove JSON config). This is cleaner — the hook system already supports multiple config files, so activation is just a file operation, not a code change.

## Trap Encountered

### stdin consumption (boundary trap)

First draft of `classify-emit.sh` parsed `TOOL_NAME`, `COMMAND`, and `SESSION_ID` with three separate `python3 -c` invocations, each reading from `echo "$INPUT"`. This works because `INPUT=$(cat)` captures stdin once, then each `echo "$INPUT" | python3 -c ...` pipes a copy. But the original code had each python invocation doing `json.load(sys.stdin)` independently — which is correct here because echo pipes fresh copies, but would fail if reading from stdin directly. Consolidated to single-pass parsing (matching `pre-command-guard.sh` pattern) for robustness.

## Insight

File-based activation (add JSON = enable, remove = disable) is superior to env flag gating for hook scripts. It's visible in `git status`, requires no code changes to toggle, and follows the existing multi-config pattern. The env flag approach would have buried activation state in the environment, invisible to the repository.

## Seed:

**Can the hook system auto-discover JSON configs?** Currently each `.json` file in `.github/hooks/` is a manual registration. A glob-based discovery (`*.json` in the hooks dir) would make activation truly zero-config — drop a file, it's active. But this trades explicitness for convenience. Is the tradeoff worth it for a security-relevant system?
