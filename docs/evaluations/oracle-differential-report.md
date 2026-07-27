# Oracle differential verification

## Scope and authority

All inputs in this report are synthetic. Oracle output is differential evidence
only: it cannot alter an Engine result, hash, Profile, Ruleset, Trace, ranking,
or production evidence. A match is evidence of mechanical agreement under the
tested inputs, not proof that a traditional method is authoritative.

## BaZi matrix

`packages/oracle-adapters/fixtures/bazi-differential-matrix.json` defines ten
boundary classes, three explicit BaZi Profiles, and three pinned Oracles. CI
therefore exercises 90 adapter combinations:

- ordinary modern date;
- both sides of the Start of Spring boundary;
- a solar-month boundary;
- civil midnight and late Zi hour;
- an apparent-solar-time cross-day candidate;
- an IANA DST fold and gap;
- unknown birth time.

Unresolved DST fold/gap inputs and unknown time are intentionally
`unsupported`; adapters do not guess an instant. On Linux CI, all three
Oracles must actually execute for the seven resolved-time cases. On Windows,
the sxtwl wheel/build may be unavailable, so local Windows evidence records
that adapter as `unsupported`; this exception is not allowed in the Linux CI
job.

Expected Linux execution totals are 63 successful Oracle executions and 27
structured unsupported results. Differences are classified using the closed
status set in the Oracle contract. The matrix never votes on which Profile is
correct and never rewrites a golden hash.

## Ziwei matrix

The pinned iztro 2.5.8 adapter executes one synthetic manually verified lunar
case. The normalized comparison covers life palace, body palace, five-element
bureau, and all fourteen major-star positions. The current fixture is
`normalized_match`. Four transformations, leap-month policy, hour boundary,
decade direction, and authoritative traditional correctness remain subjects
for manual D-005 review.

## Reproduction

```text
python -m unittest tests.test_oracle_adapters -v
```

CI installs lunar-python 1.4.8, tyme4py 1.5.0, and sxtwl 2.0.7 in the
PostgreSQL 16 Linux job, installs iztro 2.5.8 in its isolated Node directory,
then runs this command without a skip path.
