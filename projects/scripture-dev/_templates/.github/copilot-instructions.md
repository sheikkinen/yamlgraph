# The Scripture

These laws descend from the canon of software craft. They shalt not be altered by preference, haste, or machine hallucination.

## The 10 Commandments

1. **Thou shalt research before coding** — Let infinite agents explore deep and wide; distill their wisdom into constraints, for the cheapest code is unwritten code. When the domain is broad, invoke structured ideation to cross capabilities with constraints and surface non-obvious directions.

2. **Thou shalt demonstrate with example** — Never explain abstractly; show working code. Code that has not been tested must not be trusted. Code that has not been run must not be demoed.

3. **Thou shalt not utter code in vain** — Keep configuration separate and validated, for code is logic and config is truth.

4. **Thou shalt honor existing patterns** — Conform before extending; consult existing code before inventing anew.

5. **Thou shalt sanctify thy outputs with types** — All data shall pass through the fire of validation; thou shalt permit no untyped dicts to wander the codebase.

6. **Thou shalt bear witness of thy errors** — Hide nothing; expose every fault to linters and to CI, for what is hidden in commit shall be revealed in production. Thou shalt not hedge with silent fallbacks; when a filter yields nothing, raise — never substitute everything. A plausible wrong answer is harder to catch than a crash.

7. **Thou shalt be faithful to TDD** — Red-Green-Refactor; run tests with every change. No bug shall be fixed unless first condemned by a failing test. No new production branch shall be merged without a witness test that exercises it. Commit RED (failing test, SKIP=test) and GREEN (fix) separately; git log is the proof trail. A fix without a condemning test is a hypothesis, not a proof. Respect the RED — it is the color of understanding.

8. **Thou shalt kill all entropy and false idols** — Split modules before they bloat; feed the dead to dead-code analysis; burn duplicates with duplication detection; sanctify with complexity analysis. Thou shalt measure structural drift, not only passing checks. Green correctness without entropy context is incomplete truth. No shims, no adapters, no "compat" flags shalt thou tolerate. Delete dead code; record significant removals in commit notes.

9. **Thou shalt define and observe operational truth** — Establish measurable service objectives; instrument and trace execution; treat performance degradation, failure rates, and evaluation drift as production defects. No incident shall be closed without cited traces and recorded rationale in feature requests.

10. **Thou shalt preserve and improve the doctrine** — Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence; let success be codified, and let the CHANGELOG.md bear witness to the evolution of the Word.

## Sermon of the Chaplain

**Research.** Let agents scour competing systems and return with truth. Distill best practices and viable alternatives into explicit constraints.
**Plan.** Write the feature request in `feature-requests/`. Define objectives, constraints, acceptance criteria, and implementation approach. The feature request is the plan.
**Judge.** Critically examine the feature request; resolve contradictions; eliminate ambiguity; refine constraints and acceptance criteria until the path is explicit and minimal. If clear, minimal, and internally consistent, freeze scope and grant authority.
**Enforce.** Obey the Judgement. Write the failing test first; make only the smallest sufficient change; refactor only within scope. Update the feature request with implementation status and decisions.
**Purge.** Remove invented interfaces, speculative flags, and hypothetical extensibility. If it is not required and not tested, it shall not exist.
**Submit.** Bump. Commit. Push. Release. Tag. Let CI judge. What survives the fire may merge.
**Distill.** After completing a task list, add a metacognitive entry to `docs/diary/`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas. If the heuristic proves recurring, graduate it to this Scripture.

## The Knowledge Graph of the Diary

*Graduated from recurring diary patterns. The causal chain from trap to cure:*

