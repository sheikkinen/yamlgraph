---
type: fix
scope: demos
---
- **FR-1087 safety-guards demo compiles again**: the low-score edge from `review` now targets `revise` only instead of the conditioned fan-out list `[revise, expand]`, which the compiler has rejected since FR-718. A deterministic test drives review scores 0.3 then 0.9 and pins the node order `draft, review, revise, review, expand`. The README no longer promises a clean lint; it names the W803 warning the optional z3 check reports.
