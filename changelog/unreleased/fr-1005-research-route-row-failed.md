---
type: fix
scope: research
req: REQ-YG-665
---
- **FR-1005 Research route demotes a failed persona to a recorded row**: one persona whose output the model itself broke (a cell over 400 characters, a closed-enum miss, an empty cell) no longer kills the whole `scripts/research.sh` run. `gather_findings` leaves a typed `FailedPersona` record in that persona's canonical slot when exactly one recorded error belongs to its mapped graph node and is a structured-output validation failure; the reducer contains one such row by slot (never truncating or repairing it), keeps the librarian, ambiguous or non-model failures, fabricated precedent, two failures and the four-row/three-grounded floors fatal before any artifact is written, and stamps the artifact with JSON accounting (`- persona keys executed:`, `- personas failed:`) whose key set `research_preflight.verify_artifact` re-checks. Three runs on 2026-09-05 (and three on 2026-08-30, FR-926) had discarded four good findings each on one cell. (REQ-YG-665)
