# 2026-08-20 — Four Prompts, One Policy

The cookbook preflight exposed one contradiction, but tracing ownership showed
it was not a bad sentence in `judge.yaml`. Planning was silent, judgement
forbade tools, enforcement demanded YAML only, and review inherited whatever
survived. Fixing judge alone would have moved the disagreement one stage later.

**Trap: patching the prompt where the symptom speaks.** Multi-agent pipelines
often repeat a capability boundary in role-specific prose. The first visible
rejection looks locally owned, while the real defect is that no shared policy
owns the boundary. Prompt edits then become distributed schema migrations with
no schema and no drift test.

**Heuristic:** when two stages disagree about an allowed artifact class, search
every stage before editing one. Extract one human-readable policy, make each
stage reference it, and test the references plus exact known contradictions.
Do not pretend a text test proves semantic safety; it proves contract alignment.

The judge also caught a smaller form of the same error: the proposed test
assumed PyYAML because YAMLGraph has it, while gitclaw CI installs only pytest.
The consumer environment, not the author's environment, owns test feasibility.

**Seed:** should policy files eventually become typed capability manifests that
prompt stages render from, so allowed artifacts and effects cannot diverge as
free prose?
