"""State management for baseline integration."""

from typing import Dict, Any


def build_baseline_state(baseline_data: Dict[str, Any], existing_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build baseline state while enforcing namespace collision protection.
    
    Args:
        baseline_data: Baseline data to integrate
        existing_state: Existing state that might have collisions
        
    Returns:
        Dict[str, Any]: Merged state with baseline data
        
    Raises:
        ValueError: If baseline_* namespace collision is detected
    """
    # Check for namespace collisions
    for key in baseline_data.keys():
        if key.startswith("baseline_") and key in existing_state:
            raise ValueError("baseline namespace collision")
    
    # Merge states (baseline is additive)
    merged_state = existing_state.copy()
    merged_state.update(baseline_data)
    
    return merged_state