"""Transparent aggregate baselines for research protocol conformance."""
from __future__ import annotations

import random
from collections import Counter, defaultdict


def _rate_bp(successes: int, total: int) -> int:
    return (successes * 10_000) // total if total else 0


def evaluate_binary_protocol(records: list[dict], *, seed: int, permutations: int = 100) -> dict:
    """Compare a declared binary rule with base-rate and stratified permutations.

    Records contain only opaque labels: ``prediction``, ``outcome`` and
    ``stratum``.  This function never derives or changes a ruleset.
    """
    if not records or permutations < 1:
        raise ValueError("records_and_permutations_required")
    ordered = sorted(records, key=lambda value: value["record_id"])
    actual = sum(value["prediction"] == value["outcome"] for value in ordered)
    outcomes = Counter(value["outcome"] for value in ordered)
    common = sorted(outcomes.items(), key=lambda value: (-value[1], value[0]))[0][0]
    base = sum(value["outcome"] == common for value in ordered)
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, value in enumerate(ordered):
        grouped[str(value["stratum"])].append(index)
    rng = random.Random(seed)
    permuted_rates: list[int] = []
    for _ in range(permutations):
        shuffled = [value["prediction"] for value in ordered]
        for indices in grouped.values():
            values = [shuffled[index] for index in indices]
            rng.shuffle(values)
            for index, value in zip(indices, values):
                shuffled[index] = value
        permuted_rates.append(_rate_bp(
            sum(shuffled[index] == value["outcome"] for index, value in enumerate(ordered)),
            len(ordered),
        ))
    sorted_rates = sorted(permuted_rates)
    return {
        "schema_version": "research-evaluation/1.0.0",
        "asset_class": "synthetic_conformance",
        "seed": seed,
        "permutation_count": permutations,
        "sample_count": len(ordered),
        "declared_rule_accuracy_bp": _rate_bp(actual, len(ordered)),
        "base_rate_accuracy_bp": _rate_bp(base, len(ordered)),
        "permutation_median_accuracy_bp": sorted_rates[len(sorted_rates) // 2],
        "permutation_interval_bp": {
            "lower": sorted_rates[(len(sorted_rates) * 25) // 1000],
            "upper": sorted_rates[min(len(sorted_rates) - 1, (len(sorted_rates) * 975) // 1000)],
        },
        "effect_direction": (
            "above_permutation_median"
            if _rate_bp(actual, len(ordered)) > sorted_rates[len(sorted_rates) // 2]
            else "not_above_permutation_median"
        ),
        "claims": {
            "predictive_power_established": False,
            "causality_established": False,
            "ruleset_auto_promotion_allowed": False,
        },
    }
