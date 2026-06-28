---
type: feat
scope: examples
---
- **FR-561 DM v3 M2 -- causal trio hardened**: the floodmark plot model now hardens three causal
  classes. A pure, engine-free antecedent check (`validate._check_causal_antecedent`) flags the
  phantom-reversal class as `open_condition` -- a beat whose precondition has no authored producer
  and is not in the initial state. Capped reachability is enforced via a typed
  `PlotPlan.turn_budget` compiled as a unary counter (no numeric fluents; the pinned classical
  Fast Downward engine rejects `Int`), so a plan whose cumulative `cost_turns` exceeds the budget is
  proven unsolvable. A forced-window threat is proven unsolvable against the existing encoding (no
  `build_problem` change). The report gains a causal-health line (cumulative turns vs budget +
  open-condition list).
