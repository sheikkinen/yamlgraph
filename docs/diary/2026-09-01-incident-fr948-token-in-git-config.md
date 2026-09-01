# Diary: token-in-URL leak during the FR-948 canonical-clone bootstrap

**Date:** 2026-09-01
**Arc:** FR-948 enforcement — canonical-clone bootstrap (out-of-FR-948-scope, operator-authorized preparation step)
**Severity:** LAN-scoped; token disclosed to Anthropic model context; operator elected to accept residual risk and proceed (`chill. we are in lan. token leaked to anthropic. well analyze the issue separately`).

## What happened

Driving the one-time canonical-clone bootstrap on Huutokauppakone via WinRM as `HUUTOKAUPPAKONE\copilot`, I wrote a PowerShell script that:

1. Built an in-memory URL string `https://x-access-token:$Token@github.com/...` from a `param([string]$Token)` binding (correct so far — no token in script literal).
2. Called `git clone $tokenedUrl $clonePath`.
3. INTENDED to rewrite `origin` to a tokenless URL after clone with `git remote set-url origin "https://$RepoUrlNoScheme"`.

The clone failed partway through (probably a WinRM timeout at 300s during network fetch on the ~350 MB repo). `$ErrorActionPreference='Stop'` aborted the script BEFORE the `set-url` cleanup ran. Result: partial clone with `.git/config` containing the tokened origin URL sat on the remote's disk.

Then I made it worse: my follow-up probe (checking whether the clone directory existed) printed the raw remote output via `str(line)` — without the `redact()` wrapper I had defined for the driver. The `git remote get-url origin` line came back with token bytes in it, and my terminal output entered the conversation context.

## Two composed defects

### Script-side
- **Token embedded in URL**, not delivered via a credential helper. The token is on disk from the moment `git clone` writes `.git/config` — even a clean `finally` scrub happens AFTER the disk write.
- **`$ErrorActionPreference='Stop'` + no `try/finally`** meant partial success left secret state on disk with no cleanup path.

### Agent-side (mine)
- **`redact()` was defined per-driver, not per-output-boundary.** I remembered to apply it in the first driver script; in the follow-up probe I "just checked whether the clone dir existed" and didn't wrap the output — but the same output stream carried arbitrary text from `git remote get-url origin`. The redact function should have been a policy applied at the print boundary, not a decoration each caller opts into.

## Why the operator called it acceptable

The blast radius is bounded:

- The token bytes hit two surfaces beyond the operator's control: (a) Huutokauppakone's local `.git/config` (disk on a LAN box; deleted seconds later), (b) Anthropic's model context (via my terminal-output tool result). The LAN box is under the operator's physical control; Anthropic is a known trust boundary.
- The token was already expected to enter Anthropic context in the FR-948 dated safety decision (`--allow-all-tools` on a delegated Copilot session means Copilot sees the token). This incident moved forward in time an exposure that was already accepted.
- No delivery vector to a non-LAN adversary. No public-facing service was involved.

The correct treatment is diary-first (this entry) so successors can learn without paying the token-rotation cost this session. Rotation happens on the operator's own timeline.

## The heuristic

**`secret_at_boundary_two_ways`**: when a script and an agent both handle a secret, BOTH must have a redact policy applied at the print boundary — not remembered per call. The redact function should be:
- Attached to the output stream (Python: `functools.partial(print, sep='', end='')` after `str.replace`; or a `RedactingWriter` wrapper class).
- Applied by DEFAULT to every WinRM/SSH/subprocess capture from a target the token has ever crossed, regardless of what output is "expected."
- Structurally impossible to skip: any `print(line)` that isn't `print(redact(line))` is a bug, and the linter should catch it.

**`credential_helper_over_url_embedding`**: for one-shot subprocess auth (`git`, `curl`, `docker login`, `kubectl`, `az login`, `gh` inline), use a credential-helper shim that reads from an env-scoped source. URL-embedded credentials leave persistent state on disk in every wrapper's config (`.git/config`, `~/.netrc`, `~/.kube/config`, `docker.io/config.json`). Even successful runs persist unless explicitly cleaned; failures never clean.

## Immediate cleanup completed

Sent one WinRM command as `copilot` immediately after detection:

```powershell
$path = 'C:\Users\copilot\yamlgraph'
if (Test-Path $path) { Remove-Item -Recurse -Force $path -EA SilentlyContinue }
Get-ChildItem "$env:TEMP\*token*" -EA SilentlyContinue | Remove-Item -Force -EA SilentlyContinue
```

Verified: `after-cleanup exists: False`, `cleanup complete`. Token bytes no longer on remote disk. Operator's residual exposure surface: Anthropic model context (accepted), and the token remains valid.

## Corrected pattern (next attempt)

Bootstrap script rewritten to use `GIT_ASKPASS` — a temp `.cmd` shim that echoes `$Token` from an env var. Clone URL is `https://x-access-token@github.com/...` (username only, no password). Resulting `.git/config` has zero token bytes. The shim is deleted in `finally`. Try/finally ensures cleanup even on partial failure.

Agent-side, the follow-up-probe pattern is now: `for line in ps.invoke(): print(redact(str(line)))` unconditionally, never `print(str(line))` on the same channel.

## Seed

**Seed:** what's the smallest invariant that would have STRUCTURALLY prevented this leak? Options: (a) a `RedactingRunspacePool` wrapper that consumes all output through a per-call redactor bound at pool construction; (b) a repo-wide lint rule that forbids `print(...)` on the return of `PowerShell.invoke()` without a wrapping function whose name matches `/redact|scrub|sanitize/`; (c) a policy that any secret that ever hits the wire is treated as compromised and rotated on session close, so the "did I remember to redact?" question becomes moot. The rotation-on-close option is expensive but eliminates the class; the lint rule is cheap but only catches syntactic use. Which trade-off would the operator find worth paying in FR-949 (if `remote:` on copilot node lands) or a follow-up FR?

## Consequence

Proceed with the corrected `GIT_ASKPASS` bootstrap. The FR-948 code path itself (delegate.py + wrapper.ps1) is NOT vulnerable to this class of failure because it never writes a `.git/config` — it uses `git worktree add`, which inherits `origin` from the canonical clone (which will be tokenless after this fix). Byte-scan on artifacts under `.delegate-out/` remains the defense for token-in-outputs; the risk of token-in-git-config is out-of-scope for FR-948 (canonical clone is a precondition, not authored by FR-948).

Rotation deferred to operator's choice.
