# Adopt review-pr skill bundle (csap NC-413 parity mirror)

- **Req:** FR-305
- Mirror of csap NC-413: PR review promoted to a skill bundle with full
  judge-fr parity — `doctrine.md` (canonical review contract),
  `SKILL.md`, `review.template.md` (merge verdict on LINE ONE),
  graph adapter (`adapters/graph.yaml` + pointer prompt), and
  `scripts/review.sh` operator wrapper (OS lock + `REVIEW_EXECUTION`
  sentinel + artifact contract with line-one verdict check + executor
  resolution `YAMLGRAPH_BIN` > PATH > `uv run`).
- `.github/prompts/review-pr.prompt.md` DELETED — the review graph via
  `scripts/review.sh` is the SOLE review execution route (Scripture
  Submit step amended); forbidden routes have no live surface.
- judge-fr `MANIFEST.yaml` and `adapters/README.md` no longer point at
  the deleted prompt.
- Contract tests live in csap `tests/test_nc413_review_wrapper.py`
  (8/8; same precedent as the judge.sh mirror).
