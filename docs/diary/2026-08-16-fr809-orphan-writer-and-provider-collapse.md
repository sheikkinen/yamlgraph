# 2026-08-16 — FR-809: the orphan writer and the provider that collapsed tier by tier

## What happened

FR-809 (orchestrator v2: recon + browser-sniff) was structurally done in
one authoring run — and then spent the whole afternoon dying in live
smokes, five times, for five different reasons. Every one of them was a
boundary defect outside the graph: an orphaned copilot child editing
governed files 30 minutes after its wrapper timed out; DeepSeek rejecting
`response_format`, then `tool_choice`, then just timing out; unbounded
`fetch_page` HTML overflowing anthropic's 200k context; and finally a
fixture that is constitutionally incapable of exercising the route the
acceptance criteria demanded of it.

## Traps met

- **Orphan writer (new trap, boundary: process).** The wrapper's timeout
  killed the wrapper, not the process group. The child kept authoring —
  out of brief, out of boundary, removing the mandated `parsed_key` and
  hardcoding target URLs. The witness suite caught it mechanically
  (`test_parsed_keys_exposed` went red on a tree I hadn't edited). An
  armed sentinel plus a live orphan equals an authorized intruder.
  FR candidate: kill the process GROUP on copilot timeout.
- **downstream_fix, nearly.** Three provider 400s in a row and I was
  building fallback tiers in framework code before asking
  `changelog_first_diagnostic`'s question: what changed? `.env:24
  PROVIDER=deepseek`. One grep would have saved two fallback tiers —
  though both tiers were condemned by real field failures and stay.
- **Spec premise vs frozen fixture (evaluation boundary).** AC-05 assumed
  the probe would miss the fixture's API so the sniff route would fire.
  But C-4 froze handler semantics that serve the API to plain curl at
  guessable paths — and the probe agent even reads the inline JS. Two
  GATEs, mutually unsatisfiable, discovered only by running. The judge
  validated each gate in isolation; nobody simulated their conjunction.
  Operator ruled: record BLOCKED-UNREACHABLE, don't bend either gate.

## Cures vindicated

- **read_raw_output_first, mechanized.** The single highest-leverage
  change of the day was making `_parse_output` quote the raw child
  output. Before: "output is not valid JSON" → orphan rips out
  parsed_key, invents an LLM normalizer. After: the provider 400 is
  quoted verbatim in the abort and every subsequent failure was
  root-caused in one read. The error message IS the raw-output gate.
- **Preflight paid for itself same-day.** FR-806's brief preflight warned
  that a 2-smoke brief would risk the 900s ceiling; run 1 hit exactly
  that ceiling.

## Heuristic

When two GATE conditions in one judgement each reference a frozen
artifact, simulate their conjunction against that artifact BEFORE
enforcement — a gate pair can be individually sound and jointly
unsatisfiable. (First occurrence; watch for recurrence.)

**Seed:** should the judge skeleton run a "gate conjunction" pass —
mechanically checking that every pair of GATEs citing the same frozen
artifact has at least one witness state satisfying both?
