# CMM Assessment of the Feature-Request Process

YAMLGraph's feature-request process is best rated:

> **CMM Level 3 Defined, with partial Level 4 and Level 5 practices.**

This is an informal assessment, not a formal CMMI appraisal.

## Level-by-level assessment

- **Level 1 Initial:** exceeded. Work is not purely ad hoc; changes have named
  artifacts, gates, tests, CI, and traceability.
- **Level 2 Managed / Repeatable:** satisfied. The repeated loop is clear:
  proposal -> FR -> judgement -> implementation -> gates -> diary.
- **Level 3 Defined:** satisfied. The process is documented and standardized
  through the Scripture, FR template, development docs, Chaplain pipeline,
  hooks, CI, and CAP/REQ registry.
- **Level 4 Quantitatively Managed:** partial. YAMLGraph has useful metrics and
  gates--coverage, requirement coverage, CI status, changelog gates,
  file-size/complexity gates, and pipeline states--but process control is not
  yet statistically managed across lead time, rejection rates, defect escape
  rates, or remediation loops.
- **Level 5 Optimizing:** partial. Diary -> doctrine -> gates is a real
  improvement loop, with Inquisitor and Philosopher feedback. The limitation is
  unevenness: some lessons become mechanical gates, while others remain prose
  and human judgement.

## Main maturity risk

The main maturity risk is **execution split**. The formal Chaplain path is
highly staged, but `docs/development-process.md` records that most changes still
arrive through the manual loop. The process remains mature only if both paths
obey the same doctrine and gates.

## Path to stronger Level 4/5 maturity

To strengthen Level 4/5 maturity, track and act on:

- FR lead time from proposal to merge;
- judgement amend, reject, and split rates;
- validation remediation count per FR;
- CI failure classes by gate;
- escaped defects traced to missing acceptance criteria;
- diary-to-doctrine graduation latency;
- manual-loop versus Chaplain-loop throughput and defect rates.

The maturity step is not collecting these numbers. The maturity step is using
them to change the process.
