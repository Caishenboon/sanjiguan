# Ziwei, Oracle, and UI inventory

## Existing and reusable

- `packages/sanji-engine/src/sanji_engine/public.py`: four-entry public API,
  deterministic hashes, Trace, and Replay.
- `packages/sanji-engine/src/sanji_engine/calendar`: IANA historical time,
  solar-time correction, and solar-term foundation.
- `packages/sanji-engine/src/sanji_engine/bazi`: explicit Profiles and
  research-only four-pillar execution.
- `packages/sanji-engine/src/sanji_engine/yijing`: physical three-coin
  mechanical engine.
- `apps/api/app/bazi_research_routes.py`: owner-only engine adapter and
  encrypted persistence pattern.
- `apps/web/app`: responsive research pages and PWA shell to migrate onto
  shared UI components.

## Missing before this Sprint

- Ziwei had only a disabled package boundary; D-005, leap-month handling,
  Zi-hour handling, four transformations, and authoritative golden cases were
  not frozen.
- There was no external differential contract or pinned third-party registry.
- UI patterns were page-local and lacked Storybook, fixed visual snapshots,
  and a single token contract.

## Migration and exclusions

Page-local badges, warnings, evidence cards, hash rows, and research navigation
move into `packages/sanji-ui`. Application pages consume components; they do
not contain algorithm branches or scoring constants.

Ziwei interpretation, personality, auspiciousness, star-combination prose,
past-life, bardo, relationship scoring, six-signal inference, K-line, and
DeepSeek prose are excluded. The two Ziwei Profiles are explicit research
candidates, not a claim that D-005 or one unified tradition has been frozen.
