# 2026-08-15 — FR-789: the brief is code, and it shipped a bug

**FR:** FR-789 (browser-sniff step) — second of the three remaining API
discovery steps.

## The route failed exactly as designed, and the failure was mine

Run 1 of the authoring adapter died at the contract gate: exit 65,
`draft-authoring-report.md missing`. The artifacts were fine — the
adapter had authored, linted, and even proven the CAPTCHA path. What
killed it was *my brief*: I specified `python3 -m http.server` as the
smoke fixture server, but the FR-784 SPA fixture's `/api/*` fetches need
a dynamic handler (the tests' `_SpaHandler` returns JSON for those
routes). Static serving 404'd them; nothing classified as `data`; the
adapter burned its budget investigating a "failure" in artifacts that
were correct, and timed out before writing the report.

The trap has a name in the Scripture — `composition_bug` — but the
instance is new: **the task brief is itself a component of the pipeline,
and it carries defects like any other**. The adapter did everything
right, including the diagnosis (its narrative correctly identified the
static-server 404 as the cause). The report gate then did ITS job:
refused to bless an unproven run. Doctrine held at both ends; the defect
sat in the connecting artifact I wrote free-hand, unreviewed, in thirty
seconds.

## The cure was boundary-shaped

Fix: `tmp/fr789_fixture_server.py` mirroring the FR-784 handler, and a
brief edit marking the run as resumed. Run 2 validated the unchanged
artifacts end-to-end and wrote the report. Note what did NOT happen: I
did not author manually around the failed route (the standing
temptation), and the adapter did not recreate working artifacts — the
resumed-run instruction made idempotence explicit.

Heuristic (first strike, watching for recurrence): **when a brief names
a validation command, dry-run that command's premise before launching
the route** — one `curl http://127.0.0.1:8931/api/data` against the
static server would have exposed the 404 for the cost of one line.
The brief's validation section deserves the same `spec_kill` scrutiny
as an FR's acceptance criteria, because that is what it is.

**Seed:** authoring briefs are now a recurring artifact class
(fr-787, fr-789, fr-795, fr-796...) with a recurring defect class
(unverified validation premises). Should the graph-authoring skill grow
a brief template with a mandatory "validation premises verified by"
line — or is that gate theatre until the second strike?
