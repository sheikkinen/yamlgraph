# Research: Discord UI Surfaces Beyond Plain Messages

**Date:** 2026-08-18
**Status:** Research complete — no implementation authorized by this document
**Sources:** Discord developer docs fetched 2026-08-17/18 (`components/reference`,
`interactions/application-commands`, `events/gateway-events`,
`activities/overview`); live FR-812 acceptance run
**Consumers:** the chat-initiated outbound-calls plan
([plan-chat-initiated-outbound-calls.md](plan-chat-initiated-outbound-calls.md),
Phase 3 Discord adapter) and any future `examples/discord_bot/` extension
**Baseline:** FR-812 proved the interaction seam live — gateway WSS, guild
slash command, `defer()` → graph → followup embed
([examples/discord_bot](../examples/discord_bot/))

## The interaction model everything rides on

All surfaces below arrive as `INTERACTION_CREATE` events down the bot's one
outbound gateway WebSocket and are answered over REST — the FR-812
architecture carries every tier with zero new infrastructure:

- **3-second acknowledge deadline** per interaction; `defer()` buys a
  15-minute followup window (interaction token as temporary webhook).
- Interactive components round-trip a developer-defined `custom_id`
  (1–100 chars) — the routing key for command dispatch, and where a
  call-scoped payload (e.g. `macro:greet:CA123`) lives.
- Message updates are edits of the bot's own message — a message can behave
  as a **live dashboard** re-rendered on each event.

## Tier 1 — Message components (Components V2)

Enabled per message by flag `1 << 15` (`IS_COMPONENTS_V2`). Consequences:
`content` and `embeds` are replaced by components, attachments must be exposed
via components, `poll`/`stickers` disabled, up to **40 components** per
message, and the flag cannot be removed from a sent message. Legacy mode
(components alongside `content`, max 5 action rows) remains supported.

| Type | Component | Usage | Notes / limits |
|---|---|---|---|
| 1 | Action Row | Message | Container: up to 5 buttons XOR 1 select |
| 2 | Button | Message | Styles: primary/secondary/success/danger/link/premium; label ≤ 80 chars (≤ 34–38 rendered); non-link buttons need `custom_id` |
| 3 | String Select | Message, Modal | ≤ 25 options; multi-select via `min/max_values`; option = label+value+description+emoji |
| 5–8 | User / Role / Mentionable / Channel Select | Message, Modal | Auto-populated from the guild; `default_values`; channel-type filter |
| 9 | Section | Message | 1–3 Text Displays + one accessory (Button or Thumbnail) |
| 10 | Text Display | Message, Modal | Markdown block incl. mentions (allowed-mentions applies) |
| 11 | Thumbnail | Message | Image accessory for Section |
| 12 | Media Gallery | Message | 1–10 media items, spoiler/alt-text |
| 13 | File | Message | Renders an `attachment://` upload |
| 14 | Separator | Message | Divider + spacing control |
| 17 | Container | Message | Visual grouping with **accent color bar**, spoilerable |

**Operator-console reading:** a call thread's pinned bot message can be a
composed **call card** — Container (accent = call state) holding Text Display
(status + last transcript line), a Section with a Hang Up danger button, an
Action Row of macro buttons, and a String Select for the long macro tail.
State changes are edits; terminal state disables components (`disabled: true`).

## Tier 2 — Modals (forms as interaction responses)

Response `type: 9` opens a client-rendered form; submit returns
`MODAL_SUBMIT` with all values. Modal-only components, each wrapped in a
**Label** (type 18, label ≤ 45 chars + description):

| Type | Component | Limits |
|---|---|---|
| 4 | Text Input | short/paragraph styles; `min/max_length` 0–4000; placeholder; pre-filled `value`; `required` |
| 21 | Radio Group | 2–10 options, single choice |
| 22 | Checkbox Group | 1–10 options, `min/max_values` |
| 23 | Checkbox | single boolean |
| 3, 5–8 | Selects (string/user/role/mentionable/channel) | `required` honored in modals |
| 19 | File Upload | 1–10 files, `file_types` filter (extension-based) |

Validation (length, required, choice bounds) is **declared, client-enforced**
— the adapter receives pre-validated input instead of parsing free text.

**Operator-console reading:** `/call start` should open a modal — phone number
(Text Input with length bounds), script/profile (Radio Group), consent
(required single-option Checkbox Group). This is strictly better input
discipline than slash-command options.

## Tier 3 — Command surfaces beyond `/slash`

