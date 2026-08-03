"""BaZi conformance and explicit research-only mechanical four pillars.

This package is intentionally not re-exported from :mod:`sanji_engine`.  The
application-facing Engine API remains the four functions declared in API 1.0.
"""

from .conformance import (
    ConformanceError,
    compare_profiles,
    list_profiles,
    load_boundary_cases,
    load_evidence_bundle,
    load_profile,
    run_conformance,
    validate_profile,
)
from .four_pillars import calculate_four_pillars
from .traditional_structure import calculate_traditional_structure
from .profiles import (
    REGISTRY_VERSION as EXECUTION_PROFILE_REGISTRY_VERSION,
    execution_profile_registry,
    load_execution_profile,
)

__all__ = [
    "ConformanceError",
    "compare_profiles",
    "list_profiles",
    "load_boundary_cases",
    "load_evidence_bundle",
    "load_profile",
    "run_conformance",
    "validate_profile",
    "calculate_four_pillars",
    "calculate_traditional_structure",
    "execution_profile_registry",
    "load_execution_profile",
    "EXECUTION_PROFILE_REGISTRY_VERSION",
]
