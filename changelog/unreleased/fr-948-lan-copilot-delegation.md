---
type: feat
scope: skills
req: REQ-YG-636
---

- **FR-948 LAN Copilot delegation channel**: `.github/skills/lan-delegate/` skill
  submits ONE clean-committed workload from the mac to a FR-945-recon-verified LAN
  Windows host over WinRM+Copilot CLI, in a disposable per-run detached git worktree
  with a wrapper-owned wall-clock deadline enforced via `taskkill /PID <root> /T /F`.
  Scaffold: 19-value `DelegationPolicyStatus` closed enum with total precedence
  resolution, `LanDelegationResult`/`LanDelegationRequest`/`RemoteCopilotPrerequisites`
  Pydantic schemas, 10 typed pre-launch exception classes. Wire: `wrapper.ps1` (pure
  ASCII PS 5.1, param-bound Token/Prompt/RunId/TimeoutS/LocalSha, non-LLM preflight,
  Start-Job in-memory capture with 4 MiB bound, byte-scan artifacts for
  `TOKEN_LEAK_DETECTED`, in-memory redaction before any filesystem write, cleanup in
  outer finally). `delegate.py` (CLI + library) validates 10 pre-launch conditions
  before DNS/WinRM/file write, constructs pypsrp.WSMan with Option A kwargs
  (auth=negotiate, encryption=always, ssl=False, port=5985, pinned resolved address,
  operation_timeout=timeout_s+WSMAN_CLEANUP_MARGIN_S), passes Token+Prompt+RunId as
  bound parameters (never in script literal), parses `WrapperJsonSummary`, emits
  `LanDelegationResult` JSON. Enforcement of R-1..R-6 from three judgement rounds
  (argv integrity via `& operator, full-tree taskkill, in-memory capture,
  recursive-delegation guard via YAMLGRAPH_LAN_DELEGATED marker, byte-scan on
  literal-token match, phase-invariant result totality). 34 offline tests
  (13 scaffold + 21 wire); live witnesses AC-19/AC-20 pending. (REQ-YG-636)
