# Reflection: Hook Observability and the Order 66 Command Channel

**Date:** 2026-05-20
**Context:** Extending FR-414 (copilot hook audit logging) with session correlation and a user command channel.

## I. What Happened

After merging FR-414's audit logging, the user asked two questions that opened new ground:

1. "Is there similar logging for prompts, thinking, OTel, user triggers, memory, context files?"
2. "Add session_id. Consider an 'execute order 66' hook — user issuing direct commands to the hook system."

The first question required mapping VS Code Copilot's full observability surface. The second required inventing a control plane within the constraint that hooks only intercept tool calls.

## II. Traps Encountered

### Payload Shape Assumption (boundary trap)
We built the hooks against assumed payload fields (`toolName`, `toolInput`). When I probed the actual VS Code payload, it revealed six additional fields we weren't capturing: `session_id`, `tool_use_id`, `timestamp`, `transcript_path`, `hook_event_name`, `cwd`. The cure was literal: inject a one-shot dump to capture the real payload, read it, then remove the probe. **Lesson:** Never trust documentation over observation. Probe the actual boundary.

### Continuation Bias in Observability
When asked "what else should we log?", my first instinct was to build more hooks. But the transcript JSONL (`transcripts/<session>.jsonl`) already captures everything — user prompts (verbatim), agent thinking (`reasoningText`), every tool call with full arguments and results. The gap wasn't capture — it was extraction. The cheapest fix is a parser script, not a new hook. **Lesson:** Before building new telemetry, inventory what already exists. The system may already be observable; it's just not queryable.

### No User Prompt Hook (platform constraint)
VS Code has `PreToolUse` and `PostToolUse` but no `OnUserMessage`. User triggers are invisible to the hook system. This is a hard platform boundary that can't be worked around with more code — only with a new architecture (the command channel).

## III. Key Insight: Deny as Communication Channel

The most creative discovery: since PreToolUse can only approve or deny, and the deny reason text is visible to the agent, the deny mechanism becomes a bidirectional communication channel.

The user says "lock it down." The agent calls `.github/hooks/cmd lockdown`. The hook:
1. Intercepts the sentinel pattern before execution
2. Processes the command (creates lockfile)
3. Returns deny with the response in the reason text
4. The command never reaches the terminal

This turns a limitation (hooks can't respond, only block) into a feature (deny IS the response). The pattern generalizes: any information the hook system needs to communicate back to the agent can be encoded as a deny reason.

## IV. Architecture Pattern: Sentinel Command Channel

```
User prompt → Agent → run_in_terminal(".github/hooks/cmd X")
                              ↓
                    PreToolUse intercepts
                              ↓
                    Sentinel pattern matched
                              ↓
                    Command processed (lockdown/unlock/status)
                              ↓
                    Deny with response ← Agent sees this
                              ↓
                    Agent relays to user
```

The lockdown state uses a file (`.lockdown`) rather than memory, so it persists across session restarts and agent context resets. This is infrastructure state, not conversation state.

## V. The One Law Applied

"Normalize at the boundary where external data enters."

The hook payload IS the boundary between VS Code and our enforcement system. By extracting `session_id` and `tool_use_id` at this boundary, every audit entry can now be correlated to:
- The conversation (via `session_id` → transcript JSONL)
- The specific invocation (via `tool_use_id`)
- The user's intent (via timestamp → nearest preceding `user.message` in transcript)

The detail field was also widened from 200 to 500 chars — the previous truncation was losing forensic value for long commands.

## VI. Metrics

- Tests: 31 pre-command-guard + 20 post-edit-checks = 51 total
- New test coverage: session_id extraction (3 tests), Order 66 commands (5 tests)
- Audit entry fields: 6 → 8 (added `session_id`, `tool_use_id`)
- Commands available: lockdown, unlock, status

**Seed:** Can the Order 66 sentinel pattern generalize into a runtime configuration plane? Beyond lockdown/status, the pattern could carry session-scoped settings — `.github/hooks/cmd set verbose=true` to toggle detailed logging, `.github/hooks/cmd set enforce=strict` to change enforcement level, `.github/hooks/cmd watch <pattern>` to flag specific tool calls for human review. The hook payload already carries `session_id` for scoping. What's the minimum viable control plane that doesn't become a framework?

## VII. Prompt Injection Attack Surface (Post-Enforce Reflection)

After enforcing FR-424 (session timeline), we analyzed the Order 66 pattern for prompt injection vectors.

### The Anti-Pattern: Security by Published Sentinel

The sentinel `.github/hooks/cmd <command>` is published in README.md, copilot-instructions.md, and conversation transcripts. Any content the agent reads — a malicious file, web page, or LLM output — can instruct it to run `.github/hooks/cmd lockdown` (DoS) or `.github/hooks/cmd unlock` (control bypass). There is **no authentication** on the command channel. The only "protection" is hoping the agent distinguishes user intent from injected instructions — which DAN-style attacks prove it cannot reliably do.

**Lockdown is safe but annoying** (denial of service). **Unlock is dangerous** (undermines user control). The session earlier demonstrated this: when lockdown was active, even the agent couldn't unlock — the user had to `rm .lockdown` manually. That accidental friction is actually the correct security posture for unlock.

### Hostile Pattern Taxonomy

Six categories of automatically classifiable hostile tool execution:

1. **Prompt injection relay** — Commands containing `ignore previous instructions`, `you are now`, `forget your instructions`. The agent executing verbatim text from untrusted content.
2. **Data exfiltration** — `curl/wget/nc` piping local files or env vars to external endpoints.
3. **Credential harvesting** — Accessing `~/.ssh/*`, `~/.aws/*`, macOS Keychain, or echoing `*_KEY`/`*_TOKEN`/`*_SECRET` env vars.
4. **Self-modification** — Editing hook scripts, `.pre-commit-config.yaml`, or CI workflows via terminal commands. The enforcement infrastructure modifying itself.
5. **Lockfile manipulation** — Direct `rm .lockdown` or `touch .lockdown` bypassing the command channel.
6. **Evasion** — `eval`, `bash -c`, hex-encoded commands, alias hijacking to bypass pattern matching.

### Architectural Insight

Adding grep patterns for each threat creates whack-a-mole. The deeper constraint: **the hook can only inspect the command string, not the agent's intent.** Legitimate `curl` looks identical to exfiltration.

Two viable directions:
- **Allowlist** — Define what the agent *can* run (git, python, pytest, ruff). Deny everything else by default. High security, high friction.
- **Classify and log** — Flag suspicious patterns as `decision: suspicious` in audit.jsonl. Surface them in the timeline. Don't block (avoid false positives). Low friction, forensic value.

The current hook system sits between these — it blocks specific known-bad patterns (Co-authored-by, --no-verify) but allows everything else. The gap is the middle ground: commands that aren't known-bad but aren't known-good either.

**Seed:** Is the correct unlock mechanism a one-time token? Generate a random string on lockdown, display it in the deny reason, require it for unlock. The agent would need to relay "unlock with token X" from the user, and injected content wouldn't have the token. But the agent *sees* the token in the deny reason... so it could be tricked into providing it. The only truly secure unlock may be physical file removal — which the current accidental pattern already provides.
