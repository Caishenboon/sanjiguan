# Yijing physical three-coin mechanical Sprint

## Delivered

- PR #8 was merged by ordinary Merge Commit as
  `359e26a1dc45cab8717ad3220b8705d70f519973`; post-merge
  [main CI passed](https://github.com/Caishenboon/sanjiguan/actions/runs/30249992899).
- A standalone physical three-coin mechanical module in `sanji-engine`.
- Versioned 64-entry received King Wen mapping with integrity hash.
- Per-line and lookup Trace, domain hashes, Replay, and revoked-rule replay.
- Existing physical record/API reused through a thin face-to-number adapter.
- Additive database columns for native Engine results and manifests; no legacy
  backfill.
- Owner research preview that reads persisted Engine output without
  recalculation.
- Ubuntu/Windows deterministic fixture and full 4096-state enumeration.
- CI matrix commands are separate fail-fast steps. This closes an inherited
  workflow defect where a failed Windows unittest command could be masked by a
  later successful gate in the same multiline step.

## Acceptance commands

```text
python -m unittest tests.test_sanji_engine_yijing -v
python scripts/validate_sanji_engine.py
python scripts/check_secrets.py
python scripts/check_doc_links.py
```

The page states: “本页面只呈现实物投掷形成的确定性卦象，不提供正式断语。”

## Explicit exclusions

No software-random toss, automatic casting, judgment text, line text,
auspiciousness, timing, DeepSeek interpretation, past-life mapping, bardo,
relationship scoring, Bazi, Ziwei, formal Six Signals weighting, or life
chart was implemented.
