# vulture_whitelist.py — Vulture false-positive suppressions.
#
# Vulture scans yamlgraph/ but not tests/ or external callers.
# Items here are either:
#   (a) invoked by frameworks (Pydantic, LangChain, LangGraph, MCP)
#   (b) used only in tests/ or scripts/ (invisible to vulture)
#   (c) invoked dynamically (python3 -c, decorators)

# --- worktree_helpers: invoked via python3 -c in scripts/enforce_worktree.sh ---
from yamlgraph.utils.worktree_helpers import (  # noqa: F401 (CONF-126)
    construct_worktree_path,
    derive_branch_name,
    validate_clean_working_tree,
)

derive_branch_name
construct_worktree_path
validate_clean_working_tree

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
from yamlgraph.constants import EdgeType, SpecialNodes  # noqa: F401 (CONF-126)

EdgeType.SIMPLE
EdgeType.CONDITIONAL
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
    CheckpointConfig,
    DefaultsConfig,
    NodeConfig,
)

NodeConfig.model_config
NodeConfig.fallback
CheckpointConfig.backend
DefaultsConfig.model_config

# --- Pydantic validators: called automatically by framework ---
NodeConfig.validate_thinking_budget
NodeConfig.validate_node_requirements
DefaultsConfig.validate_defaults_thinking_budget
GraphConfig.validate_router_targets
GraphConfig.validate_edge_nodes

# --- schemas.py: Pydantic fields accessed in tests ---
from yamlgraph.models.schemas import (  # noqa: F401 (CONF-126)
    CopilotResult,
    GenericReport,
    PipelineError,
)

PipelineError.details
GenericReport.sections
GenericReport.recommendations
CopilotResult.exit_code
CopilotResult.backend

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
