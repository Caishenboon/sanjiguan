# Signals / Inference research baseline architecture

The migrated behavior is an engineering `research_baseline`, not an
authoritative golden standard, a traditional system, or a production Six
Signals algorithm. Its ruleset is `production_activatable: false`.

The application owns authentication, consent, authorization, PostgreSQL,
HTTP, presentation, and optional prose generation. Its legacy entry point is
now a thin presentation adapter calling `sanji_engine.execute()`. Signal
validation, independence-group deduplication, candidate generation,
contribution scoring, counterevidence, conflicts, ranking, status, research
nodes, canonical results, Trace, and Replay live only in `sanji-engine`.

```text
API / persistence / presentation / DeepSeek prose
                    |
          legacy presentation adapter
                    |
        Engine API 1.0: execute/replay
                    |
     signals -> inference -> Trace -> hashes
```

DeepSeek is outside the dependency graph and cannot change any locked field or
participate in hashes. All unconfirmed traditional and product-domain modules
continue to return `MODULE_DISABLED`.

The frozen assets retain their pre-migration order and values. Equal
deduplication candidates keep first-seen order; final candidate ordering is
`raw_score` descending followed by candidate ID. These are compatibility facts,
not an endorsement of the research theory.

