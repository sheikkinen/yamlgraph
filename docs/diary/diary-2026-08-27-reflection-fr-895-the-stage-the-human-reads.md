# FR-895: The Stage the Human Reads

## Context

FR-892 shipped the census pipeline with the synthesis tail marked
"optional" — and my own authoring brief killed it at scope pressure. The
only stage whose output a human actually reads died first. FR-895 is the
resurrection, with the lesson mechanized: the brief inputs are REQUIRED
graph variables that fail loudly, so no future consumer can silently
drop the human output again (C-6).

## Traps encountered

- **value_marked_optional, second witness**: the cure was not "add the
  stage back" but "make its omission impossible" — required variables +
  preflight raise. An optional stage dies at the first scope squeeze; a
  required input survives because dropping it is now a visible breakage,
  not an invisible de-scope.
- **Gate stack as boundary inventory**: one GREEN commit bounced off
  five distinct gates in sequence (ruff-format, EOF fixer, prior-art
  marker, REQ collision, changelog-in-diff). Each bounce was correct;
  the lesson is the pre-commit dry run must extend beyond format checks
  to *registry* checks — a new REQ claim needs CAP file + ARCHITECTURE
  row + fragment alignment before the first commit attempt.
- **REQ reuse is a collision, not a convenience**: reusing FR-892's
  REQ-YG-624 for FR-895 work felt economical and was mechanically
  rejected (cross-FR wiring test). New behavior = new CAP-250/REQ-YG-625.
  The wiring test did exactly what the ID-allocation-race memory said
  gates should do.
- **Async terminals spawn in the main checkout** (third witness this
  arc): every background command needs an explicit cd sent INTO the
  terminal; the tool strips leading cd from the command line. The first
  census launch ran main's OLD wrapper for ~a minute before the kill —
  in a shared repo that class of mistake is how stale-code artifacts
  are born (one_session_one_repo).

## What worked

- The citation boundary as pure code (R-1/R-2): nine witnesses written
  RED before any module existed; the fail-closed contract (.REJECTED.md
  with deterministic summary head) fell out of the test names.
- The sole authoring route delivered the graph tail with its own repair
  log — including a sys.path fix I would have hit manually — and both
  smokes (success + loud preflight failure) recorded without my
  narration touching the artifact.
- AC-07 as a family check, not prose match: `top_finding_cited` compares
  label families by substring, inheriting the FR-893 canary lesson
  (vocabulary drifts; exact match undercounts).
- Reading the real brief before committing caught what no witness did:
  the model recommends graduating labels that are ALREADY doctrine
  (read_raw_output_first recommending itself for graduation is a fine
  irony). The boundary checks existence, not status — an honest,
  recorded limit, and a one-line future cross-check against the
  Scripture key set the aggregator already extracts.

## Seed:

The demo gate demanded a fresh demo-output.log for a diff that only
touched proofs — so I re-ran the demo purely to mint a stageable diff.
When a gate's satisfaction artifact is regenerable on demand and its
content is not examined, the gate measures willingness to re-run, not
truth. What is the substance check for run-evidence artifacts — a
git-SHA stamp inside the log (artifact_carries_code_identity), so the
gate can verify the log was produced by the code in the diff instead of
merely being newer than it?
