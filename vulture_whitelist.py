# vulture_whitelist.py — Vulture false-positive suppressions.
#
# Vulture scans yamlgraph/ but not tests/ or external callers.
# Items here are either:
#   (a) invoked by frameworks (Pydantic, LangChain, LangGraph, MCP)
#   (b) used only in tests/ or scripts/ (invisible to vulture)
#   (c) invoked dynamically (python3 -c, decorators)

# --- worktree_helpers: invoked via python3 -c in scripts/enforce_worktree.sh ---
from yamlgraph.utils.worktree_helpers import (  # noqa: F401 (CONF-126)
    clean_stale_pth_entries,
    construct_worktree_path,
    derive_branch_name,
    validate_clean_working_tree,
    validate_editable_install,
    validate_venv_health,
    validate_venv_symlink,
)

derive_branch_name
construct_worktree_path
validate_clean_working_tree
validate_venv_health
validate_venv_symlink
clean_stale_pth_entries
validate_editable_install

# --- cli/deprecation: tested in test_deprecation.py ---
from yamlgraph.cli.deprecation import (  # noqa: F401 (CONF-126)
    deprecated_command,
    get_replacement_command,
)

get_replacement_command
deprecated_command

# --- config: constants tested in test_config.py ---
from yamlgraph.config import (  # noqa: F401 (CONF-126)
    DANGEROUS_PATTERNS,
    DEFAULT_GRAPH,
    DEFAULT_RECURSION_LIMIT,
    GRAPHS_DIR,
    MAX_TOPIC_LENGTH,
    MAX_WORD_COUNT,
    MIN_WORD_COUNT,
    PACKAGE_ROOT,
    VALID_STYLES,
)

PACKAGE_ROOT
GRAPHS_DIR
DEFAULT_GRAPH
DEFAULT_RECURSION_LIMIT
MAX_TOPIC_LENGTH
MAX_WORD_COUNT
MIN_WORD_COUNT
VALID_STYLES
DANGEROUS_PATTERNS

# --- constants: enum members tested in test_constants.py ---
from yamlgraph.constants import (  # noqa: F401 (CONF-126)
    EdgeType,
    NodeType,
    SpecialNodes,
)

EdgeType.SIMPLE
EdgeType.CONDITIONAL
NodeType.PIPELINE
SpecialNodes.START

# --- contrib/progress: methods used in examples and tests ---
from yamlgraph.contrib.progress import SkipReport  # noqa: F401 (CONF-126)

SkipReport.from_state
SkipReport.log
SkipReport.to_dict

# --- graph_loader: attribute used in map_compiler and linter ---
from yamlgraph.models.graph_schema import (  # noqa: F401 (CONF-126)
    GraphConfig,
    SubgraphNodeConfig,
)

GraphConfig.max_map_items

# --- graph_loader: public API used by MCP/A2A servers (FR-255) ---
from yamlgraph.graph_loader import invoke_graph  # noqa: F401 (CONF-126)

invoke_graph

# --- linter: Pydantic model field ---
from yamlgraph.linter.graph_linter import LintResult  # noqa: F401 (CONF-126)

LintResult.file

# --- mcp_server: handlers registered via @server decorators ---
from yamlgraph.mcp_server import (  # noqa: F401 (CONF-126)
    handle_call_tool,
    handle_list_tools,
)

handle_list_tools
handle_call_tool

# --- Pydantic model_config: framework introspection ---
SubgraphNodeConfig.model_config
GraphConfig.model_config

from yamlgraph.models.graph_schema import (  # noqa: F401 (CONF-126)
    CacheConfig,
    CheckpointConfig,
    DefaultsConfig,
    NodeConfig,
    PostGuardRule,
    VerificationConfig,
)

NodeConfig.model_config
NodeConfig.cache
NodeConfig.fallback
NodeConfig.verification
CacheConfig.ttl
CheckpointConfig.backend
DefaultsConfig.model_config

# --- Pydantic validators: called automatically by framework ---
NodeConfig.validate_timeout
NodeConfig.validate_thinking_budget
NodeConfig.validate_node_requirements
NodeConfig.parse_cache
NodeConfig.parse_verification
NodeConfig.parse_guards
PostGuardRule.validate_retry_fields
VerificationConfig.validate_on_fail
DefaultsConfig.validate_defaults_thinking_budget
GraphConfig.validate_router_targets
GraphConfig.validate_edge_nodes

# --- schemas.py: Pydantic fields accessed in tests ---
from yamlgraph.models.schemas import (  # noqa: F401 (CONF-126)
    CopilotResult,
    GenericReport,
    PipelineError,
    VerificationViolation,
)

