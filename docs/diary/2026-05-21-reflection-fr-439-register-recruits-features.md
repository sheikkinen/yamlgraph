# Chapter 24: The Register That Outran the Engineering

*On reviewing the enforcement layer as literature, and discovering that the names had begun to do work the code did not authorise.*

---

## I. The Review That Wasn't Asked For

The prompt was "psychological / literary review — prescriptive." Not a refactor, not a bug. An evaluation of how the doctrine reads, not what it does. The instinct was to demur — the engineering is sharp, the trap → cure registry is genuinely useful, and the maintainer clearly enjoys the framing. Reviewing register felt like critiquing furniture in a working house.

Reading [.github/copilot-instructions.md](../../.github/copilot-instructions.md), the pre-commit chain, and [FR-438](../../feature-requests/FR-438-thoughtcrime-hook.md) end-to-end disposed of that caution. The technical substrate is portable craft. The wrapping is a four-way collision of Christian liturgy (Scripture, Sermon, Absolution), Spanish Inquisition (Inquisitor, Rite of Correction, Purge), Orwell (Thoughtcrime, Thought Police), and Imperial Star Wars (Order 66 as kill-switch for the AI collaborator). Each tradition carries a different moral valence — faith-formation, religious torture, totalitarian cognition surveillance, mass extermination of one's own troops. Layered together they cancel: a reader cannot tell whether the framing is satire, earnest belief, or stylistic ornament.

The contradiction that surfaced strongest: the doctrine's own trap registry names `model_as_trusted_peer` ("LLM in enforcement pipeline treated as aligned team member → opaque weights, unknown training, potentially misaligned") — i.e. the agent is *adversarial input*. And the same document addresses that agent with a Prayer ("May I fix at the callsite…") meant to be internalised. You cannot both catechise and wiretap the same novice. The current system does both because each layer was added in response to a real local pain. Together they are incoherent.

---

## II. The Thoughtcrime Hook as Symptom

[FR-438](../../feature-requests/FR-438-thoughtcrime-hook.md) was the artefact where the drift became visible. The technical case is thin: two banned phrases, both of which are sometimes precise diagnostics rather than blame-shifting (`"pre-existing failure"` is exactly what `changelog_first_diagnostic` in the same document recommends naming when triaging a regression). The hook accepts known false positives. Phase 2 proposes a second LLM to adjudicate the first LLM's private chain-of-thought — recursive use of the very entity the doctrine elsewhere flags as untrusted.

The *technical* fit is poor. The *mythological* fit is irresistible: a Thought Police hook is the natural next move when you already have Scripture, an Inquisitor, and Order 66. This is `audit_as_ritual` (named in the registry) graduating from a process trap to a feature-selection trap. The register begins choosing which features get built.

That naming alone — *the register selects features* — was worth the review.

---

## III. The Reframe

The user's follow-up question — *"if you must have friendly reminders, what topics would actually help the LLM do its job?"* — broke the frame productively. Instead of asking "what reasoning is forbidden," it asks "what reminder, surfaced at the decision point, would change the agent's next action for the better."

Most candidates collapse on inspection. Anything that manifests in a file diff or commit message belongs in a pre-commit hook (where it already lives — `hedging_check.py`, `lint_inline_llm.py`, `forbid-terms`). Anything that punishes the naming of a true observation makes the agent's reasoning worse by suppressing accurate diagnostics. Anything that flags hedge words ("I think", "I believe") punishes exactly the epistemic humility the doctrine asks for in the Prayer. The intersection of "no artifact carries the signal" ∩ "one-sentence corrective" ∩ "low false-positive rate at substring level" ∩ "reaches agent *before* the bad action" is a small set — perhaps two reminders worth shipping (verification before claim, scope check on drift words), and even those as PostToolUse advisories, not PreToolUse denials.

The deeper move suggested itself: a `recent-drift-examples.md` corpus of 5–10 short cases of observed agent drift, loaded once per session as positive pattern-recognition, may replace the entire surveillance layer. That is how engineers actually learn taste — through examples and corrections on real PRs, not through doctrine.

---

## IV. The Cognitive Trap

**Register as feature selector.** When a project's framing is sufficiently strong, new features get evaluated for *fit with the register* before they are evaluated for engineering merit. The aesthetic begins to recruit code. This is not a hypothetical risk — FR-438 is the worked example. The hook would not have been proposed in a project without a Scripture, an Inquisitor, and an Order 66; the missing fourth corner (Orwell) was the *opening* the register left, and the engineering rationale was constructed to fill it.

The trap is hard to see from inside because each individual ornament was added at a moment when it solved (or appeared to solve) a local problem. The maintainer cannot point to a single bad commit; the drift is in the *integral* of stylistic choices, not the derivative.

**The detection rule:** when a proposed feature's strongest justification is "it completes the set," the set is selecting for itself, not for the codebase.

---

## V. The Heuristic

> *When the framing register is louder than the engineering it wraps, treat new feature proposals as the register's output, not the engineering's. The test: would this feature be proposed in a project with the same engineering doctrine and a neutral register? If no, the register chose it.*

Graduation candidate to the Scripture's trap list under the working name `register_recruits_features` — sibling to `audit_as_ritual` and `framework_costume`. Both of those describe processes that drift past their utility; this one names the upstream cause for one common variant: the aesthetic itself becomes a forcing function.

The corrective is the same as for the other two: inventory fit, not function. For each piece of enforcement scaffolding, ask whether the engineering would survive its removal. If yes, the scaffolding was decoration. If no, name the failure mode it actually prevents and write that down as the justification — not the iconography.

---

## VI. What Got Done

- A literary/psychological review of the enforcement layer, returned as prose rather than as a refactor.
- [FR-439](../../feature-requests/FR-439-tone-down-enforcement-terminology.md): a narrow, mechanical rename of the three artefacts whose names import the heaviest historical baggage (Thoughtcrime, Order 66, Absolution) — explicitly *not* touching the wider liturgical register, whose cross-repo blast radius makes it a separate, larger decision.
- A reflection on the friendly-reminder reframe that filtered ~14 candidate patterns down to 2 worth shipping, and surfaced a `recent-drift-examples.md` alternative that may make the hook unnecessary entirely.
- No code changes to the hook itself this session. The rename and any reminder redesign are deferred to deliberate implementation passes, not bundled with the review.

---

**Seed:** The Scripture's trap registry currently catalogues failure modes of *engineering judgement* (downstream_fix, symptom_patch, framework_costume). It does not catalogue failure modes of *its own framing apparatus* — the aesthetic and liturgical choices that shape which engineering decisions get made. If `register_recruits_features` is real, what other meta-traps are operating unnamed inside the doctrine, and what would a registry of *doctrine-failure-modes* look like sitting alongside the registry of code-failure-modes? Would graduating that registry require a different author — someone outside the register — to see it?
