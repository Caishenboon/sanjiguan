# Third-party integration matrix

| Integration | Boundary | Data allowed | Engine/hash impact | CI | Production |
|---|---|---|---|---|---|
| lunar-python 1.4.8 | `packages/oracle-adapters` | Synthetic or explicitly approved research input | None | Required Oracle matrix | Forbidden |
| tyme4py 1.5.0 | `packages/oracle-adapters` | Synthetic or explicitly approved research input | None | Required Oracle matrix | Forbidden |
| sxtwl 2.0.7 | `packages/oracle-adapters` | Synthetic or explicitly approved research input | None | Required on Linux | Forbidden |
| iztro 2.5.8 | isolated Node runner | Synthetic or explicitly approved research input | None | Required Oracle matrix | Forbidden |
| Radix/Motion/Lucide | `packages/sanji-ui` | Rendered props only | None | Build, a11y, visual | UI runtime |
| Storybook 10.5.5 | `packages/sanji-ui` | Synthetic stories only | None | Required build | Forbidden |
| Playwright 1.62.0 | `apps/web/tests/visual` | Synthetic page fixtures only | None | Required Chromium matrix | Forbidden |
| Lighthouse CI 0.15.1 | `apps/web` | Public synthetic routes only | None | Required budgets | Forbidden |

Oracle output is differential evidence. It is not inserted into Engine Domain,
Trace, Output hash, replay decisions, ranking, or production evidence. A
difference returns a bounded status and reasons for human review; there is no
majority vote and no automatic Profile mutation.

Upgrades require an explicit lock change, license review, normalized fixture
diff, and rollback proof. Unpinned upgrades fail the third-party gate.
