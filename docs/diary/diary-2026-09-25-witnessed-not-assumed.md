# Diary 2026-09-25 — The sentence that said "witnessed, not assumed"

**Context:** FR-1065 investigation probes, run as FR-1076's R-1 evidence.

FR-1076 item 6 read: "Covered by the checkpointer: completed branch writes
are stored per task, so resuming the same thread does not re-run them.
Witnessed, not assumed (AC-6)." It was written before any witness existed.
The first `kill -9` probe re-ran all six finished branches. A `put_writes`
timestamp trace showed why: branches finished at 71–178 ms, their writes
landed together at 177–179 ms, when the step ended.

The phrase "witnessed, not assumed" was itself the assumption. It named the
test that would prove it, and naming the proof felt like having it. The
judgement caught the shape (R-5: "replace the If-RED escape with a required
passing witness") without knowing the answer; the probe supplied the answer.

Second trap, same session: the store variant reported the checkpoint db and
the side store at the identical byte count, 11,923,456. Identical sizes for
two different contents is an impossible result. It was flagged as "suspect"
and re-checked at 2k items; equal again; cause: both files were named
`store.db`. `one_session_one_repo`'s line applies at file scale: an
IMPOSSIBLE result proves a shared resource.

Third: the probe expected `GraphRecursionError` from a 20-batch loop under
the default limit. The default in langgraph 1.2.11 is 10,007. The test
asserted a limit nobody had checked.

**Heuristic:** a claim that cites its own future witness (`Witnessed (AC-6)`,
"covered by X") is a hypothesis wearing a citation. Before an FR sentence
names an engine guarantee, run the ten-line probe; the probe is cheaper than
the judgement round it saves.

**Seed:** could the FR hook flag engine-behavior sentences ("is stored
per", "does not re-run", "covered by the checkpointer") that cite an AC
instead of a committed test path, and ask for the test path?
