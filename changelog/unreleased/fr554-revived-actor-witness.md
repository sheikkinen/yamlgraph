---
type: feat
scope: examples
---
- **FR-554 Recap present-fact preservation**: Add `revived_actors` to the DM v2 continuity witness -- a deterministic, visibility-not-gate gauge that flags an exited character (declared in an earlier turn's `cast_exits`) narrated on stage again in a strictly-later recap, excluding possessive-only aftermath mentions (`Arnulf's fallen body`). On 10035-BC it reads 10 incidents (Ch8 Arnulf exited t5, on stage t6-t14 -- the "surges up once more" resurrection the reviewer flagged). Acts on the FR-553 present-but-ignored finding by hoisting the already-present "who is gone this chapter" fact from buried scene prose into salient standing constraints: a `GONE THIS CHAPTER` clause in `turn_recap.yaml` (the gone must not act) and a `revival` continuity class in `turn_direct.yaml`, plumbed via a new `gone_this_chapter` turn-graph variable. Salience, not prompt mass; no new graph, no new LLM call, no mutating gate.
