---
type: feat
scope: skills
req: REQ-YG-637
---
- **FR-949 Issue-queue delegation runner (channel C)**: Private comms-repo GitHub-Issues delegation executed by a self-hosted Actions runner — canonical `.github/skills/issue-delegate/` worker bundle with typed request boundary (free-form target repo per operator override O-1), closed DelegationStatus/PublicationStatus enums, two-tier timeout truth, single redaction boundary, and full-output chunked publication (O-2). Bundle: `delegate.yml` workflow (authorization-before-mutation, credential-isolated checkout, atomic terminal mutation), control-side `submit.sh` with typed refusals and drift/runner health checks, `sync-worker.sh` byte-identical deployment, `windows_job.ps1` kill-on-close Job Object launcher with 25-minute inner deadline. Coexists with channel A (FR-948) until a separate disposition FR. Host installation scripted (`install-runner.ps1`: registration-token API, `--unattended --runasservice` service install, `DELEGATE_CHECKOUT_PAT` provisioning from the logged-in gh token — operator amendment striking the C-7 automation non-goal); reviewer doctrine gained the scriptability test for "human-owned" claims. (REQ-YG-637)
