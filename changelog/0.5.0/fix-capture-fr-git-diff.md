### Fixed
- `capture_fr` state now uses `git diff --name-only main` to find only new FR files created by the plan step, preventing pickup of pre-existing FRs inherited from main.
