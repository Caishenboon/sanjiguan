# Signals / Inference research-baseline debt

These findings are deliberately unchanged:

- Legacy scores use binary floating point. Canonical output freezes their
  compatibility string representation; a later integer/Decimal design needs a
  new method and ruleset version.
- An empty Signal list with high completeness can become `contested` rather
  than `insufficient`; completeness is the legacy insufficiency gate.
- Equal-strength members of one independence group retain the first observed
  member, so the input order is semantically relevant.
- Candidate fill order depends on the frozen archetype asset order; final ties
  are deterministically broken by candidate ID.
- Research `past_life_nodes` are legacy preview structures, not a validated or
  production past-life algorithm.
- The current source fixtures do not implement raw evidence-to-Signal mapping.

No item above may be repaired by editing the frozen fixture. Resolution
requires product approval, a new version, and independent validation.

