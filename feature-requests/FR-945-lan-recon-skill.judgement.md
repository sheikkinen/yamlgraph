# Judgement: FR-945 LAN recon skill (WinRM inventory of idle machines) (DRAFT)

**Verdict:** APPROVED WITH REVISIONS -- a read-only, typed LAN inventory skill is a justified foundation, but authority activates only after the FR closes the target/identity and transport-security boundaries, specifies the inventory schema, reconciles its non-admin contract, and folds in dependency and requirement governance.

**Prior art:**
- [FR-945.research.md](FR-945.research.md), [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) — the artifacts under judgement here; self-references, not distinguished separately.
- [FR-946-huutokauppakone-inference-revival.md](FR-946-huutokauppakone-inference-revival.md), [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) — LAN-arc siblings; this judgement scopes FR-945 explicitly so that FR-946 mutation and FR-947 test delegation remain out of authorized scope (C-7).
- [FR-765-graph-authoring-workflow-skill.judgement.md](FR-765-graph-authoring-workflow-skill.judgement.md) [Enforced] — precedent for the "skill + adapter + guard" judgement pattern applied to a repo-local read-only capability; distinguished: FR-765 governs graph authoring, this governs a read-only LAN probe.


**Reviewed against:** `feature-requests/FR-945-lan-recon-skill.md`; `feature-requests/FR-945.research.md`; `feature-requests/research-briefs/operator-work-delegation-idle-machines-brief.md`; `feature-requests/FR-766-runpod-provider.md`; `feature-requests/FR-766-runpod-provider.judgement.md`; `feature-requests/FR-902-session-worktree-lifecycle.md`; `feature-requests/FR-902-session-worktree-lifecycle.judgement.md`; `feature-requests/FR-411-inquisitor-watcher2-reintegration.md`; `feature-requests/FR-765-graph-authoring-workflow-skill.md`; `feature-requests/FR-765-graph-authoring-workflow-skill.judgement.md`; `feature-requests/FR-291-watcher-fsm-phase1-action-wiring.md`; `feature-requests/FR-946-huutokauppakone-inference-revival.md`; `feature-requests/FR-947-remote-pytest-delegation.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `ARCHITECTURE.md`; `pyproject.toml`; `reference/development-operations.md`; `capabilities/CAP-158-copilot-skill-promotion.yaml`; `tests/unit/test_fr446_copilot_skills.py`; `.github/skills/graph-authoring/SKILL.md`; `.gitignore`. The ignored `.env` file linked by the FR was not consumed under input closure.

## What is sound

The first consumer and event are concrete, and the problem has a physical witness rather than a hypothetical fleet abstraction: the FR names the next Huutokauppakone probe and records the successful qualified-user, SID, non-admin, and PowerShell-encoding observations (`feature-requests/FR-945-lan-recon-skill.md:8`, `feature-requests/FR-945-lan-recon-skill.md:81-90`). The desired output is also correctly placed at an external-data boundary: a Pydantic-validated inventory is safer than allowing later delegation FRs to infer readiness from stale environment configuration (`feature-requests/FR-945-lan-recon-skill.md:18-32`; `.github/copilot-instructions.md:40-53`).

The read-only responsibility is coherent. FR-945 inspects host state; FR-946 mutates LM Studio/bootstrap state; FR-947 delegates test execution (`feature-requests/FR-946-huutokauppakone-inference-revival.md:11`, `feature-requests/FR-947-remote-pytest-delegation.md:11-12`). Keeping those writes out of this FR gives the enforcer a narrow first increment and preserves independent test and review boundaries.

The committed research record satisfies the prospective research shape in substance: it contains five genuine solution classes, preserves disagreement between OS-native delegation, a managed registry, direct service revival, and subtraction, and answers `is_this_a_graph` for every candidate (`feature-requests/FR-945.research.md:17-23`; `.github/skills/judge-fr/doctrine.md:118-127`). The selected WinRM route is feasible in principle with the repository's Python/Pydantic environment, and the proposed `dev` extra is an existing dependency surface (`pyproject.toml:10`, `pyproject.toml:39-50`).

The skill packaging follows established repository precedent: skill frontmatter and substance are already requirement-tested under CAP-158 / REQ-YG-423 (`capabilities/CAP-158-copilot-skill-promotion.yaml:20-45`; `tests/unit/test_fr446_copilot_skills.py:46-82`). The new behavior itself still needs its own capability requirement rather than being hidden under the generic promotion requirement.

Strategic classification: **framework primitive, repo-local operational boundary**. The same typed read-only probe serves at least three named uses -- inference revival, worker provisioning, and endpoint diagnosis -- and no existing abstraction supplies host inventory. This does not authorize a YAMLGraph runtime primitive or a generic remote-execution framework.

## Required revisions

### R-1: Complete the research and committed-evidence disposition

Add a short selection table to FR-945 that dispositions every candidate in `FR-945.research.md` against the chosen WinRM inventory increment: SSH/pytest delegation, managed registry/health graph, direct LM Studio revival, removal of local pre-commit execution, and pytest-xdist SSH. State why read-only WinRM inventory is the smallest prerequisite rather than merely a sixth undisclosed alternative. The current research calls direct LM Studio revival the minimal first increment and separately proposes a registry/health graph (`feature-requests/FR-945.research.md:20-23`), while the FR moves to WinRM without recording that decision.

Disposition the retrieved `FR-291-watcher-fsm-phase1-action-wiring.md` hit and the separately retrieved `FR-765-graph-authoring-workflow-skill.judgement.md` hit in the Prior art field. The template requires every printed retrieval hit to be distinguished or dismissed (`feature-requests/TEMPLATE.md:23-29`), but FR-945 currently omits FR-291 and names only the FR-765 proposal (`feature-requests/FR-945-lan-recon-skill.md:10-14`; `feature-requests/FR-945.research.md:10-15`).

Replace the link to ignored `../.env#L18` with a committed sanitized evidence line in FR-945 or its research record. `.env` is explicitly ignored (`.gitignore:7`) and cannot be a judge input; no credential or full environment file may be committed.

