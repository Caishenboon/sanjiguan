# Third-party integration matrix

| Integration | Boundary | Data allowed | Engine/hash impact | CI | Production |
|---|---|---|---|---|---|
| lunar-python 1.4.8 | `packages/upstream-adapters` | Owner-authorized birth input | Adapter and upstream-composite hashes | 60 adapter cases | Research runtime |
| tyme4py 1.5.0 | `packages/oracle-adapters` | Synthetic or explicitly approved research input | None | Required Oracle matrix | Forbidden |
| sxtwl 2.0.7 | `packages/oracle-adapters` | Synthetic or explicitly approved research input | None | Required on Linux | Forbidden |
| iztro 2.5.8 | isolated local Node runner | Owner-authorized verified lunar input | Adapter and upstream-composite hashes | 48 adapter cases | Research runtime |
| liuyao-engine 0.1.0 | unmodified selected-file snapshot | Owner-entered 6/7/8/9 lines and day-stem index | Adapter and upstream-composite hashes | 4096 cases | Research runtime |
| najia 2.0.1 | `packages/oracle-adapters` | Synthetic differential cases only | None | Differential only | Forbidden |
| Radix/Motion/Lucide | `packages/sanji-ui` | Rendered props only | None | Build, a11y, visual | UI runtime |
| Storybook 10.5.5 | `packages/sanji-ui` | Synthetic stories only | None | Required build | Forbidden |
| Playwright 1.62.0 | `apps/web/tests/visual` | Synthetic page fixtures only | None | Required Chromium matrix | Forbidden |
| Lighthouse CI 0.15.1 | `apps/web` | Public synthetic routes only | None | Required budgets | Forbidden |

Legacy Oracle output remains differential evidence. It is not inserted into Engine Domain,
Trace, Output hash, replay decisions, ranking, or production evidence. A
difference returns a bounded status and reasons for human review; there is no
majority vote and no automatic Profile mutation.

The separately admitted upstream adapters are version-pinned mechanical fact
providers. Their outputs enter only `sanji-upstream-composite-1.0.0`, retain
source identity and disputes, and receive zero interpretive Strength and
Confidence until a reviewed mapping exists. Mechanical facts are never
silently converted into fortune, timing, useful-god, pattern, or verdict.

Upgrades require an explicit lock change, license review, normalized fixture
diff, and rollback proof. Unpinned upgrades fail the third-party gate.
