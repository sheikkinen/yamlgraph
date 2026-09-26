# Diary 2026-09-26 — The cap that seven graphs set and none received

**Context:** FR-939 enforcement. Map nodes now take a typed
`on_overflow: error | truncate` (default `error`), and
`config.max_map_items` now reaches the map compiler.

The policy change was small: one `Literal` field, one validator, one
`raise` in `resolve_items`. The propagation repair the judge found took
more thought. `GraphConfig` parsed `config.max_map_items` at load, and
`compile_map_node` read the cap from `defaults.max_map_items`. Nothing
connected the two. The FR-027 unit test passed
`defaults={"max_map_items": 5}` straight into `compile_map_node`, so it
exercised the consumer's read and never the loader-to-consumer plumbing.
Every check was green and the documented key did nothing.

The grep for callers showed what that meant in practice. Seven demo
graphs (`corpus_census`, `repo_census`, `req_witness_audit`,
`person_profile_census` twice, `cap_journey_census`, `philosopher_book`)
declare `config.max_map_items` between 50 and 1000. Every one of them has
been running with a cap of 100 and a log-only warning. The census graphs
exist to count a whole corpus, so a silent prefix is exactly the
plausible wrong answer Commandment 6 forbids.

Two smaller observations:

- `node_schema.py` sat at 397 lines against FR-716's `< 400` split gate,
  and `node_compiler.py` at 446 against the 450 file cap. The new field is
  one line and the propagation two, so no gate was touched. Several
  schema modules are now close enough to their gates that the next field
  forces a split.
- The GREEN commit's pytest hook failed once on
  `test_fr995_outsider_wrapper.py::test_input_mode_writes_placeholder_report_and_no_observation`,
  and it passed in isolation. The test asserts that the *system* temp
  directory holds no `outsider-*/input.md`. Any concurrent run of the
  same wrapper, such as a sibling worktree's hook, satisfies that glob.
  It is test pollution through a shared global directory, and its fix
  (point `TMPDIR` at `tmp_path` in `_run`) belongs to FR-995's owner, not
  to this diff.

**Heuristic:** a unit test that injects a config value where the
consumer reads it proves the consumer, not the plumbing. Every graph-level
config key needs one witness that goes through `load_graph_config` →
`compile_graph` and observes the effect; without it, "parsed" and
"honoured" can drift apart with every check still green.

**Seed:** how many other `GraphConfig` fields are parsed at load and
never observed through load→compile? The corpus is finite and
enumerable (every attribute set in `GraphConfig.__init__` × its
consumers). That makes it a corpus-map-reduce census, not a manual audit.
A second question: did any committed census output under
`examples/demos/*/proofs/` come from a run whose `over` list was longer
than 100 and was silently truncated?
