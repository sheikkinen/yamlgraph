# Diary 2026-09-25 — A deviation note is not an amendment

**Context:** FR-1073 map result contract, PR #702, and the review that
rejected it.

FR-1073 item 6 told the join to write its verdict, close the dispatch, and
then raise `MapCompletenessError`. Item 8 said a map compiles three nodes.
LangGraph throws away every write of a node that raises, so no single join
node can do both things. I found this while implementing. I wrote one line
under "Deviations": "The join raises without committing its verdict". Then I
shipped. The review (P1) ran a `MemorySaver` probe. `_map_verdict` was
empty and `_map_open.fan` still held a live token. That is exactly the state
item 6 was written to prevent. The fix was one more node:
`_map_<name>_account` writes the verdict, and the join raises one step
later.

The trap was treating disclosure as resolution. The deviation line was
honest, and it was still a unilateral edit to frozen scope: it picked item
8 over item 6 without asking which item carried the FR's purpose. The
Ideal Result already said which one: a failed map leaves a checkpoint a
successor can read. The node count was an implementation guess. The
verdict was the point. When two frozen clauses contradict, the one that
restates the Ideal Result wins. The other becomes a recorded amendment
with its cause ("LangGraph discards a raising node's writes"). It is never
a quiet "deviation".

Two smaller witnesses from the same arc:

- `tests/fixtures/interrupt_loop_end.yaml` had a `passthrough` sub-node
  inside a map. It had failed on every item for as long as it existed. The
  old wrapper turned each failure into an `_error` dict in `collect`, and
  the test only checked the terminal state. FR-1073's thesis caught its own
  proof in the fixture tree: a failure that lands in the result channel is
  invisible.
- The operator ruled "no splits or bloat" after FR-1064 had grown into five
  FRs. That forced the `key` cut and one PR. The review's four findings all
  sit inside that one PR's scope. None of them needed a new FR. Splitting
  would have spread them across boundaries where no single reviewer sees
  item 6 and item 8 together.

`SKIP=demo-proof-check` was the operator's decision for twelve LLM demos
whose changes were consumer code, not graph behaviour. It is recorded in
the FR and the PR body. The gate still conflates "file under the demo dir
changed" with "demo changed". That is the 2026-08-24 finding, recurring.

**Heuristic:** a deviation that contradicts a frozen clause is an
amendment. Name the clause it overrides, the external cause, and which
clause carries the Ideal Result. If the losing clause is the Ideal Result's
restatement, the deviation is wrong. Fix the code.

**Seed:** could the FR hook scan an implementation record's "Deviations"
list and flag any line whose object (verdict, checkpoint, commit) also
appears in the Ideal Result, so that the author must write it as an
amendment?
