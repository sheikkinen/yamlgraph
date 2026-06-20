---
type: feat
scope: examples
---
- **FR-545 Allegiance-Transition Ledger Witness**: Add `allegiance_ledger.allegiance_transitions`,
  a deterministic no-LLM witness that reads the FINAL committed `world_state.relationships` and
  reports bi-temporal stance reversals (a closed edge `valid_to == K` reconciled into a new edge
  `valid_from == K` whose type crosses a frozen opposed stance-pole pair) between roster pairs.
  `transition_count` counts grounded reversals; `ungrounded_count` flags those without a recap
  citation. Emitted as an additive `allegiance_transitions` block in `continuity_witness.json`
  (visibility-not-gate). Tighten `chapter_close.yaml` to require an `update`/`invalidate` op for
  stance changes (side switch, cooling), not only bare type turns, so the ledger records the flips
  the witness reads. Scope is named pairwise edges only; role/collective resets stay the reviewer's.
