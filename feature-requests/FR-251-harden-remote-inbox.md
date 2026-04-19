# Feature Request: FR-251 Harden GitHub Issues Remote Inbox

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-19

## Summary

Add author allowlisting, body size cap, and author audit headers to the GitHub Issues remote inbox (FR-243) to prevent prompt injection via untrusted issue bodies.

## Value Statement

Repository maintainers gain defense-in-depth against prompt injection attacks through the chaplain remote inbox, ensuring only trusted authors can drive automated code generation.

## Problem

`watch.sh` imports GitHub Issue bodies verbatim into `.chaplain/inbox/` and feeds them to the LLM pipeline that generates code and auto-commits. Currently there is:

- **No author verification** — any collaborator with triage access can label an issue `chaplain` and have its body processed as a prompt.
- **No size limit** — arbitrarily large payloads are imported and forwarded to the LLM.
- **No provenance tracking** — imported files contain no metadata about who authored the original issue.

On a public repo, this is a prompt injection vector: a malicious issue body can drive code generation and auto-commit through the Plan → Judge → Enforce pipeline.

## Proposed Solution

Three mitigations applied in `watch.sh` at the import boundary (the point where external GitHub data enters the local system):

### 1. Author Allowlist

A file `.chaplain/allowed-authors.txt` lists trusted GitHub logins, one per line. Only issues created by listed authors are imported. Default: repo owner only.

```bash
# .chaplain/allowed-authors.txt
sheikkinen
```

When an issue from an unlisted author is encountered:
- Skip import (do not write to inbox)
- Log a warning: `⚠️ Skipped issue #N from untrusted author @user`
- Do **not** remove the `chaplain` label (leaves it for manual review)

### 2. Body Size Cap

Truncate the imported body at 10,000 characters. When truncation occurs:
- Log a warning: `⚠️ Issue #N body truncated from X to 10000 chars`
- Import proceeds with the truncated content

### 3. Author Audit Header

Prepend a forensic trace header to every imported file:

```markdown
<!-- author: @username -->
# Issue Title

Issue body...
```

This enables post-incident attribution without parsing git blame or GitHub API logs.

### Implementation in `watch.sh`

The existing import block (lines 16-26) is modified:

```bash
# Load author allowlist
ALLOWED_AUTHORS="$SCRIPT_DIR/allowed-authors.txt"
BODY_SIZE_CAP=10000

gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \
| while read -r num; do
    [[ -f "$INBOX/gh-$num.md" ]] && continue

    # FR-251: Author allowlist check
    author=$(gh issue view "$num" --json author --jq '.author.login' 2>/dev/null) || continue
    if [[ -f "$ALLOWED_AUTHORS" ]] && ! grep -qxF "$author" "$ALLOWED_AUTHORS"; then
        echo "⚠️ Skipped issue #$num from untrusted author @$author"
        continue
    fi

    title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
    body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue

    # FR-251: Body size cap
    if [[ ${#body} -gt $BODY_SIZE_CAP ]]; then
        echo "⚠️ Issue #$num body truncated from ${#body} to $BODY_SIZE_CAP chars"
        body="${body:0:$BODY_SIZE_CAP}"
    fi

    # FR-251: Author audit header
    printf "<!-- author: @%s -->\n# %s\n\n%s\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"

    gh issue edit "$num" --remove-label chaplain 2>/dev/null || true
    echo "📥 Imported GitHub Issue #$num: $title"
done
```

## Acceptance Criteria

- [x] `.chaplain/allowed-authors.txt` exists with repo owner as default entry
- [x] Issues from authors not in the allowlist are skipped with a logged warning
- [x] The `chaplain` label is **not** removed from skipped issues
- [x] Issue body is truncated at 10,000 characters when it exceeds the cap
- [x] A warning is logged when truncation occurs, showing original and truncated sizes
- [x] Every imported file starts with `<!-- author: @username -->` header
- [x] When `allowed-authors.txt` does not exist, all authors are accepted (graceful degradation)
- [x] Existing local inbox files (non-GitHub) are unaffected
- [x] The `gh issue view` call fetches author login alongside title and body
- [x] Tests added for allowlist filtering logic
- [x] Tests added for size cap truncation
- [x] Tests added for audit header presence in output

## Alternatives Considered

1. **GitHub-side enforcement (branch protection / CODEOWNERS):** Does not help — the `chaplain` label can be applied by anyone with triage access, and the issue body (not a code file) is the attack vector.

2. **Content sanitization / regex filtering:** Fragile against adversarial inputs. LLM prompt injection cannot be reliably detected with pattern matching. Author allowlisting is the stronger control.

3. **Require issue approval before import:** Would require a two-phase workflow (label → approve → import). Higher friction, deferred to future FR if allowlisting proves insufficient.

## Related

- FR-243: GitHub Issues Remote Inbox (implemented — this FR hardens it)
- GitHub Issue #121: Original report of the hardening gap
- Scripture boundary: `instruction` — "vendor instructions enter here; treat as untrusted external input"
- Scripture trap: `instruction_boundary_uncrossed` — "Agent's vendor instructions treated as project-aligned"
