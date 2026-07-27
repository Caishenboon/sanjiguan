# ADR 0009: physical three-coin mechanical engine

- Status: accepted for research implementation
- Method class: `traditional_mechanical`
- Production activatable: false

## Decision

Implement only the deterministic mechanics of a user-performed physical
three-coin cast inside `packages/sanji-engine`. Six tosses are recorded from
the first/bottom line to the top line. Each toss contains three explicit
integer values, each exactly 2 or 3. The engine never assigns meanings such as
heads/tails; the application must freeze and persist that mapping before
calling Engine API 1.0.

The line sums are frozen as 6 old yin, 7 young yang, 8 young yin, and 9 old
yang. Six and nine move. Keys are yin=0 and yang=1, always bottom-to-top.
Lines 1–3 form the lower trigram and lines 4–6 the upper trigram.

The received King Wen sequence/name/structure asset is versioned independently
and contains no judgment, line text, commentary, auspiciousness, timing, or
system-specific mapping. Sources are the public received-order text in
[Chinese Wikisource](https://zh.wikisource.org/zh/%E5%91%A8%E6%98%93) and the
[Unicode Yijing Hexagram Symbols chart](https://www.unicode.org/charts/PDF/U4DC0.pdf).

## Consequences

The engine is deterministic and replayable without Web, API, PostgreSQL,
network, or an LLM. Application code may map visible coin faces and persist
results, but may not calculate lines, trigrams, hexagrams, or sequence names.
Interpretive Yijing, automated casting, Six Signals mapping, and every other
unconfirmed divination module remain disabled.

