# Heuristic Value Rationale

This document records the reasoning behind every mapping table in the ecommerce assumptions skill (`SKILL.md`). Each entry explains why a specific numeric value was chosen, what sources informed the decision, and when it was last reviewed.

**Purpose:** Audit trail and provenance for the team. Cross-reference this with `SKILL.md` step numbers when reviewing or updating heuristics.

**Last comprehensive review:** 2026-03-02

**Source categories:**
- **Cited** — Specific URL, publisher, and publication date provided
- **Industry consensus** — Multiple concordant sources; individual URLs listed where available
- **Engineering judgment** — No strong empirical source exists; reasoning documented

---

## Step 3a: Year-1 Orders Target

| Bucket   | Conservative | Base    | Aggressive |
|----------|-------------|---------|------------|
| lt_1k    | 300         | 700     | 1,000      |
| 1_5k     | 1,500       | 3,000   | 5,000      |
| 5_20k    | 6,000       | 12,000  | 20,000     |
| gt_20k   | 25,000      | 40,000  | 60,000     |

**Rationale:** Base column picks the midpoint of each range. Conservative picks the low end (safety margin for first-time founders). Aggressive picks the high end (founders with existing audience or channel expertise). The lt_1k conservative=300 (~1 order/day) represents the floor for a viable test market. gt_20k aggressive=60,000 caps at a level achievable by well-funded DTC brands in Year 1.

**Sources:** Engineering judgment. No public dataset reports median orders per store for DTC startups. Shopify does not publish per-store order volume statistics. The band structure means the founder self-selects their range; the model only picks a point within that range, limiting the impact of any calibration error.

**Confidence:** High. The self-selection mechanism limits downside risk from any inaccuracy in the midpoints.

**Status:** No change needed.

---

## Step 3b: Gross Margin Target

| Band   | Margin |
|--------|--------|
| low    | 0.35   |
| medium | 0.50   |
| high   | 0.65   |

**Rationale:** Represents DTC ecommerce gross margin ranges. Low (35%) covers commoditized products with thin margins (basic consumer goods, electronics accessories). Medium (50%) is the DTC industry average. High (65%) covers premium/luxury products (beauty, wellness, specialty food) where brand commands pricing power.

**Sources:**
- TrueProfit (Mar 2026, 5,000+ Shopify stores): Reports DTC gross margins typically in the 55-70% range for top-performing stores. https://trueprofit.io/blog/ecommerce-profit-margins
- Onramp Funds (Feb 2025): Beauty 50-70%, Apparel 40-60%, Electronics 30-50%. https://www.onrampfunds.com/resources/10-profit-margin-benchmarks-for-ecommerce-2025
- Finaloop (Dec 2025): Ecommerce profit benchmarks across verticals. https://www.finaloop.com/blog/ecommerce-profit-benchmarks-performance-metrics

Our low=35%, medium=50%, high=65% spans the range observed across categories. Category benchmarks from `data/us/{category}.json` further refine at resolution time.

**Confidence:** High.

**Status:** No change needed.

---

## Step 3d: CAC Paid Target

| Band   | CAC ($) |
|--------|---------|
| lt_10  | 7.50    |
| 10_30  | 20.00   |
| 30_80  | 55.00   |
| gt_80  | 100.00  |

**Rationale:** Midpoints of each range. lt_10 at $7.50 works for low-competition niches (pet supplies, basic home goods). 10_30 at $20 is the DTC median. 30_80 at $55 covers competitive categories (beauty, fashion). gt_80 at $100 is a single pick-point for high-CAC verticals (luxury, supplements, electronics).

**Sources:**
- First Page Sage (Aug 2025, 80+ ecommerce clients): Reports average CAC by vertical — Food $53, Beauty $61, Fashion $66, Electronics $76, Jewelry $91. https://firstpagesage.com/reports/average-cac-for-ecommerce-companies/

Our 30_80 band ($55) and gt_80 ($100) cover the First Page Sage range well. Lower bands serve niche/low-competition categories. The founder can provide an explicit CAC to override any band.

**Confidence:** Medium-high. The gt_80 band ($100) may understate for ultra-premium categories, but the explicit override handles edge cases.

**Status:** No change needed.

---

## Step 3e: Fixed Costs Total

| Band     | Annual ($) |
|----------|-----------|
| lean     | 6,000     |
| moderate | 18,000    |
| heavy    | 42,000    |

**Rationale:** Covers the spectrum from solo-founder home-based operation to fully resourced startup. Lean ($6k = $500/month) covers minimal accounting, legal, and insurance. Moderate ($18k = $1.5k/month) adds marketing tools, professional services, and small office costs. Heavy ($42k = $3.5k/month) covers significant professional services, multiple SaaS tools, and operational overhead.

**Allocation formula:** 40% professional fees, 60% misc G&A (minus SaaS costs already accounted for). This reflects that professional fees (accounting, legal, compliance) are relatively fixed while misc G&A scales with operations.

