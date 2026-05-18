## 2026-05-18: FR-406/407/408 Judgment — Lint & Repair Proposals

**Context:** Judged three related FRs proposing structured output and repair capabilities for the `yamlgraph graph lint` command. FR-406 (--json flag) approved; FR-407 (structured repair actions) and FR-408 (runtime repair metadata) rejected.

**Insight:** The judgment session exposed the `framework_costume` trap clearly: FR-407 proposed an action registry with no consumer, and FR-408 layered metadata atop a pain better solved by documentation. Both passed the "sounds useful" test but failed "who calls this today?" — a one-question kill test that should precede any approval.

**Heuristic:**

> Before approving a capability FR, ask: "Name the callsite that would invoke this in the next 30 days." If no concrete caller exists, the FR is speculative infrastructure. Reject or defer.

**Seed:** Could the judgment step itself be a YAMLGraph graph — structured criteria as nodes, with a router that gates on the "name the callsite" heuristic before proceeding to scope analysis?
