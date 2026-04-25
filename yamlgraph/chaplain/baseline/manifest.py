"""Manifest schema validation for baseline checkpointing."""

from typing import Any, Dict, List


def validate_manifest_schema(manifest_data: Dict[str, Any]) -> bool:
    """
    Validate manifest schema with glob support (pattern), explicit mode, and exclude support.
    
    Args:
        manifest_data: Dictionary containing manifest configuration
        
    Returns:
        bool: True if manifest is valid
        
    Raises:
        ValueError: If manifest schema is invalid
    """
    required_fields = ["manifest_version", "sources"]
    
    # Check required top-level fields
    for field in required_fields:
        if field not in manifest_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate manifest version
    if not isinstance(manifest_data["manifest_version"], int):
        raise ValueError("manifest_version must be an integer")
        
    # Validate sources
    sources = manifest_data["sources"]
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")
        
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Source {i} must be a dictionary")
            
        # Check required source fields
        if "pattern" not in source:
            raise ValueError(f"Source {i} missing required field: pattern")
        if "mode" not in source:
            raise ValueError(f"Source {i} missing required field: mode")
            
        # Validate mode values
        valid_modes = ["verbatim", "summarized"]
        if source["mode"] not in valid_modes:
            raise ValueError(f"Source {i} mode must be one of: {valid_modes}")
    
    # Validate exclude field if present
    if "exclude" in manifest_data:
        exclude = manifest_data["exclude"]
        if not isinstance(exclude, list):
            raise ValueError("exclude must be a list")
        for i, pattern in enumerate(exclude):
            if not isinstance(pattern, str):
                raise ValueError(f"exclude[{i}] must be a string")
    
    return True