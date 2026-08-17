# Feature Request: Discord `/hello` Slash-Command Example

**Priority:** LOW
**Type:** Feature
**Status:** Enforced 2026-08-17 — AC-04 live guild acceptance PASSED (log in examples/discord_bot/README.md)
**Effort:** 1 day
**Requested:** 2026-08-17
**First consumer / first event:** an internal test-guild member types
`/hello name:Maija style:playful` and receives the hello graph's structured
greeting as a Discord embed — the first observed interaction→graph→message
round trip for the chat-initiated outbound-calls plan
(`docs/plan-chat-initiated-outbound-calls.md`, Phase 3 seam).

**Prior art:** grepped `feature-requests/` for discord/bot/slash/chat-command —
no prior FR. Closest case law is FR-070 (`yamlgraph serve` web playground,
REJECTED 2026-02-21, "No UI, ever; text is the interface"). Disposition: FR-070
banned a visual *authoring* surface; this FR adds a text-command *execution*
adapter in `examples/` (presentation layer, like `examples/npc` HTMX and
`examples/openai_proxy`), authoring nothing and rendering an existing graph's
output. The graph remains the interface; Discord is a caller.

## Summary

Add `examples/discord_bot/`: a minimal gateway bot that registers a
guild-scoped `/hello` slash command and executes the existing
`examples/demos/hello/graph.yaml` unmodified via the async seam
(`load_and_compile_async` + `run_graph_async`), replying with the structured
greeting as an embed. Document setup and usage in the example README and link
it from the repo README's examples section.

Plan of record: `docs/plan-discord-yamlgraph-poc.md`.

## Value Statement

Demonstrates to integrators that a chat platform can drive a YAMLGraph
pipeline with ~zero framework changes, and banks the Discord adapter seam
(defer/followup, option→state mapping, embed rendering) that the outbound-calls
plan builds on.

## Problem

The chat-initiated outbound-calls plan assumes "Discord adapter over an
existing pipeline" is cheap, but the repo has no executed evidence: no example
maps a slash-command interaction to graph variables, survives the 3-second
acknowledge deadline against LLM latency, or renders a `state_key` result back
into chat. Without a witness example, Phase 3 of that plan rests on an untested
assumption.

## Ideal Result

A tester in the designated guild runs `/hello` with any of three styles and
gets the greeting embed within seconds; a missing provider key yields a clean
ephemeral error, not a hang; `git diff` shows changes only under
`examples/discord_bot/`, its tests, and README linkage. Deleting the directory
leaves YAMLGraph untouched.

## Proposed Solution

Three-layer split — bot code is presentation only:

```
examples/discord_bot/
  README.md        # token/guild setup, install line (pinned discord.py), usage, run log
  bot.py           # gateway client, command sync, defer → run_graph_async → followup
  adapter.py       # pure: options → initial state; result state → embed fields
tests/unit/test_discord_hello_adapter.py  # adapter.py only, no network
```

- `/hello` options: `name` (string, required, 1–80 chars), `style` (required,
  choices `formal|casual|playful`).
- Manual acceptance environment (R-2, human decision 2026-08-17): a **fresh
  Discord application + private guild** created for YAMLGraph examples;
  identifiers supplied via `DISCORD_BOT_TOKEN` / `DISCORD_GUILD_ID`.
- `bot.py` compiles the hello graph once at startup; each interaction is an
  independent `run_graph_async` call; always `defer()` before the graph run
  (3s ack deadline), reply via `followup.send()` guarded by `asyncio.timeout`.
- Render `state["greeting"]` (`greeting`, `emoji`, `formality_level` per
  `prompts/greet.yaml` schema) as one embed; errors surface as an ephemeral
  message with a server-side-logged correlation ID — no fallback greeting.
- Config via env: `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`; never logged.
- `discord.py` frozen at exactly `discord.py==2.7.1` (R-3; latest stable,
  2026-03-03), pinned in the example README install line only — no new core
  or dev extra.

README usage (example README + one line in the repo README examples table):

```bash
pip install "discord.py==2.7.1"
export DISCORD_BOT_TOKEN=... DISCORD_GUILD_ID=...
python examples/discord_bot/bot.py
# in Discord: /hello name:Maija style:playful
```

## Acceptance Criteria

