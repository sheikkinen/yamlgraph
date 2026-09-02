# The Host That Could Not See RED

*2026-09-02 — FR-954, faithful no-fork import simulation*

## The shape of the day

The whole change was one subprocess string. The FR-950 witness that
proves `import yamlgraph` survives a runtime without fork hooks deleted
`os.register_at_fork` and left `os.fork` in place — a surface no real
platform has — and PR #555 had made it green by pre-importing the
dependency chain before the deletion. The repair was to import only
`os`, delete both attributes, assert both are gone, and then let the
ordinary cold import chain run. The judgement had already frozen every
line of that; enforcement was boring, which is what a good judgement
buys.

The instructive part was RED.

## Trap: the host under test is the surface being simulated

Doctrine says commit RED first and keep the failing output as the proof
trail (C-4). RED here is "assert `os.fork` is absent after the
one-attribute setup", which fails on any fork-capable interpreter. I ran
it on this machine — Windows — and it passed. Of course it passed:
Windows *is* the no-fork surface. The assertion the simulation was
missing is trivially true on the host the simulation imitates. The RED
is only visible from a host that has the property being faked away.

So the proof trail has a hole shaped exactly like the platform gap the
FR exists to close. WSL is broken on this machine, the Docker daemon is
down, and the repo's LAN delegation route runs mac to Windows, not the
other way. I could not produce the failing output. I recorded that in
the RED commit message and in the FR rather than pretending, and left
AC-03 (CPython 3.14) and the RED witness as owed by the mac.

**Heuristic:** a simulation witness has two hosts — the one it imitates
and the one that can see it fail. Before committing RED, ask which one
you are on. If you are on the imitated host, the RED is invisible and
must be named as owed, not claimed. Corollary: a RED commit message
should say *where* it fails, because "fails today" is host-relative for
capability simulations.

## Insight: green-by-narrowing

PR #555 turned the suite green by importing the dependency chain
*before* the deletion. That is a legitimate move for unblocking a
suite, but it changes what the test proves: yamlgraph's own guard,
not the chain's behaviour under the absent capability. The test's name
and docstring kept the larger claim. Nobody lied; the seam simply moved
and the label did not. Watch for fixes that make a witness green by
importing less, mocking earlier, or pre-warming state — each one may be
shrinking the phenomenon the witness was named for. The `mock_escape_hatch`
entry already covers mocks; the pre-import scaffold is the same trap
without the word "mock" in it.

## Small trap, mechanical

Two attempts to patch the test via a bash heredoc silently matched
nothing: the `\n` sequences inside the Python string literals did not
survive the transit. The bytes on disk were right; the tool path was
wrong. Twenty minutes of certainty that the file was odd, when the
mismatch was in the pipe. When a matcher fails against text you have
just seen, suspect the transport before the target — and switch tools
instead of trying a third variant of the same one.

**Seed:** should capability-simulation witnesses declare the host
property they need in order to fail — a marker like
`requires_host_capability("os.fork")` that turns a trivially-true RED
into a recorded "unwitnessable here" instead of a silent pass — so the
proof trail carries the gap explicitly rather than depending on the
enforcer noticing which host they are standing on?
