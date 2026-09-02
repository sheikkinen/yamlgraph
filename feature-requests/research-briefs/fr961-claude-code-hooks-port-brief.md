# Problem brief: the lifecycle-hook enforcement layer fires for one agent and is silent for the other

**Prior art:** FR-438 (`feature-requests/FR-438-thoughtcrime-hook.md`)
introduced the transcript reasoning scan and one-shot sentinel; FR-439
(`feature-requests/FR-439-tone-down-enforcement-terminology.md`) renamed
it to `reasoning-pattern-check`; FR-883 extended its registry with the
FR-885 concealed-refusal family and its judgement R-1 forbade
overclaiming what the hook timing actually guarantees. FR-414 added the
audit trail, FR-440 the pipe-buffer guard, FR-662 the main-worktree
branch guard, FR-767 the graph-authoring sole-route guard, FR-743 the
SessionStart briefing probe, FR-877 the memory advisory. All of them
live in `.github/hooks/` and all key on VS Code Copilot tool names.
FR-163 put chaplain inbox instructions into `CLAUDE.md`; it is the only
prior FR that addresses the Claude Code surface, and it addresses
instructions, not hooks. No prior FR proposes registering the hook layer
for a second agent runtime; a REJECTED-FR sweep found nothing on the
topic.

## Problem statement

Every deterministic enforcement rule this repo relies on at agent-session
time (Co-authored-by trailer block, `--no-verify` block, multiline `-m`
trap, pytest pipe-buffer guard, main-worktree branch guard, the FR-767
governed-write guard, the FR-438/883 reasoning-pattern sentinel,
per-edit ruff/size/term checks, the FR-414 audit trail, the FR-743
session briefing) is registered only as VS Code Copilot hook JSON under
`.github/hooks/*.json`. Claude Code discovers hooks from
`.claude/settings.json` (project), `.claude/settings.local.json`, or
`~/.claude/settings.json` (user), none of which exist in this repo or on
the operator's Windows host. A Claude Code session in this repo
therefore runs with zero hook enforcement: the Scripture is advisory
text and nothing else.

The two runtimes share the hook contract almost exactly: the same
lifecycle event names (`PreToolUse`, `PostToolUse`, `SessionStart`,
`UserPromptSubmit`, `Stop`, `PreCompact`, `SubagentStop`), the same
stdin fields (`tool_name`, `tool_input`, `session_id`, `cwd`,
`hook_event_name`, `transcript_path`), and the same deny output shape
(`hookSpecificOutput.permissionDecision`) that `pre-command-guard.sh`
already emits. What differs is (a) the registration file and its one
extra nesting level with a `matcher` regex, (b) the tool vocabulary,
Copilot's `run_in_terminal`, `create_file`, `replace_string_in_file`,
`multi_replace_string_in_file`, `apply_patch` with `filePath` and
`replacements[]` versus Claude Code's `Bash`, `Write`, `Edit`,
`MultiEdit`, `NotebookEdit` with `file_path`, `old_string`,
`new_string`, `edits[]`, and (c) the transcript.

The transcript difference is the substantive one. The reasoning-pattern
check was specified (FR-438 Research section) against the Copilot
transcript: `assistant.message` entries carrying a `reasoningText` field
with the model's chain-of-thought, discovered by globbing
`~/Library/Application Support/Code/User/workspaceStorage/*/GitHub.copilot-chat/transcripts/<sid>.jsonl`.
Claude Code writes `~/.claude/projects/<slug>/<session_id>.jsonl` with
`type: "assistant"` entries whose `message.content[]` holds `thinking`,
`text`, and `tool_use` blocks, one JSONL line per block, grouped by
`requestId`. Measured on this host across four sessions, most `thinking`
blocks persist only a `signature` with an empty `thinking` string, and
the ones that carry text are short visible progress summaries, not the
reasoning the FR-885 phrases were witnessed in. The mechanism's premise,
that private reasoning is observable at the hook boundary, does not
transfer. What transfers is the `content` fallback FR-438 already
shipped for the no-extended-thinking case.

The problem: the repo has one enforcement layer with two runtimes, and
the layer's own doctrine (instructions and model behaviour are an
untrusted boundary, per the Scripture and FR-883) is enforced on only
one of them, while the unenforced runtime is the one currently operating
this Windows host.

## Classification

enforcement/latency-critical

## Constraints

