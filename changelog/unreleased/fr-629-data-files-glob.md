---
type: feat
scope: graph
req: REQ-YG-478
---
- **FR-629 data_files Glob Support**: `data_files` now accepts glob patterns (e.g. `wiki/*.yaml`), loading all matching files into state as a dict keyed by filename stem. Completes read-write symmetry with `write_data_file` — write creates files, glob discovers them. Zero matches return empty dict. Recursive `**` rejected. Same security model as single-file paths. (REQ-YG-478, REQ-YG-479)
