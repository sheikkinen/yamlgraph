---
type: feat
scope: hooks
---
- **FR-429 Post-Edit YAML Checks**: `post-edit-checks` now routes by file type instead of skipping all non-Python edits. Graph YAML files (`nodes` + `edges`) run `yamlgraph graph lint`; prompt YAML files under `prompts/` get YAML parse validation; non-target YAML is skipped to avoid false positives. Hook tests were extended with graph/prompt coverage while preserving Python checks.