### R-2: Define and secure the target, identity, timeout, and output-path boundary

Replace the ambiguous "mDNS name (or IP)" contract with these mechanically testable rules:

1. Accept a DNS/mDNS name or IP plus optional `--computer-name`.
2. Require `--computer-name` for an IP literal. For a DNS name, derive the candidate Windows computer name from the leftmost label only when it is a valid Windows computer-name token; otherwise require the flag.
3. Resolve once, reject unresolved, loopback, multicast, unspecified, and public targets, and connect only to the pinned private/link-local address produced by that resolution. Do not re-resolve downstream.
4. Qualify a bare `LAN_RECON_USER` as `<COMPUTERNAME>\<user>` before client construction; reject already qualified/domain-shaped values unless the FR explicitly adds and tests that mode. After authentication, require the returned computer name to match the selected name case-insensitively.
5. Configure finite connection and operation timeouts in `pypsrp.client.Client`; unit tests must assert the exact timeout kwargs.
6. Derive `tmp/lan/<safe-host>.json` from a normalized safe slug, never the raw argument. Tests must prove separators, `..`, control characters, and an IPv6 colon cannot escape or corrupt `tmp/lan/`.

This closes the circularity in the current proposal: `<COMPUTERNAME>\<user>` is required before the handshake, but an IP input does not reveal `COMPUTERNAME` (`feature-requests/FR-945-lan-recon-skill.md:18`, `feature-requests/FR-945-lan-recon-skill.md:44`, `feature-requests/FR-945-lan-recon-skill.md:70`). It also applies the repository's boundary-normalization law before credentials are sent or a path is written (`.github/copilot-instructions.md:40-53`).

### R-3: Make the WinRM transport security decision explicit

Add a human security-decision block to the FR with these options and record the selected option before enforcement:

- **A (recommended for this witnessed home-LAN target):** HTTP 5985 with `auth="negotiate"`, mandatory WSMan message encryption, a pinned private/link-local resolved address, and an explicit ban on Basic/CredSSP.
- **B:** HTTPS 5986 with certificate validation, with the listener/certificate provisioning moved into separately judged bootstrap work.

