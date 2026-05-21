# Reflection: FR-433 post-edit apply_patch coverage

## Trap
Tool-name filtering was frozen around legacy edit tools. The dominant editor path (`apply_patch`) silently bypassed post-edit checks, so feedback arrived only at commit time.

## Insight
Observability from `audit.jsonl` showed the mismatch immediately: pre-command saw `apply_patch`, post-edit did not. The fix was boundary normalization at tool-input parsing, not adding more commit-stage checks.

## Heuristic
When a gate claims real-time coverage, verify against actual tool event distribution and include the most-used tool path first.

Seed: Can post-edit checks publish per-tool coverage metrics (count by toolName and inspected/skipped ratio) so blind spots are detected automatically before they cause regressions?
