<!-- outsider spike | input: inputs/pr-591-v5.md | model: gpt-5.6-sol | 2026-09-05T05:53:15.363458+00:00 -->

## 1. In my own words

This change adds a local AI-assisted pipeline that gathers repository evidence for capabilities, assigns each one a user type and proposed disposition, validates the model’s citations, and fails runs that miss predefined canaries. A 30-capability trial found two removal candidates, many capabilities serving project developers rather than customers, three unsupported consumer claims, unreliable user-type classification, and unusable business-value summaries. It delivers the pipeline and committed trial ledgers for capability-retirement research; the text does not say who has final responsibility for acting on its recommendations.

## 2. Could I decide whether to merge this from the description alone?

YES

The description states what changed, summarizes the trial findings, identifies the relevant files and run command, and explicitly lists the unfinished work and operational limits.

## 3. Words and references I could not understand

**“the ten user-type names”** · What are the ten project-defined user types and their intended boundaries?

**“catalog”** · What checking rule does “catalog” refer to in the open unit-test acceptance criterion?

## 4. What a merge decision would still need

- [ ] How the 30 pilot capabilities were selected and whether the sample was intended to be representative.
- [ ] The expected and observed result for each of the six canaries across the three runs.
- [ ] The environment, package, and Anthropic credential setup required before the provided command can run.
- [ ] The exact rules used to infer which modules belong to a capability and which code-search hits count as references.
- [ ] Whether the project permits merging an FR while a stated acceptance criterion remains open.
