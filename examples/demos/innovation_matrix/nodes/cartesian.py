"""Cartesian product tool for Innovation Matrix.

Creates one capability × constraint pair per grid cell.
"""

from itertools import product


def cartesian_product(state: dict) -> dict:
    """Generate every capability × constraint pair.

    Args:
        state: Must contain 'dimensions' with 'capabilities' and 'constraints' lists
               (dimensions can be dict or Pydantic model)

    Returns:
        dict with 'pairs' list of {capability, constraint, id} dicts

    Raises:
        ValueError: If either dimension is empty.
    """
    dimensions = state.get("dimensions", {})

    # Handle both dict and Pydantic model access
    if hasattr(dimensions, "capabilities"):
        capabilities = dimensions.capabilities
        constraints = dimensions.constraints
    else:
        capabilities = dimensions.get("capabilities", [])
        constraints = dimensions.get("constraints", [])

    if not capabilities or not constraints:
        raise ValueError(
            f"Innovation Matrix needs both dimensions: got {len(capabilities)} "
            f"capabilities and {len(constraints)} constraints"
        )

    n_constraints = len(constraints)
    pairs = []
    for i, (cap, con) in enumerate(product(capabilities, constraints)):
        pairs.append(
            {
                "id": f"C{i // n_constraints + 1}S{i % n_constraints + 1}",
                "capability": cap,
                "constraint": con,
            }
        )

    return {"pairs": pairs}
