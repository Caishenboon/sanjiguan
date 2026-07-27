"""BaZi method-profile conformance only; pillar calculation stays disabled.

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

__all__ = [
    "ConformanceError",
    "compare_profiles",
    "list_profiles",
    "load_boundary_cases",
    "load_evidence_bundle",
    "load_profile",
    "run_conformance",
    "validate_profile",
]
