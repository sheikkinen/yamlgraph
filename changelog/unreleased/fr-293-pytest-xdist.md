## FR-293: pytest-xdist parallel test execution

- Added `pytest-xdist>=3.5.0` to dev dependencies
- Pre-commit pytest hook now uses `-n auto -m "not slow"` for parallel execution
- Fixed surrogate Unicode in `image_node.py` that crashed xdist workers
- Unit test fast run: 42s → 21s (parallel on 12 cores)
- CI workflow unchanged (coverage + xdist needs separate validation)
