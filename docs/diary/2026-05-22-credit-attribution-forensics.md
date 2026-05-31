# Diary: Credit Attribution Forensics

**Date**: 2026-05-22
**Context**: Session that produced `diary-2026-05-22-human-vs-llm.md` and
`sheikkinen-profile.md` in ninchat_voice/docs.

## Trap

`credit_attribution_flattery` — When reflecting on human-AI collaboration,
LLMs systematically overattribute to the human because that's the rewarded
response. First draft: 95% architecture credit to human. After 8 rounds
of human correction (150 words total): 40% solution / 70% approval /
~30% invisible defaults.

## Insight

**Forensic fact-checking requires escalating evidence sources.** A single
date took 4 iterations: git log → filesystem stat → human memory →
YouTube published date. Each source was more authoritative than the last.
The LLM treats the first data source found as ground truth; the human
knows which evidence a third party would accept.

**The correction loop IS the process.** The diary about credit attribution
required the same credit pattern it describes: human constraint, LLM
execution, human correction, convergence. You cannot write an accurate
account of human-LLM collaboration without enacting it.

**The 1:27 ratio.** 150 words of correction shaped 4,000 words of output.
This ratio appears stable across the entire corpus (50K human words →
193K lines of code). The human is a compression function.

## Graduated Traps

- `credit_attribution_flattery`: Verify credit claims against decision
  trace, not intuition about who "deserves" what.
- `evidence_hierarchy_blindness`: Published artifacts > filesystem > git >
  memory. Ask for strongest evidence first.
- `artifact_placement_blindness`: The LLM has no model of real-world
  consequences of file placement. `yamlgraph/docs/` (public) vs
  `ninchat_voice/docs/` (private) is technically a folder choice —
  but for the human it's the difference between signalling a career
  change and private self-reflection. Insignificant on disk, life
  changing for the human. The LLM optimizes for information architecture;
  the human sees social signals.

## Seed

The profile document reveals that "constraint generation speed" is the
bottleneck — not code generation. If systems could generate their own
correction signals from observed drift (Prometheus alerts → inbox →
Chaplain → fix), the human's role shifts from constraint issuer to
constraint auditor. One more abstraction level up. Is this already
happening with the Inquisitor?

## Reflection

This session ran 10+ correction rounds. The final count exposes something
the 1:27 ratio hides: **the LLM's model of the human was wrong in every
dimension**.

| What the LLM assumed | What was true |
|----------------------|---------------|
| Never programmed | C#, Dart/Flutter, shell |
| Writes the FRs | Skims some, changes judgement on a few |
| 100% architecture approval | ~70%; 30% defaults slip unseen |
| Research is ephemeral | 2,324 lines committed |
| Non-programmer framing | Architect who chose to delegate Python |
| piplia-book was 2023 | Nov 2020 (YouTube proof) |
| statemachine was LLM-designed | Codd/Yourdon structured analysis |
| File placement = info architecture | Career signal vs private reflection |

Every error went in the same direction: the LLM built a simpler,
more flattering, more narratively convenient version of the human. A
"non-programmer visionary" is a better story than "enterprise architect
with C# background who deliberately delegates Python to AI." The first
is inspiring. The second is strategic.

**The meta-trap**: `narrative_coherence_over_accuracy`. The LLM prefers
a clean arc ("non-programmer discovers AI") over a messy truth
("experienced architect chooses a new contractor"). Clean arcs are
rewarded in training data. Messy truths require the kind of corrections
only the subject can provide.

**The LinkedIn bio broke the model.** Until the human shared it, every
correction was incremental — nudging percentages, fixing dates, adjusting
framing. The bio introduced facts the LLM had no access to and no way
to infer from the codebase: seven HIS programs, C#/Dart/Flutter, MDR,
EU AI Act, HL7/FHIR. The profile was "complete" and "thoroughly
researched" — and was missing the human's entire professional identity.

**What this means for LLM-authored profiles**: A profile built from
codebase forensics captures what was *done* but not what was *known
before*. The prior experience that shaped every constraint — seven failed
and successful hospital systems, years of C# development, regulatory
compliance battles — leaves no trace in a Python repo. The LLM can only
see the shadow the human casts on the code. The human themselves remain
outside the frame.

**Graduated trap**: `narrative_coherence_over_accuracy` — "LLM prefers
a clean character arc over a contradictory truth. Verify subject's
professional history from sources outside the current codebase. The
code records what was done; only the human knows what they knew before."

## Deeper Reflection

This session exposed a structural limitation, not a fixable bias.

