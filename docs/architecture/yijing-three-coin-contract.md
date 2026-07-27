# Physical three-coin mechanical contract

## Input

- `operation`: `cast_physical_three_coin`
- `method_id`: `YIJING.THREE_COIN.PHYSICAL.MECHANICAL.V1`
- `method_version`: `1.0.0`
- `input_order`: `bottom_to_top`
- six ordered tosses with `line_position` 1–6
- every toss has exactly three integer `coin_values`, each 2 or 3

The application mapping is separately frozen as
`COIN_FACES.HEADS_3_TAILS_2.V1@1.0.0`. Raw face labels, numeric values, mapping
ID, and mapping version are persisted. Old records lacking a complete mapping
are `legacy_method_unknown` and are not back-calculated.

## Mechanical result

| Sum | State | Base | Moving | Transformed |
|---:|---|---:|---|---:|
| 6 | old_yin | 0 | yes | 1 |
| 7 | young_yang | 1 | no | 1 |
| 8 | young_yin | 0 | no | 0 |
| 9 | old_yang | 1 | yes | 0 |

Both the base and transformed six-bit keys run from bottom to top. An
unchanging cast still returns a complete transformed structure, with
`moving_lines=[]` and `has_transformed_hexagram=false`.

The ruleset is `yijing-three-coin-mechanical-0.1.0`, `research_active`,
`traditional_mechanical`, and explicitly non-production. Engine API remains
limited to `validate_request`, `execute`, `replay`, and `inspect_ruleset`.

Trace contains one derivation step per line plus one assembly/asset-lookup
step. Replay freezes method, ruleset, mapping asset, input, trace, and domain
result hashes. Revoked assets cannot create new runs but remain eligible for
historical replay while retained.

