## FR-1123 — the test that knew the wrong stream

The RED commit for AC-10 asserted the compile error lands on stderr,
because the AC said so. GREEN produced the right error on stdout: the
CLI routes errors to stderr only in `--json` mode. The test was written
from the AC's wording, not from the code it would run against, so the
RED was red for two reasons, and only one of them was the missing
feature.

A second instance of the same shape: the judgement placed the shared
provider resolver in `llm_factory`, a module the linter is contractually
forbidden to import. The judge read the FR; the import-linter contract
was not in its input closure.

Heuristic: a RED test proves the feature is missing only if every other
assumption in it is already true. Before committing RED, run it once
against the nearest existing path (here: any CLI error) and check that
it fails *only* on the new behaviour.

The parity oracle earned its place: the hand walker agreed with the
private SDK transform across every committed prompt on the first run,
including the nine offenders, which is the evidence that "mirror the
SDK" was implemented rather than approximated.

**Seed:** should the judge's input closure include `.importlinter`, so
that module-placement decisions in a judgement are checked against the
contracts that will reject them?
