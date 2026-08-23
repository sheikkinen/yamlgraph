# Copilot Hooks (ramp Tier-1)

Installed by `scripts/ramp.sh`. PreToolUse guard contract:

- The runtime pipes a JSON payload (tool name + input) to
  `scripts/pre-command-guard.sh` on stdin.
- The hook answers on stdout: `{"decision":"approve"}` or a
  `hookSpecificOutput` deny object with a reason.
- Unparseable input is denied (fail closed).
- Every decision is appended to `logs/audit.jsonl`
  (override the directory with `HOOK_LOG_DIR` in tests).

Checks shipped at Tier 1: Co-authored-by trailer block, `--no-verify`
block, multiline `git commit -m` block, pytest-pipe-buffer block.
