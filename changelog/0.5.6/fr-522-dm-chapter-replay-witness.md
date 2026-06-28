---
type: feat
scope: examples
---
- **FR-522 DM v2 scripted single-chapter replay witness**: Promoted the throwaway
  script that falsified FR-521's S1 into a first-class, tested witness. A continuity
  change can now be measured as a controlled experiment — re-play **one** chapter
  from its inherited start (every prior chapter held constant, the only changed
  variable the code under test) and compare its director-continuity flag count
  against the recorded baseline, instead of re-generating a whole confounded book.
  The doc-shape reset is one named, tested site
  (`turn_ops.reset_chapter_for_replay`); the impure LLM-driving loop lives in a new
  `api/chapter_replay.py` (deep-copies the doc so the caller's is never mutated, and
  is mockable so a test proves a prior chapter stays byte-identical); the
  deterministic measurement lives in `witness_metrics.chapter_actor_flag_metrics`
  and reports the **director-flag** count beside the **intent-map acting** count per
  turn — so a change that injects text into the scene (which `running_scene` feeds
  to all three turn nodes) cannot inflate the flag count without the independent
  acting count exposing it (FR-521's metric-pollution lesson). Witness instrument,
  not a gate — never wired into CI; measurement is unit-tested, live replay is run
  by hand.
