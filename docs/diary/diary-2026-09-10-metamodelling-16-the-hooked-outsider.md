# The hooked outsider: a rung-3 oracle at a rung-1 boundary, and the one channel it has

**Date:** 2026-09-10
**Series:** metamodelling, part 16 (applied)
**Trigger:** operator: "circling back to hooks + mercury pattern, i.e.
quick adversarial feedback. would there be use for that" → "how would
hooked outsider communicate with the agent".
**Context:** the series' recurring ask is to move checks from the
publication boundary to the generation boundary. The repository's hooks
are that boundary; today they are regex. A fast cheap model in the hook
is what would let a prose rule fire there. This entry says where that
pays, where it becomes an ordeal, and — reading the hook contract in
`.github/hooks/README.md` — what channel it actually has.

## What it is, in the series' terms

Hook = boundary. Mercury = cheap independent reader. Adversarial =
`forced_opposite` with input closure. Together: **an independent-LLM
oracle (rung 3) firing at the tool call (rung 1), on every action, cheap
enough to survive the deadline** (part 5). Today's Scripture prose rules
are advisory — `detection_without_enforcement`; this is the mechanism
that closes that gap without a full judge per write.

## Where it pays

| # | Hook | Boundary | Mercury sees (input closure) | First event / fail state |
|---|---|---|---|---|
| 1 | Claim-typer on writes to `docs/diary/**`, `feature-requests/**`, the Scripture | PostToolUse | the text + one rule: fact-typed claims carry an anchor | RED exists: the 83 Knowledge Graph lines, must flag ≈47. A week with zero flags = ordeal |
| 2 | Instruction-list check on `git commit` / `push` / `gh pr merge` / first code edit | PreToolUse | operator's last message + the action class | the 2026-09-06 "fr. judge. outsider. merge → GREEN commit" case; one-shot deny naming the omitted verb |
| 3 | Anchor drift on citations in generated `.md` | PostToolUse | claim + fetched passage; existence is a resolver, mercury does only "does the passage say that" | the 1-in-3 case (part 11) |
| 4 | Outsider-lite on PR bodies | PostToolUse | body only | FR-995 exists at full size; mercury makes it per-edit |
| 5 | Rule text vs action, all commands | PreToolUse | command + conventions block | lowest precision; run last, after 1–4 have override data |

## Where it fails — each already named in the series

- **Alert fatigue (part 6).** Warn on every write → overridden by reflex
  in days → every other hook degrades. Override rate logged from the
  first run; above roughly half, retune or remove.
- **`model_as_trusted_peer`.** A model in the enforcement path is opaque
  weights. It advises and may arm a one-shot denial; it never hard-blocks
  alone. Its output is a *claim* reconciled against the artifact
  (`two_strike_split`).
- **`confession_under_pressure` (part 8).** If mercury sees the chat it
  sees the author's case and confirms it. Artifact + rule, nothing else.
- **`two_strike_split`.** Same finding twice on the same class → the
  pattern belongs in regex/AST; mercury is the discovery layer for new
  mechanical gates, not their home.
- **Ordeal.** A weekly canary — a deliberately unanchored fact — must be
  flagged, or the guard is not alive.
- **Speed.** Hooks already feel slow. Per-call budget; over budget →
  advisory async, never silently skipped without an audit line.

## The channel, read from the contract

`.github/hooks/README.md` is explicit: VS Code has no user-prompt hook;
PostToolUse cannot address the agent; **the deny reason on PreToolUse is
the only synchronous text the agent reads**. The repo already uses this:
`reasoning-pattern-check.sh` (PostToolUse) arms a one-shot sentinel that
`pre-command-guard.sh` consumes on the next PreToolUse, and the command
channel (`lockdown|unlock|status`) is a sentinel pattern denied with the
response in the reason. The async classifier is forensic only.

So the hooked outsider communicates like this, and only like this:

1. **PostToolUse:** mercury reads the artifact under closure, writes a
   verdict record to `.github/hooks/state/` keyed by session and target
   path, appends to `audit.jsonl`, arms a one-shot sentinel **bound to
   the target artifact and to the commit/push/merge action class** — not
   to "the next tool call", which may be unrelated and would make the
   denial land on the wrong action.
2. **Next PreToolUse that touches the artifact or reaches the bound
   action:** `pre-command-guard` consumes the sentinel and denies once,
   with the verdict record as the reason.
3. **The agent proceeds by re-issuing the action.** That re-issue is the
   acknowledgement, and it is logged as an **override** with the finding
   it overrode — the census's override-rate column, produced as a
   side effect of the channel.

### Shape of the message

Decision-shaped, not prose. The agent reads it as tool output; hedges
are lost tokens.

```
HOOKED-OUTSIDER (mercury, adversarial, input-closed) — claim, not verdict
artifact:  docs/diary/diary-2026-09-10-....md:41
finding:   fact-typed claim without anchor: "Shepard's from the 1870s"
rule:      part 4 / claim typing — fact carries FR-/NC-/URL/file:line/date
proceed:   re-run the same command to override (logged), or edit and retry
```

Five properties, each traced to a series finding:

- **Declares its agenda** on line one (part 13: the only field that
  declares agenda is medicine; here it is free). The agent must treat the
  message as adversarial input from a model, per Scripture, and the
  message says so itself.
- **Says "claim, not verdict."** The agent reconciles against the
  artifact; the outsider has no authority, only an observation.
- **One shot.** The outsider has no memory and no turn two. There is no
  dialogue; a disagreement is a one-line disposition the agent writes
  into the artifact or commit body, and both finding and disposition
  reach the human in the PR.
- **Locator + rule + proceed.** Nothing the agent cannot act on in one
  edit.
- **The agent never sees the outsider's prompt.** Otherwise the agent
  optimises for the checker rather than the rule (Goodhart), and the
  witness stops being independent.

### What it must not do

- Inject into the agent's context or system prompt. There is no such
  channel, and if there were it would be `confession_under_pressure` in
  reverse — the checker shaping the generator.
- Converse. A second message is a second oracle call with the first
  message in its window: `generator_as_own_oracle` with a costume.
- Block silently. Every deny has a reason and a proceed path; every
  timeout has an audit line.

## Across the fields, one line each

Law: cite-check as you draft, the boundary *Mata* lacked. Clinical:
second signature on free text; mechanical checks stay mechanical.
Journalism: CMS publish hook, populated before deadline or dropped at it.
Teaching: lesson editor hook for untyped claims and anachronism.
Strategy: decision-doc save hook for forecasts without date or
probability. Witchcraft: a fast confirmer with uninspectable inputs is
the swimming test at millisecond latency.

## Traps

**`feedback_without_a_channel`.** Designing the checker before reading
what the boundary can actually say. Here the answer was one deny reason,
one shot, on the next call — and that constraint decided the message.

**`checker_in_the_window`.** Letting the generator read the checker's
prompt, or the checker read the generator's chat. Either direction ends
the independence the design exists for.

## Heuristic

Before building an oracle at a boundary, read the boundary's contract
and name its one channel; design the message to that channel's shape
(one shot, decision-shaped, agenda declared, proceed path stated); log
the override as a side effect. Then run the RED that already exists.

**Seed:** hook 1 with the 83-line RED. If it flags ≈47 and the override
rate over one week of diary writes is under half, the channel works and
hook 2 follows. If overrides run high, the finding is about the rule,
not the hook — and that is a Scripture-editing FR, judged, not a hook
patch.
