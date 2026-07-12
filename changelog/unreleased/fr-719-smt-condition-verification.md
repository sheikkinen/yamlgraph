---
type: feat
scope: linter
req: REQ-YG-545
---
- **FR-719 SMT-Backed Condition Verification (W803–W805)**: the linter now proves three properties per expression-edge guard group using Z3 — no gap (W803, with a concrete counterexample state: numeric interval hole or `<missing>` variable), no overlap (W804, witness model + edge indices), no shadowed guard (W805). The encoding is faithful to the runtime's None semantics per operator (`==`/`!=` are None-exempt; ordering comparisons are None→False) and is witnessed by replaying every counterexample through `evaluate_condition`. `z3-solver` ships as the optional `verify` extra; without it the family emits one skip notice. First sweep found real gaps in 8 shipped example graphs, including the flagship reflexion pattern (`critique.score` unset → silent END). (REQ-YG-545)
