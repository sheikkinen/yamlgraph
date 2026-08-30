# The Generator Nobody Fed

*FR-912 — retiring `yamlgraph skill export`, 2026-08-30*

## What happened

`yamlgraph skill export` shipped in FR-348 and grew agent-md/cursor formats in
FR-350/FR-351. Four months later it had produced exactly zero committed
artifacts. Every file under `.github/skills/**` is hand-authored — including
`graph-authoring/SKILL.md`, the flagship skill that governs how *all* graphs in
this repo get written. Somebody sat down and wrote that by hand while a
generator for exactly that artifact class sat in the CLI, one command away.

That is `builders_never_call` in its purest form: not a tool that was tried and
found wanting, but a tool never once reached for by the people who built it.
The absence is louder than a bug report. A generator whose own authors route
around it is not underdocumented — it is unwanted.

## The trap I nearly walked into

Deleting a surface reveals what was leaning on it. Vulture immediately flagged
`NodeConfig.output_schema` as unused: the exporter's schema-derivation walk was
its last Python reader. The reflex is to keep pulling the thread — the field is
dead, delete the field. But `output_schema:` is a live graph-YAML key with
`extra: "forbid"` behind it; deleting the Pydantic field would break every graph
that declares an inline schema. The "dead code" signal was measuring Python
readers, not config surface.

**Vulture measures Python reachability, not contract surface.** For a
declarative framework those are different sets, and the gap is exactly where
config fields live. The whitelist entry beside `NodeConfig.schema_ref` was
already there for the same reason — precedent I only noticed after I had
started drafting the deletion.

## The boundary that bit

The witness test asserted `ModuleNotFoundError` on `yamlgraph.export`. It
failed — in a worktree that has no `yamlgraph/export/` directory at all.

The editable install is shared across worktrees. Its path finder resolved
`yamlgraph` to the worktree and `yamlgraph.export` to the *main checkout's*
copy. Both statements true simultaneously. The assertion was measuring the
developer's filesystem layout, not the retirement.

This is `one_session_one_repo` wearing a new costume. The known form is the
shared git index; this is the shared **import path**. Any test that asserts
absence-by-import is environment-scoped in a multi-worktree repo. The honest
form asserts on `find_spec(...).origin` relative to the checkout under test —
which still catches the thing FR-924 worried about (build residue inside the
repo) while ignoring a sibling checkout that has every right to exist.

Cure candidate: **absence assertions must name their universe.** "Not
importable" is not a fact about the code; "not resolvable within this checkout"
is.

## The retirement dividend

Because FR-910 had already taken `export/mcp.py`, `yamlgraph/export/` retired
with its last member — and two `.importlinter` contracts (`export-seam`,
`compile-seam`) retired with it, the latter because its only forbidden module
was the package now gone. A deletion FR that removes enforcement machinery
usually smells like a bypass. Here it is the opposite: the contracts were
guarding a boundary that no longer has two sides. Keeping them would have been
the compliance theatre.

Net: one CLI group, four modules, three test files, one reference doc, two
import contracts, two capabilities — subtracted. Nothing added but a witness.

**Seed:** The skill exporter died of never being called. What *else* in this
repo has a zero-artifact production record? We track test coverage and REQ
coverage — both measure whether code is *exercised*. Nothing measures whether a
shipped surface has ever produced a committed artifact. Could `git log` +
capability registry be crossed into a "surface liveness" report: for every CAP
claiming an output-producing capability, the last commit whose diff plausibly
came from it? Capabilities that have never once appeared in the history are
candidates for the same fate as CAP-142 — and unlike coverage, that metric
would go *down* over time, which is the direction a mature system should move.