The current FR says only HTTP 5985 plus Negotiate (`feature-requests/FR-945-lan-recon-skill.md:45`). The implementation must not silently rely on a library default for whether password-based traffic is encrypted. Tests must inspect the constructed client arguments, and exceptions/logs/JSON must never contain `LAN_RECON_PASS` or an authentication token.

### R-4: Specify the inventory schema and keep the probe non-admin and read-only

Add a schema table to the FR naming every `LanHostInventory` field, nested model, type, required/optional status, units, and normalization rule. At minimum it must account for every advertised output plus boundary evidence: requested host, resolved address, computer name, OS, CPU, RAM bytes, GPUs, Python versions, WSL state, LM Studio/service/listener state, listening ports, disk-free bytes, `admin`, and membership in `S-1-5-32-580` (`feature-requests/FR-945-lan-recon-skill.md:18`, `feature-requests/FR-945-lan-recon-skill.md:46-51`). Unknown or unavailable commands must be represented by typed optional/error fields defined in that table, not omitted ad hoc or replaced with plausible values.

Move the fixed inventory block into a committed `.github/skills/lan-recon/inventory.ps1` artifact. It must be pure ASCII, contain no interpolation of hostname, username, password, or other caller-controlled text, emit one JSON document, and be parsed through `LanHostInventory` before any output file is written. The encoding test must inspect this actual artifact; the current conditional "generated `.ps1`" AC can pass vacuously when no file is generated (`feature-requests/FR-945-lan-recon-skill.md:47-49`, `feature-requests/FR-945-lan-recon-skill.md:72`).

Remove `Get-SmbShare` and `Get-SmbServerConfiguration` from this FR. SMB/file-drop work is explicitly assigned to a follow-up (`feature-requests/FR-945-lan-recon-skill.md:90`) and is not needed for the advertised readiness inventory. The script may only read state and may check Remote Management Users membership by SID; it must not add users, alter groups, change policy, install software, start services, create shares, or deliver another script.

Reconcile the error contract with least privilege. The FR requires `admin=False` but currently prescribes `LocalAccountTokenFilterPolicy != 1` as a likely auth cause (`feature-requests/FR-945-lan-recon-skill.md:51`, `feature-requests/FR-945-lan-recon-skill.md:75`). For this non-admin v1, the actionable auth error must name credential/qualification failure and missing `S-1-5-32-580` membership. Remove the token-filter-policy claim unless the FR adds committed evidence that it affects the exact non-admin commands authorized here.

### R-5: Replace the ambiguous test list with direct behavioral witnesses

Commit a sanitized happy-path fixture under `tests/fixtures/lan_recon/` and name it in the FR. It must contain the witnessed Huutokauppakone values needed for semantic assertions, not merely parseable JSON: computer name, non-admin status, OS, Ryzen 7 5800X CPU, 24 GB RAM, and RTX 3070 GPU (`feature-requests/FR-945-lan-recon-skill.md:81-89`). Tests must assert those values and a model JSON round-trip so a shape-correct but semantically wrong mapping fails.

Replace "four refusal paths" with an exact list. Offline tests must cover missing user, missing password, invalid/public target, unresolvable target, IP without computer name, name mismatch, WinRM authentication failure, transport timeout, malformed PowerShell JSON, Pydantic validation failure, unsafe output slug, and password redaction. Mock DNS and `pypsrp.client.Client` so the offline suite opens no socket. The CLI tests must assert non-zero status and actionable stderr for each refusal, while library functions raise typed exceptions rather than calling `sys.exit`.

Keep one real manual verification because this capability exists to observe a physical WinRM boundary. Record in FR-945 the command, generated `tmp/lan/...json` path, successful Pydantic validation, `admin=false`, SID-membership result, and selected hardware/service values. Do not record credentials. A mock-only result cannot satisfy this witness (`.github/copilot-instructions.md:86-89`; `feature-requests/FR-945-lan-recon-skill.md:76-79`).

### R-6: Add requirement, dependency, documentation, and lifecycle governance

