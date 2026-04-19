# Feature Request: GitHub Issues as Remote Chaplain Inbox

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-04-19

## Summary

Extend `watch.sh` to poll GitHub Issues labeled `chaplain` as a remote inbox, enabling the Plan→Judge→Enforce pipeline to be triggered from any device with GitHub access.

## Value Statement

Any contributor can submit a topic to the Chaplain pipeline from anywhere — phone, browser, or CI — by opening a GitHub Issue with the `chaplain` label, removing the local-only bottleneck.

## Problem

The Chaplain `watch.sh` daemon only monitors `.chaplain/inbox/` on the local filesystem. There is no remote entry point:

1. **No mobile/browser access.** Submitting a topic requires shell access to the repo working directory.
2. **No remote agent integration.** External CI, bots, or collaborators cannot trigger the pipeline without cloning the repo and writing a file.
3. **No feedback loop.** When a topic is processed, there is no notification back to the submitter unless they watch the git log.

GitHub Issues already provide authenticated, auditable, cross-platform submission with built-in notification — making them a natural remote inbox.

## Proposed Solution

Two changes, both in shell scripts (no Python dependencies added):

### A. Sync GitHub Issues into inbox (`watch.sh`)

At the top of the poll loop in `watch.sh` (before the local inbox scan), sync open GitHub Issues labeled `chaplain` into inbox files. Use a two-pass approach to avoid multi-line body corruption, and remove the label on import to prevent infinite re-import loops.

```bash
# FR-243: Sync GitHub Issues labeled 'chaplain' into local inbox
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
    gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \
    | while read -r num; do
        [[ -f "$INBOX/gh-$num.md" ]] && continue
        title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
        body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue
        printf "# %s\n\n%s\n" "$title" "$body" > "$INBOX/gh-$num.md"
        gh issue edit "$num" --remove-label chaplain 2>/dev/null || true
        echo "📥 Imported GitHub Issue #$num: $title"
    done
fi
```

Key behaviors:
- **Two-pass parsing:** `gh issue list` fetches numbers only; `gh issue view` fetches each body individually, avoiding tab-delimited multi-line corruption.
- **Label removal on import:** Removing the `chaplain` label after writing the inbox file prevents the infinite re-import loop identified by the Judge (the plan stage deletes inbox files, so file-existence alone is not sufficient for idempotency).
- **Retry mechanism:** Users can re-label an issue with `chaplain` to trigger re-processing.
- **Graceful degradation:** If `gh` is not installed or not authenticated, the entire block is silently skipped and local inbox continues to work.
- **No new dependencies:** Uses `gh` CLI which is already listed in the environment's available tools.

### B. Close originating issue on enforce completion (`watch.sh`)

Initialize `EXIT_CODE=1` as a failure sentinel before the if-elif-else block. After the block, add a single close guard that checks both `EXIT_CODE` and the `gh-*.md` filename pattern:

```bash
# FR-243: Initialize EXIT_CODE as failure sentinel (rejected FRs never override)
EXIT_CODE=1

if [[ -n "$new_fr" ]]; then
    if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
        echo "⏭️  Skipping rejected FR: $new_fr"
    elif grep -q 'Type.*Bug' "$new_fr" 2>/dev/null; then
        # ... existing bugfix pipeline (sets EXIT_CODE) ...
    else
        # ... existing enforce pipeline (sets EXIT_CODE) ...
    fi

    # FR-243: Close originating GitHub Issue on successful enforcement
    if [[ $EXIT_CODE -eq 0 ]]; then
        inbox_basename=$(basename "$topic_file")
        if [[ "$inbox_basename" == gh-*.md ]]; then
            gh_num="${inbox_basename#gh-}"
            gh_num="${gh_num%.md}"
            gh issue close "$gh_num" \
                --comment "✅ Implemented via $(git log -1 --format='%h %s')" 2>/dev/null || true
            echo "🔒 Closed GitHub Issue #$gh_num"
        fi
    fi
fi
```

