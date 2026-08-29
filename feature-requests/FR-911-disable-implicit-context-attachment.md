# Feature Request: Disable Implicit Open-File Context Attachment in Copilot Chat

**Priority:** HIGH
**Type:** Enhancement (operator environment hardening)
**Status:** Implemented (2026-08-29)
**Effort:** minutes (one settings key)
**Requested:** 2026-08-29
**First consumer / first event:** the operator's very next chat prompt —
verified live in the same session (request #13 carried no implicit
attachment after the change; #12 still did).
**Research:** in-body dispositioned record below (FR-889 style) — the
session-store forensics table IS the raw-output read; no separate
research run applicable to a vendor setting change.
**Prior art:** no prior FR covers implicit chat-context attachment.
FR-743 (UserPromptSubmit probe) established that hook stdin excludes
attachments — it is the evidence that this vector cannot be closed by a
hook, not a competing proposal. FR-898 (session accountability report)
shares the session store this FR's forensics read, but reports cost and
activity rather than context payloads. `pre-command-guard.sh` covers the
tool-read vector only and is complementary, not superseded.

## Summary

Set `chat.implicitContext.enabled: { "panel": "never" }` in user-level
VS Code settings to stop Copilot Chat from silently attaching the
focused editor file's contents to every chat prompt. Documentation FR:
the change is already applied; this record exists for sharing and for
the incident trail.

## Value Statement

Any operator with a secrets file (`.env`, keys, tokens) open in a tab
no longer leaks its contents to the model — the leak vector is closed
at the source, before any hook could see it.

## Problem

VS Code's implicit-context feature attaches the *focused editor file's
full contents* to each chat request as a `vscode.implicit.selection`
variable. This happens with no tool call, so the repository's
PreToolUse guard (`pre-command-guard.sh`) can never intervene — the
secret is already in the rendered prompt when the model is called.

**Incident evidence** (session `a7be91fc`, store forensics, 2026-08-29):

| Prompt | Implicit attachment |
|--------|--------------------|
| #2–#4  | `.env` — live API keys, three requests |
| #5–#10 | none (terminal focused) |
| #11–#12 | session `.jsonl` (operator noticed here) |
| #13–#14 | none — setting active |

The `.env` with live keys was sent to the model three times before
detection. Keys were rotated. The attachment tracks editor focus, so
exposure is nondeterministic — "always, when an editor is focused,"
not "first request only."

## Ideal Result

An open file contributes only its *path* to chat context, never its
contents, unless the operator explicitly attaches it or the agent
reads it through a tool (where the PreToolUse guard applies).

## Proposed Solution

One user-level settings key (applied):

```jsonc
// ~/Library/Application Support/Code/User/settings.json
"chat.implicitContext.enabled": {
    "panel": "never"   // never auto-attach the active file to panel chat
}
```

Values per chat location: `"never"` | `"first"` (first request only) |
`"always"`. Takes effect on the next prompt — no reload required
(verified between requests #12 and #13 of the incident session).

## Acceptance Criteria

- [x] Setting present in user `settings.json` under `chat.implicitContext.enabled` with `"panel": "never"`.
- [x] Post-change prompts carry no `vscode.implicit.selection` variable (verified in the chatSessions store for requests #13–#14).
- [x] Editor context degrades to path-only (`The user's current file is …`) with no attachment body.
- [x] This FR committed as the shared documentation of the change.
      *(Was checked while the file was still untracked — see Numbering
      below. Actually committed 2026-08-29.)*

## Numbering

Filed as FR-899, then FR-909, and committed as **FR-911**. Both earlier
numbers were claimed by other concurrent sessions while this file sat
uncommitted in the shared checkout — FR-909 was taken during the minutes
between the rename and the commit. Nothing references the old numbers.

The FR-number uniqueness guard (FR-907, `tests/unit/test_fr_numbering.py`)
reads `git ls-files`, so it never saw this file while it was untracked;
that is deliberate, but it means an uncommitted FR gets no collision
warning at all. Allocation remains first-come, and the race is real:
three numbers were lost to it in one afternoon.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Per-session eye-icon on the current-file pill | Works but per-session and forgettable; does not survive new sessions — rejected as sole control |
| `UserPromptSubmit` hook secret-scan | Hook stdin carries prompt *text only*; implicit attachments are invisible to it (FR-743 probe) — cannot cover this vector |
| PreToolUse deny on `.env` reads | Complementary, covers tool-read vector only; implicit attachment happens before any tool call |
| Workspace-level setting | User-level chosen: the leak vector is operator-wide, not repo-specific |

## Related

- Incident session store: `~/Library/Application Support/Code/User/workspaceStorage/f795c130…/chatSessions/a7be91fc….jsonl`
- FR-898 (session accountability report) — same store, reporting arc
- FR-743 (UserPromptSubmit probe) — established that hook stdin excludes attachments
- `.github/hooks/scripts/pre-command-guard.sh` — covers the tool-read vector, not this one
