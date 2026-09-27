# Diary 2026-09-27 — The threshold that counted the wrong crowd

**FR:** FR-1116 (supersedes FR-1076) · **Arc:** analysis → leaner FR → advisory judge → enforce

## What happened

FR-1076 set out to make map runs resumable. Across one revision it grew
into a store with memberships, publication and reads, and it replaced
FR-1073's result shapes. Put next to `meta_map`, the only real consumer,
most of that machinery had no caller. The replacement is two tools, split
and merge, with one SQLite table keyed by path.

The design problem was one line of arithmetic. A map's `min_success`
counts only the items it dispatched. Once a memo removes the items that
were already done, a run over two changed files is judged on two items,
not thirty. So the map declares `min_success: 0`, and merge applies the
real threshold after commit, over the whole current population. That
costs one visible opt-in per consumer. The alternative was a
compiler change, and there is only one consumer.

Two smaller findings came from the gates, not from design:

- `req_coverage.py` reads function and class decorators only. A
  module-level `pytestmark = pytest.mark.req(...)` looks tagged to a
  reader and is invisible to the scanner. The RED commit failed on this.
- FR-756 requires `pytest.mark.process` on any unit module that touches
  `examples/`. The collection error said so plainly. It fired before any
  test ran.

## Trap

**Threshold over the filtered population.** Any filter placed in front
of an aggregate gate changes what the gate means. The gate still passes
its own tests, because it is still correct for the items it sees.

## Heuristic

When a step removes items before a gate that counts them, move the gate
to the point where the whole population is back together. Or state in
the FR which population the gate judges.

**Seed:** The census (`person_profile_census`) is the named second
consumer. When it adopts the memo, will its `max_items: 500` cap need the
same move, since a cap over `todo` also judges the filtered crowd?