Key behaviors:
- **Sentinel pattern:** `EXIT_CODE=1` initialized before the branch. Rejected FRs never set it to 0, so the close guard correctly skips them.
- **Only on success:** Issues are closed only when `EXIT_CODE -eq 0`.
- **Audit trail:** The close comment includes the commit hash and message.
- **Failure tolerance:** `|| true` ensures a failed `gh issue close` does not abort the pipeline.

### C. Require `chaplain` label to exist in the repository

One-time manual setup:

```bash
gh label create chaplain --description "Chaplain pipeline remote inbox" --color 6f42c1
```

Document in `CLAUDE.md` under the "Submitting Proposals" section.

### Security note: Expanded trust boundary

GitHub Issues open the Chaplain pipeline to anyone with issue-writing permission on the repository. The existing local inbox requires filesystem access. The `chaplain` label acts as a gating mechanism — consider restricting who can apply labels (repository settings or CODEOWNERS-style review) if the repository is public.

## Acceptance Criteria

- [ ] `watch.sh` syncs open GitHub Issues labeled `chaplain` into `.chaplain/inbox/gh-{number}.md` at the top of each poll cycle
- [ ] Sync uses two-pass approach: `gh issue list` for numbers, then `gh issue view` per issue, avoiding multi-line body corruption
- [ ] The `chaplain` label is removed from the issue immediately after successful import, preventing infinite re-import loops
- [ ] Sync is skipped silently when `gh` CLI is not installed (`command -v gh` fails)
- [ ] Sync is skipped silently when `gh` is not authenticated (`gh auth status` fails)
- [ ] Local inbox (`*.md` files placed directly in `.chaplain/inbox/`) continues to work unchanged
- [ ] `EXIT_CODE` is initialized to `1` (failure sentinel) before the if-elif-else enforcement block
- [ ] On successful enforcement (`EXIT_CODE -eq 0`), if the inbox file matches `gh-*.md`, the originating GitHub Issue is closed with a comment containing the commit hash
- [ ] Issue is NOT closed when enforcement fails (`EXIT_CODE -ne 0`)
- [ ] Issue is NOT closed when FR is rejected (sentinel `EXIT_CODE=1` is never overridden)
- [ ] Issue is NOT closed for local inbox files (non `gh-*.md` filename)
- [ ] `gh issue close` failure does not abort the pipeline (`|| true`)
- [ ] CLAUDE.md "Submitting Proposals" section updated to document remote submission via GitHub Issues
- [ ] Manual verification: end-to-end test with a real GitHub Issue documented in PR description

## Alternatives Considered

### A. GitHub Actions webhook instead of polling

A workflow triggered on `issues.labeled` could write the inbox file and push. Avoids polling but adds CI complexity, requires the daemon to run on a server, and introduces git push races. Polling is simpler and aligns with existing `watch.sh` architecture.

### B. Processed-issues ledger instead of label removal

Maintain `.chaplain/.gh-processed` listing imported issue numbers. This works but adds state that must be committed and synced. Label removal is simpler: the issue itself is the source of truth, and re-labeling provides an explicit retry mechanism.

### C. Raw `curl` + `GITHUB_TOKEN` instead of `gh` CLI

Would avoid the `gh` dependency but `gh` is already available, handles auth/pagination/JSON natively, and is more readable.

### D. Bidirectional status sync (post intermediate progress to issue)

Instead of just closing on completion, update the issue with Plan/Judge/Enforce status. Disproportionate complexity — the close comment already links the commit containing the full FR. Deferred to a future FR if demand materializes.

### E. Per-branch close blocks vs. post-block sentinel

Placing close logic inside each non-rejected branch duplicates ~5 lines. The sentinel pattern (`EXIT_CODE=1` before branches, single close block after) avoids duplication while correctly handling the rejected path.

## Related

- `.chaplain/watch.sh` — target file for both changes
- `scripts/enforce_worktree.sh` — enforce pipeline (called by `watch.sh`)
- `scripts/bugfix_worktree.sh` — bugfix pipeline (called by `watch.sh`)
- FR-084: Copilot watch migration (established `watch.sh` architecture)
- FR-098/FR-196: Consolidated watch graph
- FR-163: Chaplain inbox instructions in CLAUDE.md
- FR-175: Sequential enforcement mode (established the `EXIT_CODE` pattern)
