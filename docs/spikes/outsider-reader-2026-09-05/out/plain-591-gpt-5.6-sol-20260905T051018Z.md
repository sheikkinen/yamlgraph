<!-- outsider spike | input: inputs/plain-591.md | model: gpt-5.6-sol | 2026-09-05T05:11:16.842041+00:00 -->

## 1. In my own words

This change adds an automated pipeline intended to help the project team assess 242 claimed software capabilities by collecting descriptive and code-usage evidence, asking an AI model to classify each capability by user type and recommend keeping or removing it, checking those answers with non-AI code, and testing the process against six predetermined answers; however, the description reports only a 30-capability trial, and it does not identify the specific software, capabilities, users, or final recipient of the results.

## 2. Could I decide whether to merge this from the description alone?

NO

The full census and model comparison have not been completed, the classification is acknowledged to be unreliable, and the description provides no implementation pointers or reproducible test evidence.

## 3. Things I do not understand

1. **Quote:** “The project”
   **Type:** `unexplained identifier`
   **Question:** What project and software product does this refer to, and what does that software do?

2. **Quote:** “list of 242 ‘capabilities’”
   **Type:** `claim without pointer`
   **Question:** Where is this list, how are its entries identified, and what makes an entry an official capability?

3. **Quote:** “Census of the 242 capabilities”
   **Type:** `missing outcome`
   **Question:** Why does the title describe a census of all 242 when the completed work described here covers only 30?

4. **Quote:** “what kind of user does it serve”
   **Type:** `undefined term`
   **Question:** What qualifies as serving a user, and can one capability serve more than one user type?

5. **Quote:** “does anything still actually use it”
   **Type:** `undefined term`
   **Question:** What counts as actual use: a textual reference, a call path, runtime execution, configuration, documentation, generated code, or an external consumer?

6. **Quote:** “what is it worth”
   **Type:** `undefined term`
   **Question:** In what units or according to what rubric is worth assessed?

7. **Quote:** “the original request that created it”
   **Type:** `assumed prior context`
   **Question:** What are these requests, where are they stored, and how is each request linked reliably to a capability?

8. **Quote:** “a search of the codebase for anything that uses it”
   **Type:** `mechanism without purpose`
   **Question:** How does the search recognize use of a capability, particularly indirect, generated, dynamically configured, or external use?

9. **Quote:** “an AI model”
   **Type:** `unexplained identifier`
   **Question:** Which provider, model, version, configuration, and prompt were used?

10. **Quote:** “one of ten user types”
    **Type:** `undefined term`
    **Question:** What are all ten user types, and what are their definitions and decision boundaries?

11. **Quote:** “someone running a pipeline”
    **Type:** `undefined term`
    **Question:** What kind of pipeline and user behavior does this category represent in this project?

12. **Quote:** “someone auditing a corpus”
    **Type:** `undefined term`
    **Question:** What corpus is being audited, by whom, and for what purpose?

13. **Quote:** “only this project’s own developers”
    **Type:** `undefined term`
    **Question:** Which people count as the project’s developers, and how is developer-only use distinguished from customer-facing use?

14. **Quote:** “Plain code then checks”
    **Type:** `mechanism without purpose`
    **Question:** What exact deterministic rules are applied, and which parts of the model’s output do they validate?

15. **Quote:** “cites a user that the search did not find”
    **Type:** `mechanism without purpose`
    **Question:** How can a code search establish whether a particular kind of user exists or uses the capability?

16. **Quote:** “the row is marked ‘contested’”
    **Type:** `undefined term`
    **Question:** What does contested mean operationally, what other row states exist, and what happens to a contested result?

17. **Quote:** “Six capabilities whose correct answers I wrote down in advance”
    **Type:** `claim without pointer`
    **Question:** Which six capabilities were used, what were their expected answers, and what evidence establishes those answers as correct?

18. **Quote:** “hidden in the batch”
    **Type:** `mechanism without purpose`
    **Question:** Hidden from which pipeline components, and how was accidental exposure to the model prevented?

19. **Quote:** “the whole run is marked failed”
    **Type:** `undefined term`
    **Question:** Which fields must match for an answer to be correct, and what practical effect does a failed run have?

20. **Quote:** “a 30-capability trial”
    **Type:** `claim without pointer`
    **Question:** Which 30 capabilities were selected, how were they selected, and where are the trial inputs and outputs?

21. **Quote:** “three runs”
    **Type:** `undefined term`
    **Question:** What changed between the three runs, and were model settings and inputs otherwise held constant?

22. **Quote:** “all 30 rows were valid”
    **Type:** `undefined term`
    **Question:** What does valid mean, and does validity measure schema conformance, factual correctness, classification correctness, or something else?

