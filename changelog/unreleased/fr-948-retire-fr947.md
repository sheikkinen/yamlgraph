---
type: removal
scope: skills
---

- **FR-947 remote-pytest SSH delegation retired (superseded by FR-948)**: The
  SSH+WSL2+pytest-xdist design in FR-947 was retired without implementation
  after the empirical spike proved a WinRM+Copilot channel with none of that
  infrastructure. FR-947's file body carries the `**STATUS: SUPERSEDED-BY
  FR-948**` banner; no source, capability, or test surface ever landed under
  FR-947 authority.
