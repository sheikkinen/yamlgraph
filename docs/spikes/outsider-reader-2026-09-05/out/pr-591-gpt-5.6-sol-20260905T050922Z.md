<!-- outsider spike | input: inputs/pr-591.md | model: gpt-5.6-sol | 2026-09-05T05:10:17.373096+00:00 -->

## 1. In my own words

This change instruments and pilots something called the FR-990 CAP journey census, commits raw pilot rows, modifies code and a prompt in response to those runs, and splits `render.py` to keep `tools.py` below a size limit; the intended users or beneficiaries are not stated.

## 2. Could I decide whether to merge this from the description alone?

NO

The description relies on undefined project terminology and prior documents while leaving the intended behavior, unresolved failure rate, acceptance criteria, and concrete test evidence unstated.

## 3. Things I do not understand

1. **Quote:** “census”
   **Type:** `undefined term`
   **Question:** What is the `census` component or subsystem in this project?

2. **Quote:** “FR-990”
   **Type:** `unexplained identifier`
   **Question:** What is FR-990, and where can a reviewer read its requirements and acceptance criteria?

3. **Quote:** “CAP”
   **Type:** `undefined term`
   **Question:** What does CAP mean in this project?

4. **Quote:** “CAP journey census”
   **Type:** `undefined term`
   **Question:** What is being counted or evaluated, and what constitutes a CAP journey?

5. **Quote:** “instrument + pilot”
   **Type:** `mechanism without purpose`
   **Question:** What is the instrument, what does it measure, and what decision is the pilot intended to support?

6. **Quote:** “code anchors”
   **Type:** `undefined term`
   **Question:** What are code anchors, and what behavior must they enforce?

7. **Quote:** “prompt rev 2”
   **Type:** `assumed prior context`
   **Question:** What was revision 1, what exactly changed in revision 2, and why?

8. **Quote:** “Three pilot runs x 30 CAPs read raw”
   **Type:** `missing outcome`
   **Question:** Were 90 distinct CAPs evaluated or the same 30 three times, what does “read raw” mean, and what were the results of each run?

9. **Quote:** “docs/census/cap-journey-pilot-2026-09-05.*”
   **Type:** `unexplained identifier`
   **Question:** Which concrete files does this wildcard represent, what does each contain, and which should a reviewer open first?

10. **Quote:** “enum-leak demotion”
    **Type:** `undefined term`
    **Question:** What is an enum leak, where was it occurring, and what does demotion change?

11. **Quote:** “own-example-dir exclusion”
    **Type:** `undefined term`
    **Question:** What is the own-example directory, what process was reading it, and what exactly is now excluded?

12. **Quote:** “self-consumption made every example keep”
    **Type:** `undefined term`
    **Question:** What consumed its own output, and what does `keep` mean as an outcome or classification?

13. **Quote:** “node-type consumer needles”
    **Type:** `undefined term`
    **Question:** What are consumer needles, which node types are involved, and what problem do they solve?

14. **Quote:** “extend_to”
    **Type:** `unexplained identifier`
    **Question:** Is `extend_to` a field, generated value, prompt concept, or code symbol, and what is its required behavior?

15. **Quote:** “journeys.yaml”
    **Type:** `unexplained identifier`
    **Question:** What role does `journeys.yaml` have, and which entries are relevant to this change?

16. **Quote:** “wedges”
    **Type:** `undefined term`
    **Question:** What are wedges in this project, and how do they determine `extend_to`?

17. **Quote:** “value_generic filter”
    **Type:** `unexplained identifier`
    **Question:** What is `value_generic`, what does the filter accept or reject, and why?

18. **Quote:** “tolerant evidence match”
    **Type:** `mechanism without purpose`
    **Question:** What matching rule became tolerant, what differences are tolerated, and how are false matches prevented?

19. **Quote:** “kind recorded”
    **Type:** `undefined term`
    **Question:** What `kind` is recorded, where is it stored, and how is it used?

20. **Quote:** “author_graph”
    **Type:** `unexplained identifier`
    **Question:** What is `author_graph`, and what responsibility does it have?

21. **Quote:** “junk-drawer cap”
    **Type:** `undefined term`
    **Question:** What is considered junk-drawer content, what cap is applied, and why is that threshold correct?

22. **Quote:** “scripts/author.sh”
    **Type:** `unexplained identifier`
    **Question:** What does this script generate or modify, and how should a reviewer reproduce revision 2 with it?

23. **Quote:** “extend removed”
    **Type:** `undefined term`
    **Question:** What is `extend`, where was it removed from, and why is that different from the retained `extend_to` behavior?

24. **Quote:** “render.py split keeps tools.py under the size gate”
    **Type:** `mechanism without purpose`
    **Question:** What code moved between these files, what imposes the size gate, and what is its threshold?

25. **Quote:** “Shape anchors”
    **Type:** `undefined term`
    **Question:** What are shape anchors, and what conditions determine whether one passes?

26. **Quote:** “pass 30/30”
    **Type:** `claim without pointer`
    **Question:** Which 30 cases passed, where are their results, and how does this denominator relate to the three runs of 30 CAPs?

27. **Quote:** “journey canaries”
    **Type:** `undefined term`
    **Question:** What are the journey canaries, and what behavior are they intended to detect?

28. **Quote:** “still miss”
    **Type:** `missing outcome`
    **Question:** How many canaries miss, what expected result do they miss, and what is the practical consequence?

29. **Quote:** “one rubric revision”
    **Type:** `assumed prior context`
    **Question:** Which rubric was revised, what changed, and where can the before-and-after versions be reviewed?

30. **Quote:** “prompt loop exited”
    **Type:** `undefined term`
    **Question:** What is the prompt loop, what are its stopping conditions, and why is exiting acceptable while journey canaries still miss?

31. **Quote:** “per plan section 8”
    **Type:** `assumed prior context`
    **Question:** Which plan is being referenced, where is section 8, and what stopping rule does it specify?

32. **Quote:** “FR-990 Proposed Solution 1-5”
    **Type:** `assumed prior context`
    **Question:** Where are Proposed Solutions 1–5, what fixes do they require, and are any of them merge blockers?

33. **Quote:** “remaining fixes”
    **Type:** `missing outcome`
    **Question:** What known defects remain after this PR, and what behavior remains incorrect until they are implemented?

## 4. What is missing entirely

- The project-level purpose of the census and the problem it is intended to solve.
- The intended users or beneficiaries and the expected user-visible outcome.
- A clear statement of the PR’s exact scope, including whether it contains both the initial feature and subsequent pilot fixes.
- Definitions of the data model, classifications, and expected output.
- Concrete pilot findings, including examples and a mapping from each finding to each change.
- The pilot methodology: sample source, selection criteria, whether runs used distinct rows, prompt/model configuration, and reproducibility instructions.
- Acceptance criteria for shape anchors, journey canaries, and the overall feature.
- Complete quantitative results for all three runs, including failures rather than only “30/30.”
- Test commands, automated-test results, and pointers to the evidence supporting the pass claims.
- An explanation of the impact and severity of the journey-canary misses.
- The contents and merge-blocking status of the five remaining proposed fixes.
- A reviewer entry point linking the requirement, plan, rubric, raw artifacts, and relevant code.
- Compatibility, rollout, and failure-risk information.
- The provenance, permissions, sensitivity assessment, and retention expectations for the committed raw rows.
