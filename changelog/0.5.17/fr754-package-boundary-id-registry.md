---
type: fix
scope: package
---
- **FR-754 Package Boundary Cleanup**: moved ID registry helper out of `yamlgraph` package (`yamlgraph/utils/id_registry.py` removed, `scripts/id_registry.py` added), rewired validator/tests, and added a boundary test proving no `.chaplain` references remain under `yamlgraph/` Python modules.
