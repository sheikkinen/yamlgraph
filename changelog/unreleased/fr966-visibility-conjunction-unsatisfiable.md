---
type: fix
scope: census
req: REQ-YG-643
---
- **FR-966 Reject unsatisfiable multi-value `visibility` in authored-PR discovery**: `gh search prs` conjoins repeated `--visibility` flags into `is:` qualifiers and a pull request has exactly one visibility, so a list of two or more classes matched nothing and the empty population was blamed on the author/owner/since triple. The cardinality is now refused at the input boundary — after every existing per-entry check, before any network call — with a diagnostic naming the conjunction, reproducing the supplied list in its original order and spelling, and stating the one-class-per-run remedy. (REQ-YG-643)