PipelineError.details
GenericReport.sections
GenericReport.recommendations
CopilotResult.exit_code
CopilotResult.backend
VerificationViolation.prediction
VerificationViolation.actual
VerificationViolation.check_type

# --- storage: LangGraph BaseCheckpointSaver interface methods ---
from yamlgraph.storage.checkpointer_factory import (  # noqa: F401 (CONF-126)
    shutdown_checkpointers,
)

shutdown_checkpointers

from yamlgraph.storage.simple_redis import (  # noqa: F401 (CONF-126)
    SimpleRedisCheckpointer,
)

SimpleRedisCheckpointer.aget_tuple
SimpleRedisCheckpointer.aput
SimpleRedisCheckpointer.alist
SimpleRedisCheckpointer.aput_writes
SimpleRedisCheckpointer.adelete_thread
SimpleRedisCheckpointer.get_tuple
SimpleRedisCheckpointer.put
SimpleRedisCheckpointer.put_writes
SimpleRedisCheckpointer.delete_thread

# --- llm_factory: litellm global config ---
import litellm  # noqa: F401 (CONF-126)

litellm.drop_params

# --- token_tracker: LangChain callback interface method ---
from yamlgraph.utils.token_tracker import TokenTracker  # noqa: F401 (CONF-126)

TokenTracker.on_llm_end

# --- verification: CountRangeClaim exported for public API (FR-166) ---
from yamlgraph.verification import CountRangeClaim  # noqa: F401 (CONF-126)

CountRangeClaim
CountRangeClaim.validate_range  # Pydantic @model_validator

# --- id_registry: FR-180 plan-phase ID reservation, called from scripts ---
from yamlgraph.utils.id_registry import (  # noqa: F401 (CONF-126)
    PRE_EXISTING_MAX_CAP,
    PRE_EXISTING_MAX_REQ,
    format_cap_id,
    format_req_id,
    load_registry,
    reserve_ids,
    save_registry,
    validate_registry,
)

PRE_EXISTING_MAX_CAP
PRE_EXISTING_MAX_REQ
load_registry
reserve_ids
save_registry
validate_registry
format_cap_id
format_req_id

# --- a2a_server: public API tested in test_a2a_server.py (FR-208, FR-250) ---
from yamlgraph.a2a_server import (  # noqa: F401 (CONF-126)
    YAMLGraphAgentExecutor,
    build_agent_card,
    create_a2a_app,
    extract_text_from_parts,
    map_pipeline_error,
    parse_a2a_message,
)

build_agent_card
create_a2a_app
extract_text_from_parts
map_pipeline_error
parse_a2a_message
YAMLGraphAgentExecutor._format_result

# --- a2a_message: helpers re-exported via a2a_server, tested (FR-250) ---
from yamlgraph.a2a_message import (  # noqa: F401 (CONF-126)
    _detect_interrupt,
    _extract_interrupt_payload,
)

_detect_interrupt
_extract_interrupt_payload

# --- discovery: shared module used by mcp_server and a2a_server ---
# (discover_graphs is re-imported by mcp_server and a2a_server)
# --- a2a_commands: CLI dispatch registered in cli/__init__.py ---
from yamlgraph.cli.a2a_commands import cmd_a2a_dispatch  # noqa: F401 (CONF-126)
from yamlgraph.discovery import (  # noqa: F401 (CONF-126)
    DEFAULT_GRAPH_PATTERNS,
    discover_graphs,
)

cmd_a2a_dispatch

# --- timing_tracker: LangChain callback methods invoked by framework ---
from yamlgraph.utils.timing_tracker import (  # noqa: F401 (CONF-126)
    ExecutionTimingCallbackHandler,
)

ExecutionTimingCallbackHandler.on_llm_start

from yamlgraph.linter.checks_contracts import (
    check_python_node_variables,  # noqa: F401 (API stub for FR-252 compat)
)
from yamlgraph.utils.fsm.action import (  # noqa: F401 (CONF-126)
    ActionConfig,
    run_legacy_yamlgraph_async,
)

check_python_node_variables
run_legacy_yamlgraph_async
ActionConfig._normalize_event_map  # Pydantic @field_validator; invoked by framework
ActionConfig._coerce_variable_values  # Pydantic @field_validator; invoked by framework
ActionConfig.failure  # Pydantic field with AliasChoices; read via attribute access

# --- graph_schema: Pydantic fields accessed via alias or YAML key only ---
from yamlgraph.models.graph_schema import NodeConfig  # noqa: F401 (CONF-126)

NodeConfig.schema_ref  # Pydantic field with alias="schema"; accessed via YAML key
NodeConfig.outputs  # Alias for output; used in passthrough node fixtures
