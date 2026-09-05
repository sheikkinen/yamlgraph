<!-- outsider spike | input: inputs/pr-591.md | model: gpt-5.6-sol | 2026-09-05T05:25:20.601729+00:00 -->

## 1. In my own words

This change instruments and pilots an FR-990 CAP journey census using three runs of 30 raw CAP rows, commits the raw results, and applies code fixes for issues found during that read, including filtering, evidence matching, consumer detection, directory exclusion, and graph limits. It also revises the authoring prompt for end-user journeys and splits `render.py` to keep `tools.py` within a size limit. Shape anchors passed all 30 cases, but journey canaries still missed after one rubric revision, so the prompt loop stopped according to plan and the remaining fixes were recorded elsewhere. The text does not say who uses the census or its output.

## 2. Could I decide whether to merge this from the description alone?

YES

The description identifies the changes, pilot findings, result locations, observed outcomes, and intentionally deferred work.

## 3. Words and references I could not understand

- **“FR-990”** · What requirement, issue, or design document does this identifier refer to?
- **“CAP”** · What project-specific object or artifact does CAP denote?
- **“journeys.yaml wedges”** · What are wedges in this file, and how do they define `extend_to`?
- **“shape anchors”** · What conditions or checks does this project call shape anchors?
- **“journey canaries”** · What are these canaries, and what constitutes a miss?
- **“enum-leak demotion”** · What project behavior is considered an enum leak, and what does demotion do?
- **“author_graph junk-drawer cap”** · What is `author_graph`, what enters its junk drawer, and what limit was added?
- **“FR-990 Proposed Solution 1-5”** · Where is this referenced proposal, and what work do items 1–5 contain?

## 4. What a merge decision would still need

- [ ] The exact journey-canary failures and their expected impact.
- [ ] Whether those known misses are acceptable under the merge criteria.
- [ ] The commands for reproducing the pilot and running the stated anchor checks.
- [ ] Results from relevant tests beyond the 30 shape-anchor cases.
- [ ] The runtime, cost, or operational impact of the new instrumentation and prompt revision.
- [ ] Compatibility or migration risks from the filtering and matching behavior changes.