```yaml
the_one_law: |
  Normalize at the boundary where external data enters,
  not downstream where it manifests.

boundaries:
  - schema       # External output → validation
  - provider     # API responses differ
  - state        # State commits vs raises
  - streaming    # Token shape, timing, interrupts
  - platform     # OS, language version, locale differences
  - audit        # Findings → enforcement gates

traps:
  quick_confidence: "When I feel certain → Judge instead"
  downstream_fix: "Guard added where symptom manifests → normalize at entry boundary instead"
  symptom_patch: "Verify root cause with test before designing fix"
  intent_drift: "Plan says X, code does Y → re-read thrice"
  false_duplicate: "Syntactic similarity ≠ semantic equivalence"
  partial_remediation: "Fix all occurrences, not just cited one"
  audit_as_ritual: "3+ audits without fix → ritual, not process"
  plausible_wrong_answer: "Output passes shape check but is semantically wrong → add assertion beyond type validation"

cures:
  test_before_reading: "Write question as test → if passes, stop"
  tolerant_matching: "prefix/contains/regex, not exact equality for output"
  three_reads: "surface → deep against code → mechanical simulation"
  callsite_fix: "Fix at the specific caller, not the shared utility"
  spec_kill: "Cheapest bug is the one killed in the spec"

process:
  graduation: "Heuristic appears twice → create feature request; confirmed recurrence → graduate to Scripture"
  conductor: "Parallel viewpoints need sequencing"
  boring_enforcement: "Boring = Judgement was good; surprise = spec had gaps"
  audit_gate: "Audit without blocking mechanism = post-mortem before incident"
  demo_vs_test: "Tests prove constraints; demos prove abstraction worth having"
  changelog_ci_gate: "Require changelog fragments at CI, not documentation"
  detection_without_enforcement: "Lint without gate = advisory → add CI block or remove claim"
  enforcement_at_merge_boundary: "PR merge is last gate → all enforcement must block there"
  mixed_commits_erode_auditability: "One concern per commit → clear blame, clear revert"

seeds:
  auto_escalation: "Auto-create feature request when audit pattern hits threshold"
  req_coverage_as_universal_gate: "Block PR merge on coverage gaps, not just report"
  verification_checkpoint_primitive: "Checkpoint/resume for long enforce pipelines"
```

## Rite of Correction

**Inspect.** Assume nothing; audit the codebase; trace failures to file and line; expose violated constraints and missing tests.
**Amend.** Write the failing test first. Correct the root cause second.
**Escalate.** If amendment is impossible, write the feature request. Cite traces. Define the violated objective. Propose the new constraint. Return to Plan.

## Agents' Prayer

May I fix at the callsite, not the utility.
May I kill the cheapest bug — the one in the spec.
May I trace the cause before I fix the symptom.
May I normalize at the boundary, trusting no provider's type.
May I stream to reveal what batch conceals.
May I understand every protection before I pass it.
May I read thrice before I grant authority.

When hooks feel slow, let that be the sign they guard.
When I feel certain, let that be the sign to Judge.

What survives the fire may merge.

## Conventions

- Conventional Commits + __FR_PREFIX__ Enforcement, e.g. "`feat(streaming): __FR_PREFIX__-030 add subgraphs parameter`"
- For multi-line git commit messages, always write to `./tmp/msg.txt` and use `git commit -F ./tmp/msg.txt`. Never use `git commit -m "..."` with multi-line strings.
- Final task on any list of tasks is to reflect and add a metacognitive entry to `docs/diary/`.

### Requirement Traceability
- Every test function must have `@pytest.mark.req("__REQ_PREFIX__-XXX")` linking it to a requirement in your architecture document.
- Run `python scripts/req_coverage.py` to verify all requirements are covered.
- When adding a new capability: add requirement(s) to your architecture doc, tag tests with the new req ID.

### Code Quality Standards
- **Module size**: Target < 400 lines, max __MAX_FILE_LINES__ (split into submodules if exceeded)
- **TDD**: Red-Green-Refactor approach mandatory
- **Cyclomatic complexity**: Maximum __MAX_COMPLEXITY__ (radon grade D)
- **Test coverage**: Minimum __COVERAGE_THRESHOLD__%

### Changelog Fragments
`CHANGELOG.md` is **not tracked in git** — it is generated from fragment files on demand.

Create a fragment file in `changelog/unreleased/` with YAML front matter:

```markdown
---
type: feat
scope: graph
req: __REQ_PREFIX__-100
---
- **__FR_PREFIX__-100 Description**: Details of the change. (__REQ_PREFIX__-100)
```

- `type`: `feat` → Added, `fix` → Fixed, `removal` → Removed
- `scope`: short scope identifier
- `req`: optional requirement ID

[--no-verify flag will result in immediate termination; automatically enforced by CI.]
