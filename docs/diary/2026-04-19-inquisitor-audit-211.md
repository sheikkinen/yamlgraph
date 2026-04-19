## 2026-04-19: Inquisitor Audit — FR-251 Harden Remote Inbox

**Context:** Audited the latest 5 commits on `feat/fr-251-harden-remote-inbox` against the Scripture. The work covers FR-251 (inbox hardening), a CAP/REQ collision fix, and two docs(FR) commits for the enforce pipeline.

**Findings:**

- ✓ COMPLIANT — **TDD RED/GREEN separation** (Commandment 7): RED commit (`e63153e3`) ships 11 failing tests with `SKIP=pytest`; GREEN commit (`46525e16`) makes them pass. Textbook discipline.

- ✓ COMPLIANT — **Requirement traceability** (ADR-001): CAP-109/REQ-YG-256 added to ARCHITECTURE.md. All 8 test functions carry `@pytest.mark.req("REQ-YG-256")`. Changelog fragment has `req: REQ-YG-256` front-matter.

- ✓ COMPLIANT — **Diary reflection** (Sermon: Distill): `2026-04-20-reflection-fr-251-harden-remote-inbox.md` names the cognitive trap ("detection without enforcement at design level"), extracts a heuristic, and plants a seed.

- ⚠ DRIFT — **CAP/REQ ID collision** required fixup commit (`d5ee4c2f`): FR-251 initially claimed CAP-108/REQ-YG-255, already taken by FR-247. Renamed to CAP-109/REQ-YG-256. No harm done, but manual ID allocation is collision-prone. The registry has no uniqueness gate at allocation time — only post-hoc detection.

- ✓ COMPLIANT — **Conventional Commits & FR reference** (Commandment 10): All 5 commits follow format. The `feat` commit references `FR-251` in title. `docs` and `chore` commits correctly omit FR ref.

**Heuristic:** CAP/REQ IDs are allocated manually by scanning the tail of ARCHITECTURE.md. Collisions are caught only when a second FR touches the same region. A monotonic counter file (e.g., `.chaplain/next-cap-id`) or a pre-commit uniqueness check on capability IDs would prevent collisions at allocation time rather than after the fact.

**Seed:** Could the `check_changelog_req.py` script (FR-247) be extended to also validate CAP-ID uniqueness in ARCHITECTURE.md at CI time? That would close the gap between "ID looks free when I pick it" and "ID is actually free when it merges."