- [ ] `adapter.py` unit tests pass with zero network: option→state mapping,
      embed rendering from a canned `greeting` dict, and the error path.
- [ ] Manual acceptance in the test guild, run log pasted into the example
      README: all three styles; two overlapping invocations reply correctly
      without crossing; unset provider key produces the ephemeral error; bot
      restart re-syncs the command without duplicates.
- [ ] `examples/demos/hello/` byte-identical (no graph authoring; the
      graph-authoring doctrine is not triggered).
- [ ] No `yamlgraph/` core changes; no new dependency outside the example
      README install line.
- [ ] Repo README links the example; example README documents token setup,
      guild scoping, and the 3-second defer rationale.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-600")` (R-4); a new registry file
      `capabilities/CAP-239-discord-hello-example.yaml` declares REQ-YG-600 and
      is authorized by this FR. Re-run the CAP/REQ `uniq -d` duplicate check at
      push time (allocation-race precedent).

## Alternatives Considered

- **HTTP interactions endpoint** (public URL + Ed25519 signature check):
  production-appropriate, PoC-hostile; rejected for the example.
- **Generic `/run <graph>` command:** an authorization surface, not a PoC;
  explicitly out of scope (`growth_as_default`).
- **Documenting the pattern without code:** rejected — the 3s-deadline vs
  LLM-latency interaction is exactly the kind of claim that needs a witness
  (Commandment 2).

## Related

- `docs/plan-discord-yamlgraph-poc.md` (plan of record)
- `docs/plan-chat-initiated-outbound-calls.md` (Phase 3 consumer)
- `examples/demos/hello/` (executed graph, unchanged)
- `yamlgraph/executor_async.py` (`load_and_compile_async`; re-exports
  `run_graph_async`), `yamlgraph/observability/async_run.py` (implementation;
  R-1 — corrected after the FR-811 module move)
- FR-070 (rejected playground — dispositioned above)

## Judgement (2026-08-17)

**Verdict:** APPROVED WITH REVISIONS — rendered via the sole judge route
(`scripts/judge.sh`, gpt-5.5); full verdict, frozen scope, revised acceptance
criteria, and enforcement gates in
`FR-812-discord-hello-slash-command-example.judgement.md`.

| # | Finding | Resolution (folded 2026-08-17) |
|---|---------|--------------------------------|
| R-1 | Cited `yamlgraph/executor_async_run.py` no longer exists (FR-811 moved it) | Related section now cites `yamlgraph/executor_async.py` + `yamlgraph/observability/async_run.py` |
| R-2 | Manual acceptance guild/bot identity unresolved | Human selected fresh Discord application + private guild |
| R-3 | `discord.py==2.x.y` placeholder | Frozen at `discord.py==2.7.1` |
| R-4 | Requirement ID delegated to enforcer | REQ-YG-600 via new `capabilities/CAP-239-discord-hello-example.yaml` |

### Questions for the human (as options, or 'none')

None — the single parked question (acceptance identity) was answered at
judgement time.

## Implementation Notes (2026-08-17)

- RED `68ebffa6` (tests + CAP-239/REQ-YG-600 registry — the traceability gate
  requires the registry to be born with the condemning test), GREEN follows.
- Delivered: `examples/discord_bot/{adapter.py,bot.py,__init__.py,README.md}`,
  `tests/unit/test_discord_hello_adapter.py` (16 tests, zero network),
  catalog rows in `examples/README.md` + repo `README.md`, changelog fragment.
- Verified: 16/16 GREEN, `req_coverage --strict` pass, `ruff` clean,
  `examples/demos/hello/` byte-identical (AC-05), no dependency manifest
  changes (AC-06, gate C-3).
- Deviation: none from frozen scope; D-6 (CAP-239) exercised as authorized.
- Pending: AC-04 manual acceptance log in the example README after the live
  guild run (fresh app + private guild per R-2).
- AC-04 completed 2026-08-17: three styles, overlap (replies 380ms apart, not
  crossed), restart re-sync (1 command, no duplicates), invalid-key 401 →
  ephemeral error with correlation_id=f24fd16ac50c. Post-judgement fix: bot.py
  inserts repo root into sys.path (script-path execution defect found live).
  Error-path testing gotcha: yamlgraph config.py load_dotenv restores unset
  provider keys from .env — override with an invalid value instead.
