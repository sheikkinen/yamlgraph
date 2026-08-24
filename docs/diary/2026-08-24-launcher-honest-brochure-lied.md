# 2026-08-24 — The Launcher Was Honest; the Brochure Lied

FR-872 enforcement: a read-only attribution pass over nine surfaces of
the first real ramp install. The FR arrived pre-convinced that
`judge.sh` shipping without its adapter graph was "the one unambiguous
defect." The judge demoted that to a hypothesis (R-2), and the
investigation proved the demotion right: the script fails loudly and
instructively *exactly as curated* — `ramp/curation-diffs.md` had
already decided the adapter graph must be authored in-target. The
launcher was honest. What actually lied was the installed `SKILL.md`
bundle map, which asserts `adapters/README.md` exists with no hint it
must be authored — an instruction-without-bundle gap, two instances,
one class.

**Trap instance:** `quick_confidence` at FR-authoring time. The most
broken-looking surface (a script that cannot run) drew the
"unambiguous defect" label, while the actually-defective artifact (a
doc that reads fine) drew none. Brokenness visibility and defect
location are independent variables; the fail-loudly design *moved* the
honesty into the failure and left the lie in the prose. This is
`gate_checks_shape_not_substance` inverted: the runtime check was
substantive, the documentation was shape.

**What worked:** the judgement's primary+secondary disposition schema
dissolved the contested rows without a fight. "Deliberate AND
unfinished" (CI stub) and "deliberate AND defectively documented"
(judge.sh) both fit once cardinality stopped being forced to one.
Attribution disputes are often schema deficiencies, not evidence
deficiencies.

**Also:** seven of nine rows routed to FR-867 steps that were already
written down. The investigation mostly confirmed the ramp's own
remaining-steps list — which is the success case: the delta between
"looks incomplete" and "is attributed" was one table, 0.25 days, zero
fixes.

**Seed:** the AC-06 closure check treats path references in shipped
assets as claims to validate against the manifest. Is there a general
form — every install artifact that *names* a path is asserting a
contract, and `expects_authored:` is just the manifest learning to
distinguish "I ship it" from "you owe it"? Could the same field drive
the install transcript's TODO list, making the next ramp's gaps known
at install time rather than discovered by inspection?
