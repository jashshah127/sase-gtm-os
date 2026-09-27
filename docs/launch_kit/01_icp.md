# Prisma Browser: ideal customer profile

*Derived from the synthetic dataset in this project. Replace with CRM data before field use.*

## Who buys first

Early Prisma Browser adopters (81 accounts that bought before the March 2026 relaunch) differ from the firewall base in consistent ways. The strongest signals, in order of lift:

| Attribute | Value | Share of base | Share of early adopters | Lift | ICP points |
|---|---|---|---|---|---|
| Contractor share | 25% or more | 1.0% | 4.9% | 5.19x | 30 |
| Segment | Large Enterprise | 6.8% | 16.0% | 2.37x | 15 |
| Prisma Access | Customer | 25.2% | 45.7% | 1.81x | 10 |
| Industry | Technology | 11.8% | 19.8% | 1.67x | 10 |
| Unmanaged devices | 25 to 35% | 14.5% | 22.2% | 1.53x | 5 |
| VDI | Runs VDI | 33.5% | 50.6% | 1.51x | 5 |
| Industry | Financial Services | 15.6% | 22.2% | 1.42x | 5 |
| Contractor share | 15 to 25% | 22.3% | 30.9% | 1.38x | 5 |
| Industry | Healthcare | 13.0% | 16.0% | 1.23x | 5 |
| Industry | Professional Services | 8.1% | 9.9% | 1.22x | 5 |
| Industry | Education | 6.2% | 7.4% | 1.20x | 5 |
| Industry | Telecommunications | 7.4% | 8.6% | 1.17x | 5 |

In plain terms: the buyer has a large contractor or third-party workforce, many unmanaged devices, often a VDI estate that exists mainly to give those users browser access, and usually already runs Prisma Access. Regulated and knowledge-work industries lead.

## Tiers

Points come from lift (12 x log2 of lift, rounded to 5, capped at 30). Tier A is a score of 20 or more; Tier B is 10 or more.

| Tier | Accounts | Early adoption rate | Post-launch opps per 100 accounts | Post-launch win rate |
|---|---|---|---|---|
| A | 1,114 | 3.6% | 20.4 | 46% |
| B | 1,628 | 1.9% | 7.1 | 14% |
| C | 1,458 | 0.7% | 3.3 | 9% |

## Does it hold up?

The scorecard was built only from pre-relaunch adopters, then checked against deals created after March 23, 2026. Tier A generated 20.4 opportunities per 100 accounts against 3.3 for Tier C, and won 56 of the 69 post-launch deals. That out-of-time check is what makes the ICP usable for routing, not just descriptive.

## How to use it

- Tier A: route to SASE specialists and SEs for a proactive POV offer; lead with the contractor or VDI use case.
- Tier B: partner-led and marketing programs; qualify on contractor volume and AI usage policy first.
- Tier C: nurture. Do not spend SE time without a named use case.
- Refresh the points after 100 or more post-launch wins; early-adopter samples are small.

## Watch-outs

- A fully managed device fleet with few contractors is a weak fit even in a strong industry.
- VDI signals are strongest where VDI exists mainly for browser-based apps; heavy desktop-app VDI is a different sale.
