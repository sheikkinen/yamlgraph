# FR-1166: The setting written in the margin

**Date:** 2026-11-16
**FR:** FR-1166 (lint LLM settings written where yamlgraph never reads them)

## What happened

An operator report blamed race nodes for ignoring `thinking_budget`. That was
true of the pinned 0.5.25. It was false at HEAD, where FR-1144 had fixed it
weeks earlier. The thinking stayed on anyway, because every one of the 18
csap files that set the budget put it under `metadata:`, and yamlgraph reads
no setting from `metadata:`.

FR-1144's own text had named that migration in prose, and nothing moved. The
lint census then found the same mistake in our shipped examples: 14 prompts
across four graphs ask for a `temperature` in `metadata:` and run at the
0.7 default. `examples/beautify/prompts/analyze.yaml` asks for 0.4 and has
never received it.

## Trap: downstream_fix, author-side

The report described the symptom: Gemini is slow and Azure wins 95% of the
races. The natural fix was one more forwarding path in the race node. The
data had already been lost at the boundary where the author wrote it.
`metadata:` is a free-form map, so a wrong key there is silently accepted
instead of rejected. Fixing the race would have changed nothing: the race was
never sent the key.

## Heuristic

When a setting "doesn't work", first ask whether the place it was *written*
is read at all, before asking whether its consumer handles it. A free-form
map next to typed keys is a place where settings go to be ignored, and the
loader will never say so. The lint has to say it, by name and location.

The second lesson came from the census: run the new check on our own corpus
before celebrating it on the customer's. Our own examples had the defect
that prompted the FR.

**Seed:** `metadata:` is not the only free-form map next to typed keys
(`variables:`, tool `args:`, map `node:` bodies). Which of them silently
accept a typed key one level too deep? A census of every user-owned map ×
the typed keys of its sibling scope would find the next margin note before
an operator does.
