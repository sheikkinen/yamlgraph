# 2026-08-25 — The invoice audits the doctrine

**Context:** The operator shared the Copilot premium-usage billing table
(the image will vanish; the numbers are preserved below) and asked for a
reflection mapping cost to the pinned models in the governed paths —
the sole routes (author / judge / review) and the chaplain pipeline.

## The record (Copilot billing, period ending 2026-08-25)

Total: **$5,743.68 gross / $4,895.10 additional (paid overage)**.
Included credits 84,858.24; additional credits 489,510.23.

| Model | Included cr. | Additional cr. | Gross | Overage |
|---|---|---|---|---|
| Claude Fable 5 | 64,143.08 | 340,041.83 | $4,041.85 | $3,400.42 |
| GPT-5.6 Sol | 1,981.44 | 58,761.42 | $607.43 | $587.61 |
| GPT-5.5 | 5,429.46 | 24,252.95 | $296.82 | $242.53 |
| Claude Opus 4.6 | 0 | 28,755.41 | $287.55 | $287.55 |
| Claude Opus 5 | 245.93 | 18,919.09 | $191.65 | $189.19 |
| Claude Sonnet 5 | 63.47 | 18,264.43 | $183.28 | $182.64 |
| Claude Opus 4.8 | 12,958.77 | 0 | $129.59 | $0.00 |
| GPT-5.4 | 0 | 298.74 | $2.99 | $2.99 |
| GPT-5.4 mini | 0 | 115.28 | $1.15 | $1.15 |
| Claude Haiku 4.5 | 0 | 74.20 | $0.74 | $0.74 |
| Claude Sonnet 4.6 | 36.08 | 10.08 | $0.46 | $0.10 |
| GPT-5.3-Codex | 0 | 14.72 | $0.15 | $0.15 |
| Auto: MAI-Code-1.1-Flash | 0 | 2.07 | $0.02 | $0.02 |

## Mapping billing lines to pinned paths

- **gpt-5.5 ($296.82)** is the ONLY model pinned in all three sole
  routes: `.github/skills/{graph-authoring,judge-fr,review-pr}/adapters/
  graph.yaml` (`cli_flags.model: gpt-5.5`). The entire plan-judge-
  enforce-review governance spine is ~5% of spend.
- **claude-opus-4.6 ($287.55, 100% overage, 0 included)** is pinned in
  `.chaplain/graphs/watcher-enforce/validate-session.yaml` — the single
  most expensive pinned model, billed entirely at overage because the
  included pool was drained when it ran (contrast Opus 4.8: fully
  included, $0 overage — same class, opposite billing, pure timing).
- **claude-sonnet-4.6 ($0.46)** — `sanity-check-session.yaml`,
  `step-judge-v2.yaml`; **gpt-5.3-codex ($0.15)** —
  `enforce-session.yaml`, `step-plan-unified.yaml`. Chaplain
  plan/enforce nearly idle this period.
- **Claude Fable 5 ($4,041.85, 70% of gross)** and **GPT-5.6 Sol
  ($607.43)** appear in ZERO graphs, hooks, or adapters. They are the
  interactive sessions — the ungoverned surface.
- `claude-haiku-4-5` (fr_triage) and `mercury-2` (enforce-session) are
  direct-API providers — different invoice, not in this table.

**The insight: the governed paths are the cheap paths.** The reflex
reading of a $5.7k invoice is "the automation is expensive" — the record
says the opposite. Everything doctrine constrains (sole routes, chaplain
steps, pinned copilot nodes) sums to under 10% of spend; 83% of overage
flows through interactive sessions where no doctrine constrains model
choice. This is `is_this_a_graph` in billing form: work not routed
through a graph is billed at the ambient premium model. The invoice is
an audit of the question's firing rate — every Fable-5 dollar is a
moment where "is this a graph?" either wasn't asked or was answered no.

**The drift surface nobody bills to a diff:** unpinned copilot nodes
inherit the CLI's ambient default (`copilot_node.py` omits `--model`
when nothing resolves; the linter's `has_model_signal` check exists for
exactly this). A model-price change or CLI-default change alters cost
with no diff in the repo — configuration truth (Commandment 3) says the
model belongs in YAML, pinned.

**Concrete lever found:** repoint `validate-session.yaml` off Opus 4.6
(to gpt-5.5, matching the sole routes, or Sonnet-class) unless the
validate step demonstrably needs Opus-class reasoning — it zeroes the
largest pinned-path line.

**Heuristic:** *read the invoice as a coverage report.* Cost per model,
joined against `grep model: graphs/ hooks/ adapters/`, partitions spend
into governed (pinned, cheap, auditable) and ungoverned (ambient,
premium, invisible in git). The ratio is a dogfooding metric: it
measures how much work the doctrine actually routes through its own
machinery.

**Seed:** the billing table is a screenshot that vanishes; the mapping
above was manual. Could a periodic `scripts/` census join Copilot usage
(API or exported CSV) against the repo's pinned-model inventory and emit
the governed/ungoverned ratio — making `is_this_a_graph` observable as a
trend line instead of a post-hoc reflection?