23. **Quote:** “The fact-collection and checking parts work”
    **Type:** `claim without pointer`
    **Question:** What test results or artifacts demonstrate that these parts work, including their false-positive and false-negative behavior?

24. **Quote:** “three cases where the model invented a user”
    **Type:** `claim without pointer`
    **Question:** Which cases were these, what did the model claim, and what evidence showed that each claimed user was invented?

25. **Quote:** “Two capabilities have nothing in the codebase using them”
    **Type:** `missing outcome`
    **Question:** Which two capabilities are these, and what evidence rules out indirect or external use?

26. **Quote:** “If that rate holds, roughly 10–20”
    **Type:** `claim without pointer`
    **Question:** How was this range calculated, and why is the 30-capability sample representative enough to extrapolate to all 242?

27. **Quote:** “About half of the sampled capabilities”
    **Type:** `claim without pointer`
    **Question:** What is the exact count, which capabilities are included, and what evidence supports each classification?

28. **Quote:** “someone writing a graph”
    **Type:** `undefined term`
    **Question:** What does graph mean here, and what activity was this category intended to cover?

29. **Quote:** “a different category”
    **Type:** `missing outcome`
    **Question:** Which category became the replacement catch-all, and how often was it selected?

30. **Quote:** “the business plan”
    **Type:** `assumed prior context`
    **Question:** Which business plan is this, where can a reviewer inspect it, and how does it establish category priority?

31. **Quote:** “corpus auditing and compliance evidence”
    **Type:** `undefined term`
    **Question:** What are the project-specific definitions and intended users for these two categories?

32. **Quote:** “business value”
    **Type:** `undefined term`
    **Question:** What dimensions, evidence, and scoring criteria are supposed to determine business value?

33. **Quote:** “the default in the template I copied”
    **Type:** `unexplained identifier`
    **Question:** Which template was copied, where did it come from, and which model did it configure by default?

34. **Quote:** “the fast, cheap one we had agreed to try”
    **Type:** `assumed prior context`
    **Question:** Which model is this, who agreed to use it, and what speed, cost, and quality targets were agreed?

35. **Quote:** “a justification for that afterwards”
    **Type:** `claim without pointer`
    **Question:** Where is this justification, and does it affect the implementation or only an earlier explanation?

36. **Quote:** “My summaries”
    **Type:** `unexplained identifier`
    **Question:** Which summaries does this refer to, and where can the reviewer inspect them?

37. **Quote:** “the project’s internal shorthand”
    **Type:** `undefined term`
    **Question:** Which terms in the implementation or its outputs are internal shorthand, and what do they mean?

38. **Quote:** “its rulebook”
    **Type:** `assumed prior context`
    **Question:** What rulebook is this, where is it located, and which decisions in this change depend on it?

39. **Quote:** “Rerun the same 30”
    **Type:** `unexplained identifier`
    **Question:** Where is the exact, immutable definition of this 30-capability sample?

40. **Quote:** “compare”
    **Type:** `undefined term`
    **Question:** Which metrics and acceptance thresholds will be used to compare the agreed model with the original model?

41. **Quote:** “hand over the list”
    **Type:** `missing outcome`
    **Question:** Who receives the list, in what format, where will it be stored, and what decision are they expected to make from it?

## 4. What is missing entirely

- The files, modules, generated artifacts, or reviewer entry point included in the pull request.
- Instructions and commands for running the pipeline and reproducing the reported trial.
- The full list and definitions of the ten user categories.
- A formal rubric for keep/remove recommendations and business-value assessment.
- The identities and evidence for all 30 trial capabilities, especially the two removal candidates and six hidden checks.
- The raw and summarized outputs from each of the three runs.
- Automated test names, test commands, and results covering collection, model-output parsing, validation, and failure handling.
- Evidence that code search can detect indirect, dynamic, generated, configured, or externally initiated use.
- Model prompts, response schema, parameters, nondeterminism controls, and reproducibility expectations.
- Runtime, monetary cost, rate-limit behavior, retry behavior, and expected cost for all 242 capabilities.
- Data-handling and privacy implications of sending capability descriptions, original requests, or source-derived evidence to an AI provider.
- The pipeline’s behavior on malformed model output, unavailable requests, ambiguous matches, model failures, and incomplete searches.
- Whether the pipeline runs locally, in CI, or in production, and whether it changes any existing behavior.
- The completed comparison with the agreed fast model.
- Results for all 242 capabilities, including removal candidates, user-type counts, contested rows, and unresolved cases.
- Acceptance criteria defining when the pipeline is reliable enough for its recommendations to influence removal decisions.
