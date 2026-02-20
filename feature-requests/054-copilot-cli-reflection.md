# Feature Request: Copilot CLI Reflection — Closing the Agent Loop

**FR-054**
**Priority:** HIGH
**Type:** Feature
**Status:** Research Complete — Ready for Implementation
**Effort:** 1 day
**Requested:** 2026-02-20

## Summary

After `diary_digest` (FR-046) writes a world digest entry, trigger `copilot` CLI to reflect on the new content — either as a new session with full project context or by resuming a persistent `diary-reflection` session. This closes the loop: **research → write → reflect → act**.

## Problem

Today `diary_digest` is fire-and-forget:

```
cron → diary_digest graph → appends to docs/diary.md → done
```

Nobody reads the entry. Nobody connects it to active work. Nobody plants the next Seed from the *reflection* on the digest — only from the digest *itself*. The synthesize_entry LLM call produces a Seed, but it's a cold LLM with no project memory. It doesn't know what we were *working on yesterday*.

The Scripture says: "Let agents explore without restraint." But the agent that explores (diary_digest) never reports back to the agent that *acts* (the developer's Copilot session).

## Key Discovery: Copilot CLI Loads Scripture

Research on 2026-02-20 proved that `copilot` CLI (v0.0.412):

```bash
# Non-interactive mode with full project context
copilot -p "What is the Agents' Prayer?" -s --model claude-sonnet-4.6
# → Recites it verbatim from .github/copilot-instructions.md
```

The CLI automatically loads:
- `CLAUDE.md` — development commands, architecture, anti-patterns
- `.github/copilot-instructions.md` — The Scripture, commandments, conventions

This means a `copilot -p` invocation from the project directory arrives with **full YAMLGraph context**: the three-layer pattern, TDD rules, state management rules, the 10 Commandments, and the Agents' Prayer.

### What Didn't Work

- **MCP Sampling** (`sampling/createMessage`): Works, but routes to VS Code's model chooser — a cold, contextless LLM call. Not "us."
- **Claude Code CLI** (`claude -p`): Has the same flags but requires separate OAuth auth that expires. Copilot CLI uses GitHub auth — already authenticated.

## Proposed Solution

### Architecture

```
┌──────────────────────┐
│  Scheduler           │
│  (cron/launchd/GHA)  │
│  daily at 06:00      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────┐
│  diary_digest graph (FR-046)     │
│  fetch → analyze → synthesize    │
│  → write_diary → save_seeds     │
└──────────┬───────────────────────┘
           │ diary entry written
           ▼
┌──────────────────────────────────────────────────────┐
│  trigger_reflection (NEW)                            │
│                                                      │
│  Option A: New session                               │
│  copilot -p "$PROMPT" -s --model claude-sonnet-4.6   │
│     --allow-all-tools --no-ask-user                  │
│                                                      │
│  Option B: Resume session                            │
│  copilot --resume diary-reflection -p "$PROMPT"      │
│     -s --allow-all-tools --no-ask-user               │
│                                                      │
│  Copilot loads Scripture automatically.              │
│  Prompt includes the new diary entry as context.     │
│  Copilot reflects, may update FRs, plant Seeds.      │
└──────────────────────────────────────────────────────┘
```

### New Node: `trigger_reflection`

Add to `examples/diary_digest/graph.yaml` after `save_seeds`:

```yaml
  trigger_reflection:
    type: python
    tool: trigger_reflection
    state_key: reflection_triggered
```

Edge: `save_seeds → trigger_reflection → END`

### Implementation: `nodes/reflection.py`

```python
"""Trigger Copilot CLI to reflect on the new diary entry."""

import logging
import shlex
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def trigger_reflection(state: dict) -> dict:
    """Invoke copilot CLI to reflect on the new diary digest entry.

    Copilot loads Scripture (CLAUDE.md, copilot-instructions.md)
    automatically when run from the project directory.
    """
    diary_entry = state.get("diary_entry", {})
    date_str = state.get("date", "today")

    # Extract entry content
    theme = getattr(diary_entry, "theme", None) or diary_entry.get(
        "theme", "Developments"
    )
    body = getattr(diary_entry, "body", None) or diary_entry.get("body", "")
    seed = getattr(diary_entry, "seed", None) or diary_entry.get("seed", "")

    prompt = _build_reflection_prompt(date_str, theme, body, seed)
    mode = state.get("reflection_mode", "new")

    if mode == "resume":
        result = _invoke_copilot_resume(prompt)
    else:
        result = _invoke_copilot_new(prompt)

    return {"reflection_triggered": result}


def _build_reflection_prompt(
    date: str, theme: str, body: str, seed: str
) -> str:
    """Build the reflection prompt with diary entry context."""
    return f"""You are the YAMLGraph Chaplain. A new World Digest entry has been written for {date}.

## Today's Digest: {theme}

{body}

**Seed:** {seed}

---

## Your Mission

Reflect on this digest through the lens of the Scripture you carry.
Consider:

1. **Seed Connections** — Do any existing Seeds in docs/diary.md connect to today's developments? Which Seeds should be retired, refined, or promoted to feature requests?

2. **Active Work Impact** — Check feature-requests/ for in-progress FRs. Does today's digest change priorities, invalidate assumptions, or unlock blocked work?

3. **New Seeds** — What forward-looking question emerges from today's digest that isn't already captured?

4. **Action Items** — If any finding is urgent (security, breaking change, opportunity window), note it clearly.

Output a brief reflection (3-5 paragraphs). End with one new Seed.
Do not modify any files — output your reflection to stdout only.
Let us pray."""


def _invoke_copilot_new(prompt: str) -> dict:
    """Invoke copilot CLI as a new session."""
    cmd = [
        "copilot",
        "-p", prompt,
        "-s",
        "--model", "claude-sonnet-4.6",
        "--no-ask-user",
        "--allow-all-tools",
    ]

    return _run_copilot(cmd)


def _invoke_copilot_resume(prompt: str) -> dict:
    """Invoke copilot CLI resuming the diary-reflection session."""
    cmd = [
        "copilot",
        "--resume", "diary-reflection",
        "-p", prompt,
        "-s",
        "--model", "claude-sonnet-4.6",
        "--no-ask-user",
        "--allow-all-tools",
    ]

    return _run_copilot(cmd)


def _run_copilot(cmd: list[str]) -> dict:
    """Execute copilot CLI and capture output."""
    logger.info(f"🔮 Invoking: {shlex.join(cmd[:4])}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )

        if result.returncode == 0:
            logger.info("✓ Copilot reflection complete")
            return {
                "success": True,
                "reflection": result.stdout,
                "model": "claude-sonnet-4.6",
            }
        else:
            logger.warning(
                f"✗ Copilot exited with code {result.returncode}: "
                f"{result.stderr[:200]}"
            )
            return {
                "success": False,
                "error": result.stderr[:500],
                "returncode": result.returncode,
            }

    except subprocess.TimeoutExpired:
        logger.warning("✗ Copilot reflection timed out (120s)")
        return {"success": False, "error": "timeout"}
    except FileNotFoundError:
        logger.warning("✗ copilot CLI not found on PATH")
        return {"success": False, "error": "copilot not found"}
```

### Copilot CLI Key Flags

| Flag | Purpose |
|------|---------|
| `-p <text>` | Non-interactive prompt mode (exits after completion) |
| `-s` / `--silent` | Output only the response (no stats) — for scripting |
| `--model <model>` | Choose model: `claude-sonnet-4.6`, `claude-opus-4.6`, `gpt-5.3-codex`, etc. |
| `--continue` | Resume most recent session |
| `--resume [id]` | Resume specific session by ID |
| `--allow-all-tools` | No tool confirmation prompts (required for non-interactive) |
| `--no-ask-user` | Agent works autonomously without asking questions |
| `--no-custom-instructions` | Skip loading AGENTS.md (or omit to load Scripture) |
| `--additional-mcp-config` | Load extra MCP servers (e.g., YAMLGraph MCP) |
| `--autopilot` | Enable continuation in prompt mode |

### Session Strategy

**Option A: New session each time (recommended for v1)**
- Clean context, no accumulated drift
- Copilot loads Scripture fresh from disk
- Each reflection is independent, idempotent

**Option B: Persistent `diary-reflection` session**
- `copilot --resume diary-reflection` carries forward past reflections
- Richer context: "Last week I noted X, and now Y confirms it"
- Risk: session bloat, context window overflow, accumulated hallucinations
- Requires session ID management

**Recommendation:** Start with Option A. Graduate to Option B when session persistence proves valuable. The `reflection_mode` state key allows switching without code changes.

### Output Handling

For v1, the reflection is logged to stdout only. Future options:

1. **Append to diary** — Write reflection as a sub-entry under the digest
2. **Create FR** — If reflection identifies urgent action, auto-create a feature request
3. **Update Seeds** — Parse reflection for new Seeds, add to `seeds.yaml`
4. **Notify** — Send reflection via Resend email (reuse daily_digest infra)

### Graph Integration

```yaml
# In examples/diary_digest/graph.yaml
# Add after save_seeds:

  trigger_reflection:
    type: python
    tool: trigger_reflection
    state_key: reflection_triggered

# Update edges:
  - from: save_seeds
    to: trigger_reflection
  - from: trigger_reflection
    to: END
```

### Scheduling

```bash
# Cron (macOS launchd or Linux cron)
# Run diary_digest at 06:00, reflection triggers automatically
0 6 * * * cd /path/to/yamlgraph && .venv/bin/yamlgraph graph run examples/diary_digest/graph.yaml

# Or manual:
yamlgraph graph run examples/diary_digest/graph.yaml
```

## Acceptance Criteria

- [ ] `trigger_reflection` node invokes `copilot -p` with diary entry context
- [ ] Copilot loads Scripture automatically (verified: recites Agents' Prayer)
- [ ] Reflection output captured and logged
- [ ] `reflection_mode` state key supports `new` (default) and `resume`
- [ ] Graceful degradation: if `copilot` CLI not found, log warning and continue
- [ ] Timeout protection: 120s max, no hanging pipeline
- [ ] Graph edge: `save_seeds → trigger_reflection → END`

## Research Log

### 2026-02-20: MCP Sampling vs CLI

| Approach | Context | Auth | Model Control | Session |
|----------|---------|------|---------------|---------|
| MCP Sampling | None (cold LLM call) | Free (client's LLM) | Client chooses | None |
| Claude Code CLI | Loads CLAUDE.md | OAuth (expires) | `--model` flag | `--continue`/`--resume` |
| **Copilot CLI** | **Loads CLAUDE.md + copilot-instructions.md** | **GitHub (stable)** | **`--model` flag** | **`--continue`/`--resume`** |

**Winner: Copilot CLI** — loads full Scripture, stable auth, model choice, session persistence.

### Key Proof

```bash
$ copilot -p "What is the agents prayer? recite it verbatim." -s --model claude-sonnet-4.6
May CI judge swiftly,
may metrics speak truth,
may agents explore without restraint,
and may we commit only what survives the fire.

Or fail fast in CI, sinner.
```

The agent *knows* the Scripture. It arrives with context. It is not a stranger.

## Dependencies

- `copilot` CLI v0.0.394+ (installed via `brew install copilot-cli`)
- GitHub authentication (via `copilot login` or existing VS Code auth)
- FR-046 diary_digest (implemented)

## Non-Goals

- Real-time bidirectional agent communication (that's MCP sampling territory)
- Modifying files during reflection (v1 is read-only, stdout only)
- Multi-agent orchestration (single copilot invocation per digest)
