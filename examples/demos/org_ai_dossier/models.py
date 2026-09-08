"""FR-1029 typed contracts (judgement R-2) — Pydantic v2, ``extra="forbid"``.

Owner per field is documented in the FR § Typed contracts; here the types
and bounds are frozen. Ceilings (R-3) live alongside because every model
bound derives from them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# --- ceilings (R-3) -------------------------------------------------------------
MAX_REPOS = 400
MAX_PROJECTS = 150
MAX_TOP_PERSONS = 60
MAX_SYNTHESIS_CALLS = 2
N_CANARIES = 5  # 3 repo + 2 jira
MAX_LLM_CALLS = (
    MAX_REPOS + MAX_PROJECTS + MAX_TOP_PERSONS + MAX_SYNTHESIS_CALLS + N_CANARIES
)
MAX_API_CALLS_GITHUB = 4000
MAX_API_CALLS_JIRA = 400
MAX_MAP_FAILED = 5
MAX_ONEPAGER_WORDS = 800
ONEPAGER_FINDINGS = 3
CANARY_PREFIX = "__canary__/"

AIUsage = Literal["none", "product", "dev_tooling", "both", "unclear"]
ToolKind = Literal["provider", "framework", "coding_agent", "model"]
Visibility = Literal["public", "private", "internal"]


class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- collector bundles -----------------------------------------------------------


class Hit(Frozen):
    path: str = Field(min_length=1)
    line: str = Field(max_length=160)


class PRAuthor(Frozen):
    login: str = Field(min_length=1)
    bot: bool
    n: int = Field(ge=1)


class GitHubBundle(Frozen):
    id: str = Field(pattern=r"^[^/\s]+/[^/\s]+$")
    description: str | None
    pushed_at: datetime | None
    archived: bool
    visibility: Visibility | Literal[""]
    language: str | None
    readme_head: str = Field(max_length=3000)
    contributors: list[str] = Field(max_length=10)
    tree_truncated: bool
    instruction_files: list[str]
    manifest_hits: list[Hit] = Field(max_length=60)
    workflow_hits: list[Hit] = Field(max_length=30)
    pr_authors: list[PRAuthor] = Field(max_length=30)
    absent: list[str]

    def evidence_paths(self) -> set[str]:
        paths = {h.path for h in self.manifest_hits} | {
            h.path for h in self.workflow_hits
        }
        return paths | set(self.instruction_files)


class JiraPerson(Frozen):
    account_id: str = Field(min_length=1)
    display_name: str
    n: int = Field(ge=1)


class JiraLead(Frozen):
    account_id: str | None
    display_name: str | None


class JiraIssue(Frozen):
    key: str = Field(min_length=1)
    summary: str
    issuetype: str
    status: str
    assignee_id: str | None
    reporter_id: str | None
    description_head: str = Field(max_length=300)


class JiraBundle(Frozen):
    key: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    name: str
    project_type: str
    lead: JiraLead | None
    updated_in_window: int = Field(ge=0)
    created_in_window: int = Field(ge=0)
    ai_term_count: int = Field(ge=0)
    issues: list[JiraIssue] = Field(max_length=30)
    assignees: list[JiraPerson] = Field(max_length=10)
    reporters: list[JiraPerson] = Field(max_length=10)

    def issue_keys(self) -> set[str]:
        return {i.key for i in self.issues}


# --- model outputs (validated at the boundary) -----------------------------------


class RepoAITool(Frozen):
    name: str = Field(min_length=1)
    kind: ToolKind
    evidence_path: str = Field(min_length=1)


class JiraAITool(Frozen):
    name: str = Field(min_length=1)
    kind: ToolKind
    evidence_issue: str = Field(min_length=1)


class RepoClassification(Frozen):
    purpose: str
    ai_usage: AIUsage
    ai_tools: list[RepoAITool]
    rationale: str


class JiraClassification(Frozen):
    purpose: str
    ai_usage: AIUsage
    ai_tools: list[JiraAITool]
    rationale: str


# --- ledger rows -------------------------------------------------------------------


class RepoAIRow(Frozen):
    id: str
    activity: Literal["active"] = "active"
    pushed_at: datetime | None
    purpose: str
    ai_usage: AIUsage
    ai_tools: list[RepoAITool]
    search_keywords: list[str]
    contributors: list[str]
    status: Literal["classified", "map_failed"]


class JiraAIRow(Frozen):
    key: str
    activity: Literal["active"] = "active"
    purpose: str
    ai_usage: AIUsage
    ai_tools: list[JiraAITool]
    updated_in_window: int
    ai_term_count: int
    status: Literal["classified", "map_failed"]


class PersonRow(Frozen):
    id: str = Field(pattern=r"^(github:[^\s:]+|jira:[^\s:]+)$")
    label: str
    source: Literal["github", "jira"]
    repos: list[str]
    projects: list[str]
    score: int = Field(ge=1)
    rank: int = Field(ge=1)
    summary: str | None = None


class AIToolRow(Frozen):
    name: str
    kind: ToolKind
    n_repos: int = Field(ge=0)
    n_projects: int = Field(ge=0)
    evidence: list[str]


class CoverageGitHub(Frozen):
    api_total: int | None
    listed: int
    archived: int
    out_of_window: int
    visibility_rejected: int
    active: int
    extracted: int
    classified: int
    unclear: int
    map_failed: int
    tree_truncated: int
    search_caveats: list[str]


class CoverageJira(Frozen):
    visible: int
    active: int
    dormant: int
    extracted: int
    classified: int
    unclear: int
    map_failed: int
    page_cap_hit: bool


class CoverageRecord(Frozen):
    github: CoverageGitHub
    jira: CoverageJira


class RunRecord(Frozen):
    run_id: str
    started: datetime
    finished: datetime
    org: str
    window_days: int
    visibility: list[str]
    persons_llm: bool
    persons_llm_ack: str | None
    head_sha: str
    graph_sha256: str
    provider: Literal["azure"] = "azure"
    deployment: str
    prompt_versions: dict[str, str]
    api_calls_estimated: int
    api_calls_actual: int
    llm_calls_estimated: int
    llm_calls_actual: int
    coverage: CoverageRecord
    artifact_sha256: dict[str, str]
    canaries: dict[str, Literal["pass"]]