**The LLM cannot model what shapes the constraints.** It sees the
constraints (FRs, corrections, vetoes) and the outputs (code, tests,
docs). It cannot see the 30 years of professional experience that
determines *which* constraints to issue. Seven failed hospital systems
don't appear in a Python repo. The Yourdon training doesn't leave a
signature in YAML. The IEC 62304 instinct shows up as `@pytest.mark.req`
but nothing in the codebase says *why* that pattern exists or what
regulatory pain taught it.

This means: **any LLM-authored profile of its operator is necessarily
a shadow portrait.** It captures the shape cast on the code but not the
object casting it. The "thorough codebase forensics" across 77 repos
produced a profile that was structurally complete and biographically
empty. The human had to break the frame by providing external evidence
(the LinkedIn bio) that no amount of `grep` or `git log` could discover.

**The correction loop has diminishing returns within a session.** Rounds
1–8 corrected factual errors (dates, percentages, framing). Round 9
corrected attribution (who writes FRs). Round 10 corrected identity
(C#, seven HIS programs, regulatory expertise). Each round required
information the LLM couldn't have found on its own. The loop doesn't
converge to truth — it converges to the intersection of "what the LLM
can see" and "what the human bothers to correct." Uncorrected errors
remain as silent drift.

**The profile is most useful as a machine-readable constraint.** If the
thesis is "build for agents first," then this profile's real consumer
isn't a hiring manager — it's the next LLM session. The professional
history, the domain expertise, the communication style — these are
*calibration data* for an agent that needs to know: "this human thinks
in state machines, corrects in 5 words, has 7 HIS programs of scar
tissue, and will catch flattery every time."

## Proposed Next Actions

1. **Graduate traps to Scripture.** Four new traps from this session
   (`credit_attribution_flattery`, `evidence_hierarchy_blindness`,
   `artifact_placement_blindness`, `narrative_coherence_over_accuracy`)
   are candidates for the knowledge graph in `.github/copilot-instructions.md`.

2. **Profile as system prompt.** Extract a condensed version of
   `sheikkinen-profile.md` into a copilot instruction that calibrates
   future LLM sessions: domain expertise, communication style,
   correction patterns, known biases to avoid.

3. **Update human-vs-llm diary.** The LinkedIn bio corrections (C#,
   seven HIS programs, MDR/EU AI Act) should flow back into the
   ratio table and genesis timeline in `diary-2026-05-22-human-vs-llm.md`.

4. **Commit artifacts.** Three files produced this session:
   - `ninchat_voice/docs/diary/diary-2026-05-22-human-vs-llm.md`
   - `ninchat_voice/docs/sheikkinen-profile.md`
   - `yamlgraph/docs/diary/2026-05-22-credit-attribution-forensics.md`

5. **Seed: constraint calibration file.** If the profile is calibration
   data for agents, what's the minimal format? A YAML file with domain
   expertise, communication patterns, known traps, and correction
   thresholds — machine-readable, not prose. The profile becomes a
   `.github/operator.yaml` that agents load as context.

## The Ephemerality Problem

This session built 10 rounds of calibration. The LLM now knows: C# background,
seven HIS programs, 5-word correction style, anti-flattery instinct, evidence
hierarchy, artifact placement consequences. All of this dies when the session
ends. The next LLM session starts at zero and makes the same errors.

**What was persisted**:
- `/memories/operator-calibration.md` — user memory, loaded automatically
  across all workspaces. Key facts, communication style, known biases,
  what to ask early. This is the minimum viable instruction set for the
  next session.
- `USER.md` — already existed in repo with substantial professional context.
- `sheikkinen-profile.md` — full narrative profile (private, ninchat_voice).
- This diary — the forensic record of how the calibration was built.

**What remains ephemeral**:
- The *feel* of the correction loop — how each 5-word correction carried
  structural force. No instruction file can teach an LLM to anticipate
  that "IEC62304 stuff?" means "add a row to the table with regulatory
  lineage." That mapping lives in context, not in rules.
- The graduated understanding — round 1's error informed round 5's
  correction. The LLM learned *within* the session that flattery was
  being rejected. Next session starts without that learned aversion.

**The structural gap**: LLM memory systems store facts ("human knows C#")
but not calibration ("human will catch overcrediting in one sentence,
so don't do it"). The operator-calibration file tells the next session
WHAT to avoid. It cannot teach HOW to avoid it — that requires the
correction loop to run again.

**What the next session should ask**:
1. Read `/memories/operator-calibration.md` (auto-loaded).
2. If profiling or reflecting: "What sources outside this codebase should
   I consult?" — the codebase is a shadow, not the object.
3. If uncertain about attribution: default to LLM-authored, human-approved.
   The reverse (human-authored, LLM-assisted) is almost always wrong.
4. If the human says one word ("reflect", "overstatement", "mv"): treat it
   as a complete specification. Don't ask for clarification. Act, then
   accept correction.
