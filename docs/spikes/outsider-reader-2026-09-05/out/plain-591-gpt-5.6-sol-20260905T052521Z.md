<!-- outsider spike | input: inputs/plain-591.md | model: gpt-5.6-sol | 2026-09-05T05:25:39.284259+00:00 -->

## 1. In my own words

This change adds an automated pipeline that gathers descriptions, originating requests, and code-usage evidence for a list of 242 claimed capabilities, then uses an AI model plus deterministic checks and six hidden reference cases to classify each capability by user type, recommend keeping or removing it, and describe its value. Three trial runs over 30 capabilities produced valid rows by the third run, identified two apparent removal candidates, found that about half served only project developers, and showed that the user-type and business-value outputs remain unreliable. The intended recipient is someone deciding which capabilities to retain and how they serve users; the text does not identify that person or team more specifically.

## 2. Could I decide whether to merge this from the description alone?

NO

The description explains the change, trial findings, and known limitations, but does not say where the pipeline or its results are, how to run it, or what automated testing was added.

## 3. Words and references I could not understand

- **“the business plan”** · **Which plan defines the two priority user types, and where are those definitions?**
- **“the fast, cheap one we had agreed to try”** · **Which model is this, and where was that choice agreed?**
- **“the default in the template I copied”** · **Which template and default model does this refer to?**
- **“the project's internal shorthand”** · **Which terms in the implementation or output use this shorthand?**
- **“its rulebook”** · **What rulebook is this, and where can a reviewer find it?**
- **“someone writing a graph”** · **What does this user-type category mean in this project?**

## 4. What a merge decision would still need

- [ ] The files containing the pipeline and checker.
- [ ] The location and format of the 30-capability trial results.
- [ ] Instructions for running and configuring the pipeline.
- [ ] The model and model-version configuration used for the reported runs.
- [ ] The tests added, including how the six hidden expected answers are evaluated.
- [ ] The complete set and definitions of the ten user types.
- [ ] How codebase usage searches are performed and what kinds of references they can miss.
- [ ] Expected runtime and model cost for all 242 capabilities.
- [ ] Whether outputs are deterministic, reproducible, or sensitive to model changes.
- [ ] Which parts of the planned category-definition and fast-model work are intentionally excluded from this change.