Create a dedicated `capabilities/CAP-XXX-lan-host-recon.yaml` with a new unused `REQ-YG-XXX`, register the skill, Python modules, PowerShell artifact, and tests, regenerate the corresponding `ARCHITECTURE.md` section, tag every new test with the requirement, and require `python scripts/req_coverage.py --strict` to pass. CAP-158 / REQ-YG-423 may continue to govern generic skill discovery/frontmatter, but it must not be the only requirement attached to WinRM behavior (`.github/copilot-instructions.md:165-168`; `capabilities/CAP-158-copilot-skill-promotion.yaml:20-45`).

Keep `pypsrp>=0.10` in the proposed `dev` extra only if installation succeeds on both supported CI interpreters, Python 3.11 and 3.13 (`pyproject.toml:10`, `pyproject.toml:39-50`). Update `constraints/dev-py312.txt`, run the declared dependency CVE scan, and run the direct-import scan; record any version constraint required by those checks in the FR rather than silently widening or skipping it (`reference/development-operations.md:7-44`, `reference/development-operations.md:102`).

Require `SKILL.md` frontmatter with `name: lan-recon`, a substantive `Use when:` trigger, and a non-empty `argument-hint`; document the exact invocation, read-only boundary, credential prerequisites, and refusal behavior. Add `LAN_RECON_USER` / `LAN_RECON_PASS` placeholders to `.env.sample`, document them in `reference/development-operations.md`, add a requirement-linked changelog fragment, add the required diary reflection, and update FR-945 with implementation status and deviations (`tests/unit/test_fr446_copilot_skills.py:46-82`; `reference/development-operations.md:98-104`; `.github/copilot-instructions.md:26`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/lan-recon/SKILL.md`: discovery frontmatter, invocation, read-only triggers, credential and refusal contract. |
| D-2 | `.github/skills/lan-recon/recon.py`: validated CLI/library boundary, one pinned LAN resolution, qualified identity, finite-timeout encrypted WinRM client, Pydantic validation, safe JSON write. |
| D-3 | `.github/skills/lan-recon/models.py`: typed `LanHostInventory` and typed nested models matching the folded schema table. |
| D-4 | `.github/skills/lan-recon/inventory.ps1`: fixed ASCII, read-only, non-admin inventory script emitting one JSON document. |
| D-5 | `tests/unit/test_lan_recon.py` and `tests/fixtures/lan_recon/`: offline boundary/refusal tests, semantic fixture assertions, serialization round-trip, password-redaction and ASCII witnesses. |
| D-6 | `pyproject.toml` and `constraints/dev-py312.txt`: declared `pypsrp` dependency and reproducibility update. |
| D-7 | `capabilities/CAP-XXX-lan-host-recon.yaml` and generated `ARCHITECTURE.md` section: dedicated requirement traceability. |
| D-8 | `reference/development-operations.md` and `.env.sample`: credential placeholders and operational usage without secrets. |
| D-9 | `feature-requests/FR-945-lan-recon-skill.md`, `changelog/unreleased/`, and `docs/diary/`: folded revisions, implementation/live witness, changelog, and reflection. |
| D-10 | Runtime-only `tmp/lan/<safe-host>.json`: ignored, validated inventory output; never committed. |

Not authorized: changing `.env`; committing credentials or host inventory; public-host WinRM; Basic or CredSSP authentication; remote mutation of users, groups, policy, services, software, firewall, shares, scheduled tasks, SSH, WSL, Python, or LM Studio; SMB/file-drop support; FR-946 revival behavior; FR-947 remote pytest behavior; a generic remote-command API; YAMLGraph runtime changes; hooks, CI, judge/review doctrine, or adapter changes.

## Revised acceptance criteria

- [ ] AC-01: FR-945 contains the folded research-selection table, dispositions every retrieved prior-art hit, and replaces the ignored `.env` link with committed sanitized evidence.
- [ ] AC-02: `.github/skills/lan-recon/SKILL.md` has valid frontmatter (`name`, substantive `Use when:` description, non-empty `argument-hint`) and documents the exact read-only invocation and refusal contract.
- [ ] AC-03: FR-945 contains the complete `LanHostInventory` schema table; Pydantic models implement it without untyped result dictionaries crossing the parsing boundary.
- [ ] AC-04: DNS/mDNS and IP inputs obey R-2: IP requires `--computer-name`; invalid/non-LAN targets and unsafe names are rejected; resolution is pinned; returned computer-name mismatch fails.
- [ ] AC-05: A bare `LAN_RECON_USER` is qualified as `<COMPUTERNAME>\<user>` before client construction; missing user/password fails before DNS or WinRM; qualified/domain-shaped input follows the folded explicit contract.
- [ ] AC-06: The human-selected transport option is recorded. Client-construction tests prove its auth, encryption, address, and finite-timeout kwargs; Basic/CredSSP are absent; no error, log, or JSON contains the password.
- [ ] AC-07: `inventory.ps1` is committed, pure ASCII, contains no caller-controlled interpolation, performs only the frozen read operations, uses SID `S-1-5-32-580`, and emits exactly one JSON document.
- [ ] AC-08: The inventory contains all typed advertised fields, records `admin` and Remote Management Users membership, and excludes SMB share/server configuration.
- [ ] AC-09: Successful output is Pydantic-validated before an atomic write beneath `tmp/lan/`; the safe filename cannot escape that directory; `LanHostInventory.model_validate_json()` round-trips the file.
- [ ] AC-10: Offline tests cover every refusal listed in R-5 with no real DNS/socket/WinRM call and assert non-zero CLI status plus actionable stderr; library functions expose typed exceptions.
- [ ] AC-11: The committed sanitized Huutokauppakone fixture asserts concrete computer, OS, CPU, RAM, GPU, admin, and SID-membership values rather than parse success alone.
- [ ] AC-12: A real Huutokauppakone verification is recorded in FR-945 with command, JSON path, model-validation result, `admin=false`, membership result, and selected inventory values, with no credential material.
- [ ] AC-13: `pypsrp>=0.10` is declared in `dev`; editable dev installation succeeds under Python 3.11 and 3.13; `constraints/dev-py312.txt`, dependency audit, and direct-import scan are updated/passing.
- [ ] AC-14: A dedicated capability and new requirement register all implementation/test surfaces; all new tests carry `@pytest.mark.req(...)`; generated architecture and `python scripts/req_coverage.py --strict` agree.
- [ ] AC-15: `reference/development-operations.md` and `.env.sample` document only credential names, prerequisites, invocation, and security boundaries; no real username/password is committed.
- [ ] AC-16: The FR implementation record, requirement-linked changelog fragment, and diary reflection are present, and no surface from the not-authorized list changed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement from the current FR text until R-1 through R-6 and the human transport decision are folded into FR-945; authority is revision-gated. | GATE |
| C-2 | The v1 skill is read-only and non-admin. It may inventory and report state only; no remote mutation or reusable arbitrary-command/script-delivery API is authorized. | GATE |
| C-3 | Credentials may be used only for a pinned private/link-local target with the selected encrypted Negotiate/HTTPS contract; they must never enter committed files, JSON, logs, or exception text. | GATE |
| C-4 | The fixed PowerShell artifact and parsed output must satisfy the folded typed schema. Missing commands/data surface explicitly; no silent omission or plausible fallback is permitted. | GATE |
| C-5 | Do not claim live validation from mocks. The physical Huutokauppakone witness must actually run or be recorded as blocked with the exact command and reason. | GATE |
| C-6 | Dependency installation on the supported Python matrix, the dependency audit, requirement coverage, targeted offline tests, and the exact live witness are all required before completion. | GATE |
| C-7 | FR-946 mutation/bootstrap, FR-947 test delegation, SMB/file drop, `.env` repair, generic remote execution, hooks, CI, and YAMLGraph runtime work require separate authority. | GATE |

Authority granted: after all required revisions and the human transport-security decision are folded into FR-945, the enforcer may build one repo-local, read-only, non-admin LAN WinRM inventory skill within D-1 through D-10 and no adjacent remote-management capability.
