---
type: feat
scope: examples
---
- **FR-553 Turn-director prompt-salience witness**: Add `examples/dungeon_master/api/prompt_salience.py` -- a deterministic, visibility-not-gate harness that recomputes `running_scene` offline and tiktoken-counts the director's actual scene mass (correcting the premise that a turn's ~12.3k tokens was the director prompt; it is the 5-call turn-graph sum, dominated by the intent sub-calls), and cross-references each continuity break against whether its subject was present in the opening scene at the failing turn. On 10035-BC the director scene peaks at ~2k tokens (never 12k) and 2/2 continuity breaks were present-but-ignored (0 presence gaps), redirecting the continuity fix from prompt mass toward wording/recap. Wired into the continuity witness; no change to generation behavior.
