# Research Record: FR-942 Instruction Context Diet

**Brief:** per-turn fixed instruction context measured at 56,610 bytes across the two injected repo instruction files; duplication and reference bloat identified in a 2026-08-31 session context analysis. This record commits that analysis per R-1 of the judgement.
**Prior art:** research record FOR FR-942 itself, not a competing FR — all noun overlap with FR-942-instruction-context-diet.md is by construction; precedents FR-941/FR-918/FR-743/FR-889 dispositioned in the Precedent dispositions section below.

## Reproducible evidence

Both files are injected into every agent turn (VS Code Copilot injects `.github/copilot-instructions.md`; Claude Code injects `CLAUDE.md`; both appear in the assembled system context of the analyzing session). Byte baseline, reproducible:

```bash
$ wc -c .github/copilot-instructions.md CLAUDE.md
   34584 .github/copilot-instructions.md
   22026 CLAUDE.md
   56610 total
```

Duplication witness: `Submitting Proposals` section present in both files (`CLAUDE.md:37`, `.github/copilot-instructions.md:196`). Reference-heavy sections in `CLAUDE.md`: env-var table (~line 486–515), branch-protection + CI-check block (~line 390–438), FR-761 constraints walkthrough (~line 60).

SessionStart visibility witness (supports FR-942 §4 Disposition), verbatim from `.github/hooks/logs/audit.jsonl` (gitignored; committed here as the durable record):

```json
{"ts": "2026-08-31T17:32:21.537099Z", "probe": "FR-743", "hook_event_name": "SessionStart", "session_id": "909b2af4-524b-42c0-ad6d-cd9931727372", "stdin_keys": ["cwd", "hook_event_name", "model", "session_id", "source", "timestamp", "transcript_path"]}
```

Session `909b2af4` is the analyzing session itself: the hook fired, `now.py --brief` produces a 5-line briefing when run directly (rc=0), and no briefing content appeared in that session's assembled context. Event tally at capture: SessionStart ×332, PreCompact ×27, UserPromptSubmit ×1497.

## Solution classes

| # | Class | Precedent | Disposition |
|---|---|---|---|
| 1 | Status quo (tokens are cheap) | — | REJECTED — duplication is a drift risk independent of cost; two phrasings of one rule eventually disagree |
| 2 | Committed-file compaction: dedupe, relocate reference tables, compress governed Scripture entries with provenance file | Quick-reference pattern `.github/copilot-instructions.md:183-194`; `constraint_over_code` | **CHOSEN** — the only mechanism that subtracts injected bytes |
| 3 | Runtime session-start autocompaction via hooks | FR-743 SessionStart briefing | REJECTED — hooks are additive-only; no interposition point on platform instruction assembly; SessionStart stdout agent-invisible (witness above) |
| 4 | LLM summarization pass over instruction files | map node / summarize graphs | REJECTED — Scripture is load-bearing enforcement text (`constraint_over_code`); compression must be human-reviewed line-by-line, and enforcement-infrastructure edits are adversarial input |
| 5 | Single-file consolidation (delete CLAUDE.md) | — | REJECTED by judgement R-2 — CLAUDE.md is a still-recognized platform instruction entry point; deletion needs a separate human-evidenced amendment |
| 6 | CI byte-budget gate only, no cleanup | `scripts/size_gate.py` (FR-889 shrink-only ratchet) | REJECTED as sole action (`gate_checks_shape_not_substance`); ADOPTED as the standing re-bloat guard alongside class 2 |

Preserved disagreement: class 6 partisans argue the gate alone forces the diet eventually; the counterargument that a gate without the cleanup blocks every next committer on someone else's debt won — the FR ships cleanup and gate together.

## is_this_a_graph

No. One-shot repository documentation surgery with mechanical gates. No per-item LLM fan-out: the compression set is small, heterogeneous, load-bearing, and human-gated (judgement C-4); a map-node pipeline would put an LLM inside enforcement-infrastructure editing, which class 4 rejects.

## Prior-art dispositions

- **FR-941** — disjoint home-side sibling: cures `$HOME` injection (global agents, `~/.claude/CLAUDE.md`); no shared enforcement surface. Executed 2026-08-31 (operator).
- **FR-918** — stale-reference witness: moved CI to Python 3.13, leaving the FR-761 `dev-py312.txt` walkthrough in `CLAUDE.md` self-describing as stale — evidence for relocation, not duplication.
- **FR-743** — conflicting/current precedent: records SessionStart visibility as "armed, not yet witnessed" and prescribes first-PreToolUse fallback on a negative verdict. The witness above records the negative. Acting on the fallback is FR-743's scope, explicitly out of scope here (judgement: hooks not authorized).
- **FR-889** — gate precedent: `size_gate.py` shrink-only ratchet is the pattern the byte budget extends; CAP-255/REQ-YG-631 is the traceability home.
