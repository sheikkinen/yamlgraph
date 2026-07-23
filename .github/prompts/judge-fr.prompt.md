---
description: "Judge a feature request — thin adapter; doctrine lives in the judge-fr skill"
argument-hint: "path to feature-requests/<ID>-*.md"
---

Read `.github/skills/judge-fr/doctrine.md` and apply it to the feature
request at ${input:fr_path}.

Input closure: the FR file, files it cites as evidence, and repo
doctrine ONLY. Do not consume chat history or author narrative.

Write `<fr-path-without-.md>.judgement.md` per
`.github/skills/judge-fr/judgement.template.md`. Output is advisory
until human-reviewed (NC-412 C-6).