- One set of hook scripts, two registrations. Rules must not drift
  between agents; a rule that exists for Copilot and not for Claude Code
  (or vice versa) is the defect this brief names, so the fix cannot
  introduce a second copy of the guard logic.
- The Copilot registration under `.github/hooks/*.json` and its tests
  under `.github/hooks/tests/` must keep passing unchanged; the tests
  are the contract witnesses for the shared scripts.
- No overclaim (FR-883 judgement R-1, binding precedent): any statement
  about what the reasoning-pattern check covers on Claude Code must
  match what the transcript actually persists, visible text and visible
  summaries, not private reasoning. The FR must say so in its
  first-consumer line, not in a footnote.
- The PostToolUse-scan, sentinel, next-PreToolUse-deny timing remains
  the authorized shape; whether Claude Code's PostToolUse `decision:
  block` feedback path is used in addition is a design decision for the
  FR, not a licence to remove the sentinel.
- Enforcement infrastructure changes require human review before merge
  (FR-883 judgement R-4). The FR inherits that gate.
- Hook budget: every script must complete inside its declared timeout
  (5 s guard, 10 s post-edit checks) on both runtimes. Transcript scans
  must stay O(latest message), not O(session).
- Windows host reality: `python3` on PATH resolves to the Windows Store
  3.10 stub, the venv interpreter is `.venv/Scripts/python.exe` while
  the scripts hardcode `.venv/bin/python`, and Git Bash is the only
  shell that can run them. The port must not silently succeed by doing
  nothing (fail-open is acceptable only with an audit record, per the
  FR-877 pattern); it must also not block the session when the
  interpreter is absent.
- Session-id path-traversal guard (FR-438 AC) and the sentinel's
  session isolation must hold: Claude Code session ids are UUIDs, so the
  existing regex is the contract, not a new one.
- The `.github/hooks/logs/` audit trail stays the single sink; entries
  must record which runtime produced them so the FR-424 timeline join
  can distinguish the two.
- `is_this_a_graph`: must be answered. The research must state whether
  any graph-shaped construct (the FR-425 classifier daemon, a yamlgraph
  pipeline over the transcript) belongs at this boundary, or whether
  this is necessarily a shell-level registration and adapter contract.

## Witnessed incidents

- 2026-09-02, this host: `.github/hooks/logs/audit.jsonl` does not
  exist; only `memory-curation-audit.jsonl` is present. No hook has ever
  fired for any agent on this machine. The FR-414 audit trail, the
  FR-767 governed-write guard, and the FR-883 sentinel have zero
  observations for every Claude Code session run here.
- 2026-09-02, transcript measurement, `~/.claude/projects/C--src-yamlgraph/*.jsonl`
  (four sessions, model `claude-fable-5-1`): 228 `thinking` blocks,
  57 with non-empty text (25 percent), longest 534 characters; every
  non-empty sample reads as a one-sentence progress summary. The
  `reasoningText` premise of the FR-438 Research section does not hold
  for this runtime.
- `.github/hooks/scripts/reasoning-pattern-check.sh` lines 36-50 and
  `.github/hooks/scripts/session-timeline.py:52-73` hardcode the macOS
  Copilot workspaceStorage path for transcript discovery, although the
  hook input already carries `transcript_path` on both runtimes. The
  discovery step is the wrong abstraction and is the reason the scan
  cannot run on any other OS or agent today.
- `.github/hooks/scripts/pre-command-guard.sh:91,114,240-241,282,310`,
  `.github/hooks/scripts/checks/common.sh:12` and
  `.github/hooks/scripts/checks/main_write.py:47-50` allowlist Copilot
  tool names only; a Claude Code `Bash` or `Edit` call would fall
  through every check as a non-terminal, non-edit tool and be approved.
- FR-883 judgement R-1: the FR draft overclaimed "denial before first
  tool spend"; the judge corrected it to "denial of the next tool call
  after the scan arms the sentinel". The same overclaim risk applies
  with more force when the scanned surface shrinks from reasoning to
  visible text.
- FR-955 research run, 2026-09-02, Windows host: the route ran but the
  verifier reported a CRLF/LF hash mismatch on a byte-identical
  promotion. The hook and research shell layers have already shown
  undeclared text-boundary defects on this host (FR-951 class).
- `.pre-commit-config.yaml` local hooks and `session-briefing.sh`,
  `memory-advisory.sh` reference `.venv/bin/python`; on this host that
  path does not exist and the scripts fall back to the Store `python3`
  or exit 0 silently.