- **User commands** (type 2) and **message commands** (type 3): app entries in
  right-click context menus; no options, return the clicked user/message.
  *Message command "Speak to caller" on any thread message is the most natural
  macro-from-text gesture available.*
- **Autocomplete** on string/int/number options: server-driven suggestions as
  the operator types (allowlisted destinations, macro names); partial input
  arrives with `focused: true`; suggestions are not validated server-side —
  treat as untrusted.
- **Subcommands / groups**: `/call start|say|macro|status|hangup` under one
  command; one level of group nesting; base command becomes unusable.
- **Command permissions**: `default_member_permissions` bitset,
  per-role/user/channel overrides (≤ 100), guild-scoped; the mechanical
  enforcement layer for "operator role only".
- **Ephemeral replies**: invoker-only visibility (already used for FR-812
  errors).
- **Localization**: `name/description_localizations` dictionaries with locale
  fallbacks — relevant if operator UI needs Finnish labels.

Registration limits worth remembering: 100 global CHAT_INPUT / 15 USER / 15
MESSAGE commands; 200 command creates per guild per day; guild commands sync
instantly, global cache up to ~1 h (why FR-812 pinned to one guild).

## Tier 4 — Channel-structure primitives

- **Threads** — one per call (already the plan); auto-archive; thread member
  events on the gateway.
- **Forum / media channels** — one post per case with tags; an alternative to
  threads for a case-queue shape.
- **Webhooks** — post into a channel under distinct name/avatar identities
  ("Caller", "System") without extra bot users; cheap speaker attribution in
  transcripts.
- **Polls** — native voting, `MESSAGE_POLL_VOTE_ADD` gateway events.
- **Pins, scheduled events, auto-moderation events** — auxiliary.
- **Voice channels** — a bot can join voice, play and receive audio
  (soundboard, voice status/effects events exist too). This is a *separate
  research rung*: live call-audio monitoring in Discord would compete with
  the existing `AudioMixer`/ffplay monitor; park until a consumer names it.

## Tier 5 — Activities (arbitrary web UI inside Discord)

Web apps in an **iframe** on desktop/mobile/web, communicating through the
Embedded App SDK (auth, user, and instance-state commands/events), launched
via a PRIMARY_ENTRY_POINT command from the App Launcher. Full HTML/JS —
waveforms, multi-call switchboards, anything.

Costs: the web app must be hosted (public URL) — forfeiting the
zero-infrastructure property that justified the gateway PoC — plus OAuth
inside the iframe and a heavier review surface.

**Doctrine note:** FR-070 ("No UI, ever; text is the interface") banned visual
*authoring* surfaces; its own rejection table sanctioned visual
*observability*. An Activity used as a read-only call monitor would need that
distinction argued explicitly in its FR; an Activity that *authors* graph or
call behavior is precedent-rejected. Either way it is far beyond current
consumers — recorded here so the graveyard check finds a disposition, not a
gap.

## Recommendation for the outbound-calls MVP

Everything the operator console needs lives in tiers 1–4, on the proven
FR-812 connection:

1. **Call card** — Container + Section + Text Display, edited per event;
   accent color as call state.
2. **Macros** — Action Row buttons (≤ 5 hot macros) + String Select (tail);
   `custom_id` carries `macro_id:call_sid`; server resolves macro text
   (buttons never carry speech).
3. **Dial form** — modal from `/call start`: number, profile, consent.
4. **"Speak this"** — message command on thread messages, replacing/augmenting
   the armed-thread free-text mechanism (more explicit, no Message Content
   intent anywhere).
5. **Authorization** — command permissions (operator role) + channel
   restriction, mechanically enforced by Discord before the bot sees the
   interaction.
6. **Speaker attribution** — webhook identities in the call thread.

Explicitly deferred: voice-channel audio monitoring (no named consumer;
existing mixer covers it) and Activities (infrastructure + doctrine cost, no
consumer).

## Seeds

- **Seed:** the call card is `state → components` — the same pure-adapter
  shape as `greeting_to_embed`. Should the channel-neutral Call Hub contract
  define an abstract "card" (status, lines, actions) that each adapter renders
  natively (Components V2 / Block Kit / Ninchat text), so macros and hangup
  are declared once?
- **Seed:** `custom_id` is a 100-char attacker-visible routing key. The
  fail-closed rule for it (signed? nonce-checked against the call registry?)
  belongs in the Call Hub command contract before any button ships.
