"""ValidateGateAction — deterministic CI-parity gate with retry counter.

Runs four deterministic checks before done:
1. pre-commit run --all-files
2. commit title contract from latest commit subject
3. branch freshness versus origin/main
4. diary-in-diff parity based on the branch primary PR title policy

On any failure, stores diagnostics in context["validate_gate_output"] and
returns the configured retry event. Returns configured error event when
max_attempts is exhausted.
"""

import logging
import re
import subprocess
from typing import Any

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)

TITLE_PATTERN = re.compile(
    r"^(?P<type>feat|fix|chore|docs|refactor|test|ci|perf|style|build|revert)"
    r"(?:\([^)]+\))?: .+$"
)
TITLE_TYPE_PATTERN = re.compile(
    r"^(?P<type>feat|fix|chore|docs|refactor|test|ci|perf|style|build|revert)"
    r"(?:\([^)]+\))?:\s+"
)
FR_PATTERN = re.compile(r"FR-(\d+)")
PRIMARY_TITLE_SELECTOR = ".chaplain/lib/watcher/select_primary_pr_title.sh"


def _extract_title_type(title: str) -> str:
    match = TITLE_TYPE_PATTERN.match(title)
    return match.group("type") if match else ""


class ValidateGateAction(BaseAction):
    """Run deterministic quality gate checks with bounded retry semantics."""

    async def execute(self, context: dict[str, Any]) -> str:
        max_attempts = int(self.get_config_value("max_attempts", 5))
        success_event = self.get_config_value("success", "pass")
        retry_event = self.get_config_value("retry", "fix_needed")
        error_event = self.get_config_value("error", "error")
        cwd = self.get_config_value("cwd") or context.get("wt_dir", ".")
        machine_name = self.get_machine_name(context)

        attempt = int(context.get("validate_gate_attempt", 0))
        if attempt >= max_attempts:
            logger.error(
                f"[{machine_name}] Validate gate exceeded {max_attempts} attempts"
            )
            return error_event

        context["validate_gate_attempt"] = attempt + 1
        logger.info(
            f"[{machine_name}] Validate gate attempt {attempt + 1}/{max_attempts}"
        )

        failures: list[dict[str, str]] = []
        checks: list[dict[str, Any]] = []

        precommit_result = self._run(["pre-commit", "run", "--all-files"], cwd)
        precommit_output = self._combined_output(precommit_result).strip()
        context["precommit_output"] = precommit_output
        checks.append(
            {
                "name": "precommit",
                "returncode": precommit_result.returncode,
                "passed": precommit_result.returncode == 0,
            }
        )
        if precommit_result.returncode != 0:
            failures.append(
                {
                    "check": "precommit",
                    "reason": "pre-commit run --all-files failed",
                }
            )
            self._run(["git", "add", "-u"], cwd)

        title_result = self._run(["git", "log", "-1", "--format=%s"], cwd)
        commit_title = title_result.stdout.strip()
        title_type = ""
        checks.append(
            {
                "name": "commit_title",
                "returncode": title_result.returncode,
                "passed": False,
                "title": commit_title,
            }
        )
        if title_result.returncode != 0:
            failures.append(
                {
                    "check": "commit_title",
                    "reason": "failed to read latest commit subject",
                }
            )
        else:
            title_match = TITLE_PATTERN.match(commit_title)
            if not title_match:
                failures.append(
                    {
                        "check": "commit_title",
                        "reason": "title does not satisfy Conventional Commits contract",
                    }
                )
            else:
                title_type = title_match.group("type")
                checks[-1]["passed"] = True
                checks[-1]["type"] = title_type
                if title_type == "feat" and not FR_PATTERN.search(commit_title):
                    checks[-1]["passed"] = False
                    failures.append(
                        {
                            "check": "commit_title",
                            "reason": "feat title must include FR-XXX",
                        }
                    )

        primary_title_result = self._run(["bash", PRIMARY_TITLE_SELECTOR], cwd)
        primary_title = primary_title_result.stdout.strip()
        primary_title_type = ""
        checks.append(
            {
                "name": "primary_pr_title",
                "returncode": primary_title_result.returncode,
                "passed": False,
                "title": primary_title,
            }
        )
        if primary_title_result.returncode != 0 or not primary_title:
            failures.append(
                {
                    "check": "primary_pr_title",
                    "reason": "failed to select branch primary PR title",
                }
            )
        else:
            primary_title_type = _extract_title_type(primary_title)
            checks[-1]["passed"] = True
            checks[-1]["type"] = primary_title_type

        fetch_result = self._run(["git", "fetch", "origin", "main"], cwd)
        checks.append(
            {
                "name": "branch_freshness_fetch",
                "returncode": fetch_result.returncode,
                "passed": fetch_result.returncode == 0,
            }
        )
        if fetch_result.returncode != 0:
            failures.append(
                {
                    "check": "branch_freshness",
                    "reason": "git fetch origin main failed",
                }
            )

        ancestor_result = self._run(
            ["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"], cwd
        )
        checks.append(
            {
                "name": "branch_freshness_ancestor",
                "returncode": ancestor_result.returncode,
                "passed": ancestor_result.returncode == 0,
            }
        )
        if ancestor_result.returncode != 0:
            failures.append(
                {
                    "check": "branch_freshness",
                    "reason": "branch is behind origin/main (rebase or merge required)",
                }
            )

        diary_checked = primary_title_type in {"feat", "fix"}
        diary_passed = True
        diary_reason = "not_required"
        if diary_checked:
            fr_match = FR_PATTERN.search(primary_title)
            if fr_match:
                fr_num = fr_match.group(1)
                diff_result = self._run(
                    ["git", "diff", "--name-only", "origin/main...HEAD"], cwd
                )
                if diff_result.returncode != 0:
                    diary_passed = False
                    diary_reason = "failed to read diff against origin/main"
                    failures.append(
                        {
                            "check": "diary_parity",
                            "reason": diary_reason,
                        }
                    )
                else:
                    diary_pattern = re.compile(
                        rf"docs/diary/.*reflection.*fr-{fr_num}[^0-9]", re.IGNORECASE
                    )
                    changed_files = [
                        line.strip()
                        for line in diff_result.stdout.splitlines()
                        if line.strip()
                    ]
                    if any(diary_pattern.search(path) for path in changed_files):
                        diary_reason = "found"
                    else:
                        diary_passed = False
                        diary_reason = (
                            f"missing diary reflection for FR-{fr_num} in diff"
                        )
                        failures.append(
                            {
                                "check": "diary_parity",
                                "reason": diary_reason,
                            }
                        )
            else:
                diary_reason = "no_fr_reference"

        checks.append(
            {
                "name": "diary_parity",
                "passed": diary_passed,
                "checked": diary_checked,
                "reason": diary_reason,
            }
        )

        diagnostics = {
            "attempt": attempt + 1,
            "max_attempts": max_attempts,
            "commit_title": commit_title,
            "primary_pr_title": primary_title,
            "checks": checks,
            "failures": failures,
        }
        context["validate_gate_output"] = diagnostics

        if failures:
            logger.warning(
                f"[{machine_name}] Validate gate failed (attempt {attempt + 1}): "
                f"{failures}"
            )
            return retry_event

        logger.info(f"[{machine_name}] Validate gate passed")
        return success_event

    def _run(self, command: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603
            command,  # noqa: S607
            capture_output=True,
            text=True,
            cwd=cwd,
        )

    @staticmethod
    def _combined_output(result: subprocess.CompletedProcess[str]) -> str:
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        return f"{stdout}\n{stderr}"
