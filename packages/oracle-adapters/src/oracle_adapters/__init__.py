"""Research-only external Oracle contract.

This package may depend on third-party projects. ``sanji_engine`` must never
import it, and Oracle output must never enter an Engine domain or output hash.
"""

from .common.contract import (
    diff_against_engine,
    execute_oracle,
    identify_oracle,
    inspect_oracle,
    normalize_oracle_output,
    validate_oracle_input,
)

__all__ = [
    "identify_oracle",
    "validate_oracle_input",
    "execute_oracle",
    "normalize_oracle_output",
    "diff_against_engine",
    "inspect_oracle",
]
