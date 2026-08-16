---
type: fix
scope: release
---
- **Release CI portability**: Pure network-sniff helpers no longer require Playwright at import time, example ownership tests use path components instead of checkout-name substrings, and regulated strict-evidence tests distinguish an unset route-log env from an explicit disable.