**Sources:** Engineering judgment. No single source publishes DTC startup fixed-cost benchmarks by tier. The band structure lets founders self-select their expected overhead level, limiting calibration risk. The 40/60 allocation split is a modeling convention to separate line items.

**Confidence:** Medium. Varies significantly by region and business type. The band structure lets founders self-select.

**Status:** No change needed.

---

## Step 4: Conversion Rates

| Difficulty | conv_paid | conv_organic | conv_retention |
|-----------|-----------|-------------|----------------|
| hard      | 0.010     | 0.020       | 0.080          |
| average   | 0.015     | 0.030       | 0.100          |
| easy      | 0.020     | 0.040       | 0.120          |
| very_easy | 0.025     | 0.050       | 0.150          |

**Rationale:** These are baseline starting points. The hierarchy (retention > organic > paid) reflects that returning customers convert at significantly higher rates than cold traffic. Organic visitors (who found the site through search or content) convert better than paid traffic (interruptive ads).

"Average" difficulty (1.5% paid, 3% organic, 10% retention) aligns with the industry-wide ecommerce conversion benchmark of ~2-3% overall. The split by traffic type is based on the general observation that retention converts 5-8x better than paid.

**Sources:** Industry consensus — multiple benchmarking services report blended ecommerce conversion rates of 2-3%. Category benchmark files in `data/us/{category}.json` provide specific per-category overrides with individual source citations. For example, beauty_personal_care has conv_paid=0.048 (significantly higher than the 0.015 "average" default).

**Confidence:** Medium. These are generic baselines — category benchmarks in `data/us/{category}.json` provide much more accurate values.

**Status:** No change needed. Category overrides handle the specificity.

---

## Step 5: Channel Mix Weights

| Priority     | Paid | Organic | Retention |
|-------------|------|---------|-----------|
| profit_first | 0.25 | 0.35    | 0.40      |
| balanced     | 0.40 | 0.35    | 0.25      |
| growth_first | 0.55 | 0.30    | 0.15      |

**Rationale:** Profit-first businesses minimize expensive paid acquisition and rely on organic (cheaper but slower) and retention (highest ROI). Growth-first businesses invest heavily in paid to maximize new customer acquisition at the expense of short-term margins. Balanced is the middle ground.

The adjustment algorithm (boost selected channels, floor unselected, normalize to 1.0) ensures the founder's explicit channel preferences override the base weights while maintaining mathematical consistency.

**Sources:**
- Measured + Sequent Partners (2022, survey of 300+ DTC marketers): Reports average DTC budget split as 37% prospecting, 30% retargeting, 33% retention. https://www.measured.com/press/heres-how-dtc-brands-are-divvying-up-their-marketing-budgets/

Our "balanced" split (40/35/25) is close to the Measured survey data (37/30/33). Growth-first tilts further toward paid; profit-first tilts toward retention. The normalization step ensures self-consistency regardless of input combination.

**Confidence:** Medium-high.

**Status:** No change needed.

---

## Step 7: AOV Bands

| Band   | AOV ($) |
|--------|---------|
| lt_30  | 25      |
| 30_80  | 55      |
| 80_200 | 140     |
| gt_200 | 275     |

**Rationale:** Midpoints of each range. lt_30 at $25 represents impulse buys (small accessories, consumables). 30_80 at $55 is near the DTC median. 80_200 at $140 covers premium products (skincare sets, specialty electronics). gt_200 at $275 covers luxury/high-ticket items.

**Sources:** Industry consensus — multiple ecommerce analytics platforms report median AOV in the $50-$100 range depending on vertical. Founders can provide explicit AOV to override.

**Confidence:** High. The band midpoint approach limits impact of any calibration error, and founders can override with an explicit value.

**Status:** No change needed.

---

## Step 7: Discount/Promo Rate

| Priority     | Default % |
|-------------|----------|
| profit_first | 0.05     |
| balanced     | 0.10     |
| growth_first | 0.20     |

**Rationale:** Represents the blended effective discount rate across all orders (welcome discounts, seasonal sales, coupon codes, bundle pricing). Profit-first at 5% means minimal discounting — only selective loyalty rewards or rare seasonal events. Balanced at 10% reflects a standard DTC approach with welcome offers (~10-15% for first purchase) and periodic promotions, averaged across all orders. Growth-first at 20% reflects aggressive promotional strategy with frequent welcome discounts, referral incentives, and seasonal sales.

**Sources:**
- Opensend / Forbes (Apr 2025): Reports on average ecommerce discount rates. Notes that while individual coupon values can be 10-20%, the effective rate as a percentage of total revenue is lower because not all orders use coupons. https://www.opensend.com/post/average-discount-rate-statistics-ecommerce

Engineering judgment for the specific tier values. No single source breaks down effective discount rate by business strategy type. The tiered approach (5%/10%/20%) spans the observed range.

**Confidence:** Medium. Highly variable by category and founder strategy.

**Change log (2026-03-02):** Previous values were balanced=0.175 and growth_first=0.30. Lowered based on stress-test: 17.5% was above industry medians for a "balanced" default, and 30% effectively gives away nearly a third of gross revenue — more consistent with a clearance model than a growth DTC brand. New values (10% and 20%) better align with observed DTC discounting patterns.

---

## Step 7: Return Rate by Category

| Category              | Rate  |
|----------------------|-------|
| fashion_apparel       | 0.20  |
| beauty_personal_care  | 0.08  |
| home_garden           | 0.10  |
| electronics_gadgets   | 0.12  |
| food_beverage         | 0.03  |
| health_wellness       | 0.06  |
| pets                  | 0.05  |
| sports_outdoors       | 0.12  |
| toys_kids             | 0.10  |
| jewelry_accessories   | 0.15  |
| other                 | 0.10  |

**Rationale:** Category-specific return rates based on industry data. Fashion leads at 20% (sizing issues, try-before-you-buy behavior). Food/beverage at 3% (consumables rarely returned). Beauty at 8% (allergic reactions, shade mismatches). Electronics at 12% (defect returns, buyer's remorse).

**Sources:**
- NRF + Happy Returns (Dec 2024): Reports overall retail return rate of 16.9% in 2024. https://nrf.com/media-center/press-releases/nrf-and-happy-returns-report-2024-retail-returns-total-890-billion
- Rocket Returns (Jul 2025): Category-specific analysis — Fashion ~24%, Electronics ~12%, Beauty ~12%, Home ~10%. https://www.rocketreturns.io/blog/ecommerce-return-rates-2025-complete-industry-analysis-benchmarks-by-category

Our fashion=20% is slightly below the Rocket Returns 24% figure (conservative for a startup model). Electronics=12% and beauty=8% align with the lower end of published ranges. Food/beverage=3% and pets=5% reflect the inherently low return rates for consumables.

**Confidence:** High. These are well-documented industry averages.

**Status:** No change needed.

---

## Step 7: Payment Processing Fee by Platform

| Platform      | Fee   |
|--------------|-------|
| dtc_website   | 0.029 |
| amazon        | 0.00  |
| etsy          | 0.029 |
| multi_channel | 0.015 |

**Rationale:** DTC at 2.9% is the standard Stripe/PayPal rate (2.9% + $0.30, simplified to percentage-only for modeling). Amazon at 0% because payment processing is bundled into their referral fee. Etsy at 2.9% matches Etsy Payments processing. Multi-channel at 1.5% is a weighted average assuming some orders go through marketplace-bundled processing.

**Sources:** Published platform pricing pages — Stripe (2.9% + $0.30), Amazon Seller Central fee schedule (processing bundled into referral fee), Etsy Payments fee schedule (2.9% + $0.25 for Etsy Payments, reduced for Etsy Plus).

**Confidence:** High. These are published rates.

**Status:** No change needed.

---

## Step 7: Platform Fee by Platform

| Platform      | Fee  |
|--------------|------|
| dtc_website   | 0.00 |
| amazon        | 0.15 |
| etsy          | 0.065|
| multi_channel | 0.08 |

**Rationale:** DTC at 0% — no marketplace commission (Shopify charges a subscription, not a transaction fee, which is captured in SaaS costs). Amazon at 15% — standard referral fee across most categories. Etsy at 6.5% — transaction fee. Multi-channel at 8% — weighted average of DTC (0%) and marketplace (15%) assuming roughly 50/50 split.

**Sources:** Published marketplace fee schedules — Amazon referral fee (15% for most categories, ranging 8-45%), Etsy transaction fee (6.5%).

**Confidence:** High. Published marketplace rates. Amazon varies by category (8-45%) but 15% is the most common.

**Status:** No change needed.

---

## Step 7: Shipping Cost Bands

| Band     | $/order |
|----------|---------|
| very_low | 4       |
| normal   | 8       |
| high     | 15      |

**Rationale:** Very_low ($4) covers lightweight items (cosmetics, small accessories, digital-adjacent products with minimal packaging). Normal ($8) aligns with the US regional default ($8.50 in regional_defaults.json) for a standard 1-3lb ground shipment. High ($15) covers bulky, heavy, or fragile items requiring special handling.

**Sources:** regional_defaults.json US shipping cost ($8.50, sourced from Simple Global). FedEx/UPS/USPS rate calculators for 1-5lb packages confirm the $4-$15 range for domestic ground.

**Confidence:** Medium-high. Regional defaults provide more specific values; these bands are for when the founder selects a qualitative band.

**Status:** No change needed.

---

## Step 7: Handling Cost by Fulfillment Mode

| Mode          | Formula                          |
|--------------|----------------------------------|
| self_fulfill  | max($1.00, 10% of ship_cost)     |
| third_party   | max($2.50, 30% of ship_cost)     |
| dropship_pod  | max($0.50, 5% of ship_cost)      |

**Rationale:** Self-fulfill at 10% reflects the labor cost of picking, packing, and labeling when the founder handles it. Floor of $1.00 ensures some handling cost even for very cheap shipping. Third-party at 30% reflects 3PL pick-and-pack fees. Floor of $2.50 covers minimum 3PL per-order charges. Dropship at 5% reflects minimal handling (supplier ships directly). Floor of $0.50 covers any coordination cost.

**Sources:**
- Ideal Fulfillment (Oct 2025): Reports 3PL pick-and-pack fees of $2.50-$5.00 for the first item, with all-in fulfillment costs of $5-$10/order. https://idealfulfillment.com/blog/2025/10/how-much-does-3pl-warehouse-cost/
- EasyPost / ShipBob (Jul 2024): Typical 3PL costs and fee structures. https://www.easypost.com/blog/2024-07-19-navigate-common-3pl-costs-and-fees-to-find-best-pricing/

Our third_party floor of $2.50 aligns with the low end of Ideal Fulfillment's $2.50-$5.00 pick-and-pack range. The 30% formula captures scaling with shipping cost (heavier/bulkier items have higher handling costs).

**Confidence:** Medium. Varies significantly by 3PL provider and package complexity.

**Status:** No change needed.

---

## Step 7: Repeat Purchase

| Expectation | Rate | Frequency |
|------------|------|-----------|
| none       | 0.00 | 1.0       |
| low        | 0.10 | 1.5       |
| medium     | 0.25 | 2.5       |
| high       | 0.40 | 4.0       |

**Rationale:** Rate = percentage of customers who make a repeat purchase within the year. Frequency = average number of orders per repeat customer per year. None at 0% rate means all customers are one-time buyers (frequency set to 1.0). Low at 10% rate, 1.5 frequency covers products with occasional repurchase (home goods, electronics accessories). Medium at 25%, 2.5 frequency covers consumables with moderate replenishment cycles (beauty, supplements). High at 40%, 4.0 frequency covers daily-use consumables (food, beverages, pet supplies).

**Sources:**
- Bluecore (Apr 2024, 100+ retailers): Reports average repeat purchase rate of 16.5%. https://www.globenewswire.com/news-release/2024/04/16/2863832/0/en/
- BS&Co (156K customers analyzed): Reports average repeat purchase rate of 18.8%. https://bsandco.us/blog-post/repeat-purchase-rate-benchmarks

Our low=10% is below the Bluecore/BS&Co average (intentionally conservative for "low" expectation). Medium=25% is above average, appropriate for categories with natural replenishment. High=40% is aspirational, appropriate for subscription-adjacent or daily-use categories.

**Confidence:** Medium. Highly variable by product type and retention strategy.

**Change log (2026-03-02):** Changed "none" frequency from 1.5 to 1.0 for semantic clarity. No mathematical impact (rate=0 means frequency is never applied).

---

## Step 7: Retention Improvement by Ambition

| Ambition     | Rate |
|-------------|------|
| conservative | 0.03 |
| base         | 0.05 |
| aggressive   | 0.08 |

**Rationale:** Annual improvement in repeat purchase rate, compounded: `repeat_rate_year_n = repeat_rate_year1 * (1 + rate)^(n-1)`. Conservative at 3% reflects minimal retention investment. Base at 5% reflects standard email/loyalty programs improving retention over time. Aggressive at 8% reflects heavy investment in retention (loyalty programs, subscriptions, personalization).

**Sources:** Engineering judgment. No published dataset tracks YoY retention rate improvement for DTC startups specifically. The values are calibrated so that even the aggressive rate (8%) produces modest absolute change over 6 years (e.g., 25% repeat rate → ~37% by Year 6), which stays within plausible bounds.

**Confidence:** Low-medium. Limited empirical data on retention rate improvement trajectories.

**Status:** No change needed.

---

## Step 7: COGS Improvement by Ambition

| Ambition     | Rate |
|-------------|------|
| conservative | 0.005 |
| base         | 0.01  |
| aggressive   | 0.02  |

**Rationale:** Annual COGS reduction as the business negotiates better supplier terms and achieves scale efficiencies. Applied as `cogs_pct_year_n = cogs_pct * (1 - rate)^(n-1)`. Conservative at 0.5% reflects minimal improvement. Base at 1% reflects standard supplier renegotiation. Aggressive at 2% reflects active sourcing optimization and volume-based pricing tiers.

**Sources:**
- Klavena (2025): Notes that ecommerce businesses can achieve 3-5% per-unit cost reductions at volume through supplier negotiation and bulk purchasing. https://www.klavena.com/blog/cost-of-goods-sold-cogs-optimization-for-ecommerce-businesses/

Engineering judgment for the specific tier values. The Klavena figure (3-5% per-unit at volume) supports the aggressive end of our range. Our conservative=0.5% and base=1% are intentionally below this for early-stage businesses without volume leverage.

**Confidence:** Low-medium. Varies significantly by category and supplier relationships.

**Status:** No change needed.

---

## Step 8: CPC Inflation by Ambition

| Ambition     | Rate |
|-------------|------|
| conservative | 0.06  |
| base         | 0.08  |
| aggressive   | 0.12  |

**Rationale:** Annual cost-per-click inflation. Higher ambition levels target more competitive keyword auctions, facing faster CPC growth. Conservative at 6% aligns with the long-term CAGR in global_defaults.json. Base at 8% reflects moderate competition. Aggressive at 12% reflects entering highly competitive ad auctions with rapidly escalating costs.

**Sources:**
- WordStream Google Ads Benchmarks (Sep 2025 update): Reports average CPC increased ~10% in 2024. https://www.wordstream.com/blog/2024-google-ads-benchmarks
- WordStream 2025 Benchmarks (Sep 2025): Reports CPC increased 12.88% in 2025. https://www.wordstream.com/blog/2025-google-ads-benchmarks
- Search Engine Land (Apr 2025): Reports long-term CPC CAGR of approximately 4.37%. https://searchengineland.com/cpc-inflation-google-ads-costs-rising-fast-454291

Our conservative=6% sits between the long-term CAGR (~4.4%) and recent annual spikes (10-13%). For a 6-year model, the long-term rate is more appropriate than recent-year spikes. global_defaults.json cpc_inflation=0.06 uses the same anchor.

**Confidence:** Medium. CPC inflation is volatile year-to-year. The range from 6% to 12% brackets the plausible outcomes.

**Change log (2026-03-02):** Previous values were conservative=0.075, base=0.10, aggressive=0.125. Adjusted downward to anchor conservative to the global_defaults.json long-term CAGR of 6%, and scale up for higher ambition levels.

---

## Step 8: Traffic YoY Growth by Ambition

| Ambition     | Rate |
|-------------|------|
| conservative | 0.10  |
| base         | 0.225 |
| aggressive   | 0.45  |

**Rationale:** Annual traffic growth rate, held constant across all 6 years. These are midpoints of ranges from deep_research_policy.md: conservative 5-15%, base 15-30%, aggressive 30-60%. Over 6 years, conservative compounds to ~1.8x, base to ~3.6x, and aggressive to ~9.3x.

**Sources:**
- Invesp (2025): Reports overall DTC market CAGR of ~24.3%. https://www.invespcro.com/blog/direct-to-consumer-brands/

Engineering judgment for the specific tier values. No published source reports startup-specific traffic growth rates (as distinct from market-level growth). The DTC market CAGR (~24%) supports our "base" midpoint of 22.5%. The flat rate across all years is a simplification; real businesses see declining growth rates. But for a 6-year pre-launch model, a single rate is the right tradeoff between accuracy and complexity.

**Confidence:** Medium.

**Status:** No change needed.

---

## Step 9: Team Cost

**Headcount:** 0_1=0.5, 2_3=2.5, 4_7=5.5, 8_plus=10.0
**Base salary:** low=$40k, mid=$65k, high=$100k
**Burden multiplier:** 1.25

**Rationale:** Headcount uses midpoints of each bucket. 0_1 at 0.5 FTE represents a solo founder working part-time (a full-time solo founder should select 2_3). Base salaries reflect US ecommerce operations roles: low ($40k) for junior/entry-level or part-time contractors, mid ($65k) for experienced operators, high ($100k) for senior managers and specialists. The 1.25 burden multiplier (25% on top) covers payroll taxes (~8%) and minimal benefits/stipends (~17%) — appropriate for startups without full benefits packages.

**Regional adjustment:** Salary is multiplied by the regional salary multiplier from regional_defaults.json (UK=0.85, EU=0.90, CA=0.95, AU=1.05, other=0.75).

**Sources:**
- BLS Employer Costs for Employee Compensation (Sep 2024): Total employer costs for private industry workers averaged $44.40/hour. For small establishments (<50 workers), benefits add approximately 34% on top of wages. Payroll taxes alone are 8.05% of wages. https://www.bls.gov/opub/ted/2024/compensation-costs-for-private-industry-workers-averaged-44-40-per-hour-in-september-2024.htm
- Abacus Payroll (2024): Federal payroll tax rates — employer share ~8.05% (6.2% Social Security + 1.45% Medicare + FUTA). https://abacuspay.com/resources/payroll-tax-wage-rates/federal-payroll-tax-rates-2024/

Our 25% burden targets startups: payroll taxes (8%) + minimal benefits/stipends (~17%). BLS reports 34% all-in for small biz (includes health insurance, retirement, paid leave), but pre-launch startups typically don't offer full benefits packages.

**Confidence:** High for US; medium for other regions (multipliers are approximations).

**Status:** No change needed.

---

## Step 9: Months to Full Team

| Bucket   | Months |
|----------|--------|
| 0_1      | 0      |
| 2_3      | 3      |
| 4_7      | 6      |
| 8_plus   | 9      |

**Rationale:** Larger teams take longer to hire. Solo founder (0_1) starts immediately. Small team (2_3) ramps over a quarter. Medium team (4_7) ramps over two quarters. Large team (8_plus) ramps over three quarters. During ramp months, salary cost is calculated at 50% (average of 0 hires at start and full team at end of ramp).

**Sources:** Engineering judgment. No published dataset reports average hiring timelines for DTC ecommerce startups. The 3-month increment per tier is a modeling convention.

**Confidence:** Medium. Varies by labor market and founder's hiring readiness.

**Status:** No change needed.

---

## Step 9: Monthly SaaS Costs by Platform

| Platform      | Monthly ($) |
|--------------|------------|
| dtc_website   | $250       |
| amazon        | $100       |
| etsy          | $50        |
| multi_channel | $350       |

**Rationale:** DTC at $250/month covers Shopify Basic ($39), email marketing (Klaviyo ~$45), analytics (GA4 free + paid tools ~$50), reviews/UGC ($30), and miscellaneous tools (~$86). Amazon at $100/month covers Professional seller subscription ($39.99) plus basic listing/inventory tools. Etsy at $50/month covers Etsy Plus ($10) and basic tools. Multi-channel at $350/month covers DTC stack plus marketplace tools and integration software.

**Sources:** Published SaaS pricing pages for Shopify ($39/month Basic plan), Klaviyo (free up to 250 contacts, ~$45/month at 1K-2K contacts), Amazon Professional seller ($39.99/month), Etsy Plus ($10/month). The composite estimates per platform are engineering judgment based on aggregating published individual tool costs.

**Confidence:** Medium-high. SaaS costs are well-documented but founders may use more or fewer tools.

**Status:** No change needed.

---

## Step 9: Overhead Inflation

| Band | Rate |
|------|------|
| flat | 0.00 |
| 3_5  | 0.04 |
| 5_10 | 0.075 |

**Rationale:** Midpoints of each band. Flat at 0% for founders who expect no overhead growth (solo operation, fixed-price contracts). 3_5 at 4% aligns with general business cost inflation. 5_10 at 7.5% covers rapid overhead growth from scaling (new tools, increased professional fees, expanding team support costs).

**Sources:** Industry consensus — US CPI for services has averaged 3-5% annually in recent years. SaaS vendors typically raise prices 5-10% annually.

**Confidence:** Medium.

**Status:** No change needed.

---

## Step 9: Warehouse Rent

| Condition | Annual rent |
|-----------|-----------|
| no_stock (dropship/POD) | $0 |
| 0_1 team + 1_2_months inventory | $0 |
| 2_3 team OR 3_plus_months inventory | $12,000 |
| 4_7 team | $24,000 |
| 8_plus team | $42,000 |

**Rationale:** Dropship/POD businesses hold no inventory and need no warehouse. Solo founders with light inventory (1-2 months) work from home/garage. Once team exceeds 2-3 people OR inventory exceeds 3 months, a small warehouse unit is needed. Larger teams need proportionally more space.

**Sources:**
- Colliers via Supply Chain Dive (Feb 2024): Reports average US warehouse asking rent of $9.72/sq ft/year. https://www.supplychaindive.com/news/warehouse-rent-lease-rates-colliers-2024/707552/
- Cushman & Wakefield via Red Stag Fulfillment (Q2 2025): Reports $9.51/sq ft/year for facilities under 100,000 sq ft. https://redstagfulfillment.com/warehousing-rates-per-square-foot-in-us/

At $9.51/sq ft/year: ~1,200 sq ft = $11.4k (our 2_3 team = $12k), ~2,500 sq ft = $23.8k (our 4_7 team = $24k), ~4,400 sq ft = $41.8k (our 8_plus team = $42k). Values align closely with real warehouse rent data.

**Confidence:** Medium. Highly variable by geography.

**Change log (2026-03-02):** New mapping table added to replace LLM inference. Previously only the start year had deterministic rules; the rent amount was inferred.

---

## Step 9: Office Rent

| Condition | Annual rent |
|-----------|-----------|
| team_size_bucket < 8_plus | $0 |
| team_size_bucket = 8_plus | $18,000 |

**Rationale:** Pre-launch ecommerce businesses work remotely. Solo founders and small teams (0-7 people) do not need dedicated office space. Only teams of 8+ benefit from a shared workspace ($1.5k/month for coworking or small office).

**Sources:**
- CoworkingCafe via Coworking Insights (Q2 2024): Reports median dedicated desk cost of $300/month, hot desk at $149/month. https://coworkinginsights.com/the-cost-of-coworking-these-are-2024s-most-least-affordable-metros-for-coworking-subscriptions/
- Deskpass (Aug 2024): Reports coworking space costs by type and market. https://www.deskpass.com/resources/guides/how-much-do-coworking-spaces-cost

At 10 desks × $300/month = $36k, but a small shared office or team plan is cheaper than individual desks. Our $18k/year ($1.5k/month) is reasonable for a small shared space or team coworking plan.

Remote work assumption: Engineering judgment. No ecommerce-specific data on remote work rates exists. Broader surveys (BLS, Zoom) suggest ~30% of small businesses work fully remotely, but DTC ecommerce is inherently digital and likely above average. Remote-first is the standard assumption for pre-launch DTC startups.

**Confidence:** Medium. Remote-first is the standard assumption for DTC ecommerce.

**Change log (2026-03-02):** New mapping table added to replace LLM inference.

---

## Step 9: Rent Start Years

| Ambition     | Condition       | Start Year |
|-------------|-----------------|------------|
| conservative | any             | 2028       |
| base         | any             | 2027       |
| aggressive   | heavy inventory | 2027       |
| aggressive   | no heavy inv    | 2026       |

**Rationale:** Conservative businesses delay physical space commitment. Aggressive businesses with heavy inventory need warehouse space sooner. The 1-2 year delay reflects the pre-launch reality: most DTC founders start from home and only take on rent when volume demands it.

**Sources:** Engineering judgment. No published data on when DTC startups first take on physical space. The logic follows from the assumption that founders minimize fixed costs early and only commit to rent when operations demand it.

**Confidence:** Medium. Depends heavily on local real estate and founder's personal situation.

**Status:** No change needed.

---

## Step 9: Inflation Defaults

| Driver         | Rate  |
|---------------|-------|
| rent_inflation | 0.03  |
| ship_inflation | 0.06  |
| aov_inflation  | 0.025 |

**Rationale:** Rent at 3% aligns with global_defaults.json (sourced from Cushman & Wakefield industrial rent data, 2-4% post-pandemic normalization). Ship inflation at 6% aligns with global_defaults.json (sourced from FedEx/UPS 5.9% GRI announcement). AOV inflation at 2.5% reflects gradual price increases to offset input cost inflation — conservative relative to CPI.

**Sources:** global_defaults.json (rent and shipping sourced with citations). AOV inflation is engineering judgment — no single source publishes DTC price increase rates.

**Change log (2026-03-02):** Ship inflation changed from 0.05 to 0.06 to align with global_defaults.json sourced value (FedEx/UPS 5.9% GRI).

---

## Step 7: Packaging Cost Per Order

| Category type | $/order | Categories |
|--------------|---------|-----------|
| lightweight/simple | $1.50 | beauty_personal_care, health_wellness, jewelry_accessories, food_beverage |
| standard | $2.50 | home_garden, pets, toys_kids, electronics_gadgets, other |
| bulky/fragile | $4.00 | sports_outdoors, fashion_apparel |

**Rationale:** Packaging cost depends on product size and fragility. Lightweight items (cosmetics, supplements, small jewelry) need minimal packaging — a poly mailer or small box with tissue paper. Standard items (home goods, toys, electronics) need a standard corrugated box with void fill. Bulky/fragile items (outdoor gear, apparel with hangers/tissue) need larger boxes or specialized packaging.

**Sources:**
- Opensend (2024): Reports typical ecommerce packaging costs of $0.50-$2.00, with premium branded packaging at $2.50-$5.00. https://www.opensend.com/post/packaging-cost-per-order-statistics-ecommerce

Our lightweight=$1.50 (within the $0.50-$2.00 typical range), standard=$2.50 (at the top of typical / bottom of premium), bulky=$4.00 (within the $2.50-$5.00 premium range). All values align with the Opensend data.

**Confidence:** Medium. Varies significantly by product dimensions and brand packaging standards.

**Change log (2026-03-02):** New mapping table added to replace LLM inference.

---

## Step 7: Support Cost Per Order

| Platform      | $/order |
|--------------|---------|
| dtc_website   | $1.50   |
| amazon        | $0.50   |
| etsy          | $1.00   |
| multi_channel | $1.75   |

**Rationale:** DTC sellers handle all customer inquiries directly — pre-sale questions, order status, returns, complaints. At $1.50/order, this covers the blended cost of support software and time spent per ticket. Amazon at $0.50 reflects that Amazon handles most customer service. Etsy at $1.00 reflects partial platform support. Multi-channel at $1.75 covers the complexity of managing support across multiple platforms.

**Sources:**
- MaestroQA (2024) via LiveChatAI: Reports customer support cost per ticket of $2.70-$5.60. https://livechatai.com/blog/customer-support-cost-benchmarks
- Gorgias blog: Illustrative example showing ~$1.73/order for a DTC store using Gorgias. https://www.gorgias.com/blog/how-to-calculate-the-marginal-cost-of-customer-support-for-your-ecommerce-store

Not every order generates a support ticket. The MaestroQA per-ticket cost ($2.70-$5.60) translates to a lower per-order cost when divided by total orders. The Gorgias example (~$1.73/order) closely matches our DTC value ($1.50/order).

**Confidence:** Medium. Varies by product complexity and support team efficiency.

**Change log (2026-03-02):** New mapping table added to replace LLM inference.

---

## Step 10: Working Capital

**AR Days:** upfront=0, mostly_upfront=3, invoice=30
**AP Days:** 15_days=15, 30_days=30, 45_60_days=52.5
**Inventory Days:** no_stock=0, 1_2_months=45, 3_plus_months=120

**Rationale:** AR days reflect how quickly customers pay. DTC ecommerce is mostly upfront (credit card at checkout = 0 days). B2B or wholesale adds invoice terms (Net 30). AP days match the named payment terms. Inventory days: 1_2_months at 45 days (midpoint of 30-60), 3_plus_months at 120 days (4 months of stock, reflecting the upper end of the range for businesses that batch-order from overseas manufacturers).

**Sources:** Standard accounting definitions. AP and AR days map directly to the named terms (Net 15, Net 30, etc.) — no estimation required.

**Confidence:** High.

**Status:** No change needed.

---

## Step 11: Capex and Depreciation

**Capex %:** profit_first=0.01, balanced=0.02, growth_first=0.035
**Depreciation:** <1.5% → 3yr, 1.5-3.5% → 4yr, >3.5% → 5yr

**Rationale:** Capex as a percentage of revenue. Profit-first at 1% reflects minimal investment (basic equipment, minor upgrades). Balanced at 2% covers moderate investment (equipment, tooling, minor buildouts). Growth-first at 3.5% covers significant investment (custom equipment, major buildouts, technology infrastructure). Depreciation period scales with capex magnitude — larger investments tend to be longer-lived assets.

**Sources:** deep_research_policy.md ranges: profit_first 0.5-1.5%, balanced 1-3%, growth_first 2-5%. Values are midpoints. Engineering judgment for the depreciation tiers.

**Confidence:** Medium. DTC ecommerce is relatively asset-light; capex is a minor line item for most startups.

**Status:** No change needed.

---

## Step 12: Loan Interest Rate Bands

| Band  | Rate  |
|-------|-------|
| 5_8   | 0.065 |
| 8_12  | 0.10  |
| gt_12 | 0.14  |

**Rationale:** Midpoints of each range. 5_8 at 6.5% reflects SBA loan rates. 8_12 at 10% reflects online lenders and revenue-based financing. gt_12 at 14% reflects higher-risk lending (merchant cash advances, high-interest lines of credit).

**Sources:** Industry consensus — SBA loan rates are published by the SBA (currently Prime + 2.25-4.75% depending on loan size and term). Online lender rates (Kabbage, BlueVine, OnDeck) are published on their websites, typically 8-15%.

**Confidence:** Medium-high. Interest rates fluctuate with Fed funds rate; these are mid-2024 anchored.

**Status:** No change needed.

---

## Step 12: Tax Rate by Region

| Region | Rate  |
|--------|-------|
| US     | 0.26  |
| UK     | 0.19  |
| EU     | 0.213 |
| CA     | 0.122 |
| AU     | 0.25  |
| other  | 0.25  |

**Rationale:** Aligned with regional_defaults.json sourced values. US at 26% is federal 21% + weighted average state ~5%. UK at 19% is the small profits rate (applicable for businesses under GBP 50k profit — appropriate for pre-launch). EU at 21.3% is the EU-wide average (significant variation: Germany 29.9%, Ireland 12.5%). CA at 12.2% is the small business deduction rate (9% federal + ~3% provincial) — correct for our pre-launch founder audience. AU at 25% is the base rate entity rate (turnover under AUD $50M).

**Sources:** regional_defaults.json (all individually sourced):
- US: Tax Foundation https://taxfoundation.org/data/all/state/state-corporate-income-tax-rates-brackets/
- UK: HMRC https://www.gov.uk/corporation-tax-rates
- CA: CRA https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/corporation-tax-rates.html
- AU: ATO https://www.ato.gov.au/rates/company-tax/

**Confidence:** High for US, UK, AU. Medium for EU (varies by country). High for CA (small business rate clearly applies).

**Change log (2026-03-02):** Previous SKILL.md values were US=0.25, EU=0.22, CA=0.26, AU=0.30. Updated to match regional_defaults.json sourced values. The CA correction is the most significant: 26% → 12.2% (was using the general corporate rate instead of the small business rate, overstating Canadian founder tax bills by 2x).

---

## Step 12: Equity Suggestion Algorithm

**Runway months:** conservative=6, base=9, aggressive=12
**Buffer multiplier:** 1.15
**Floor:** $10,000

**Rationale:** Conservative businesses need less runway (lower burn, slower growth). Aggressive businesses need more runway to sustain higher burn rates through the growth phase. The 1.15 buffer (15%) provides a safety margin above the calculated minimum. The $10,000 floor prevents unrealistically low equity suggestions for micro-businesses.

**Sources:**
- JP Morgan: Recommends 18-24 months historical runway, 24-36 months in current environment. https://www.jpmorgan.com/insights/business-planning/does-your-startup-have-enough-runway-to-survive
- Scaleup.finance (2025): Startup runway planning guide. https://www.scaleup.finance/article/startup-runway-guide-how-much-cash-buffer-you-really-need-in-2025

Our runway months (6/9/12) are below the JP Morgan recommendation (18-24 months), which is appropriate because: (1) pre-launch ecommerce has simpler cost structures than the tech startups JP Morgan targets, and (2) the equity optimization loop in the financial-model skill iterates until cash stays positive, providing an additional safety net.

**Confidence:** Medium. The algorithm's real validation comes from the equity optimization loop, which adjusts equity upward if the model shows negative cash.

**Status:** No change needed.
