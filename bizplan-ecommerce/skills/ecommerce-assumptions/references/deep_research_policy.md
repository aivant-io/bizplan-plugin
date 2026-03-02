### Deep-Research Instruction Policy (V1 Ecommerce)

### Purpose

This file captures the **production policy** for how the deep-research/normalization agent should convert the intake (`intake_schema.jsonc`) + driver definitions (`driver_catalog.jsonc`) into final model driver values (one value per `input_id`) plus any internal-only targets (as documented in `resolved_assumptions_schema.jsonc`).

- **UI question wording is not policy**; keep heuristics here.
- **Excel cell addresses are not policy**; keep them in `input_map.jsonc`.

---

### Global rules (apply to all drivers)

- **Forecast period**: the model forecast runs on calendar years **2026–2031** (Year 1 = **2026**). Any `type = year` drivers refer to these calendar years.
- **Respect types and bounds** from `driver_catalog.jsonc` (Excel wiring is not a source of semantic truth).
- **Flat-by-design drivers stay flat**: if the model uses a single YoY rate, treat it as constant across the forecast.
- **Avoid over-determination**: do not set redundant driver sets that can conflict. Prefer one canonical set of drivers and derive the rest deterministically.
- **Keep assumptions explainable**: pick values that are plausible for category/region/stage and consistent with the user’s ambition.

---

### Numerical mapping tables (defaults)

These tables provide **default numeric pick-points** for enums/bands. Use these unless you have strong evidence to adjust (category/region specifics), and always respect `driver_catalog.jsonc` bounds.

#### Year-1 orders bucket → numeric target (before traffic math)

| `demand.year1_orders_bucket` |    low |   base |   high |
| ---------------------------- | -----: | -----: | -----: |
| `lt_1k`                      |    300 |    700 |  1,000 |
| `1_5k`                       |  1,500 |  3,000 |  5,000 |
| `5_20k`                      |  6,000 | 12,000 | 20,000 |
| `gt_20k`                     | 25,000 | 40,000 | 60,000 |

#### Conversion difficulty → baseline conversion rates (Year 1)

Use these as baseline starting points (then apply category/region adjustment). Maintain: retention > organic > paid.

| `acquisition.conv_difficulty` | `conv_paid` | `conv_organic` | `conv_retention` |
| ----------------------------- | ----------: | -------------: | ---------------: |
| `hard`                        |        1.0% |           2.0% |             8.0% |
| `average`                     |        1.5% |           3.0% |            10.0% |
| `easy`                        |        2.0% |           4.0% |            12.0% |
| `very_easy`                   |        2.5% |           5.0% |            15.0% |

#### CAC band → numeric CAC target

| `acquisition.cac_band` | default CAC (USD) |
| ---------------------- | ----------------: |
| `lt_10`                |               7.5 |
| `10_30`                |                20 |
| `30_80`                |                55 |
| `gt_80`                |               100 |

#### Gross margin band → numeric target

| `unit_economics.gross_margin_band` | default GM% |
| ---------------------------------- | ----------: |
| `low`                              |         35% |
| `medium`                           |         50% |
| `high`                             |         65% |

Then compute: `cogs_pct = 1 - gross_margin_target_pct`, where `gross_margin_target_pct` is the resolved GM% (from `unit_economics.gross_margin_target_pct` when explicit, otherwise from `unit_economics.gross_margin_band`).

#### AOV band → numeric AOV (Year 1)

| `pricing.aov_band` | default AOV (USD) |
| ------------------ | ----------------: |
| `lt_30`            |                25 |
| `30_80`            |                55 |
| `80_200`           |               140 |
| `gt_200`           |               275 |

#### Shipping cost band → numeric shipping+packaging (Year 1)

| `unit_economics.shipping_cost_band` | default ship cost (USD/order) |
| ----------------------------------- | ----------------------------: |
| `very_low`                          |                             4 |
| `normal`                            |                             8 |
| `high`                              |                            15 |

#### Fulfilment mode → handling cost proxy (Year 1)

Use these as default proxies (adjust by category/region and ship-cost realism):

| `unit_economics.fulfilment_mode_year1` |                default handling cost |
| -------------------------------------- | -----------------------------------: |
| `self_fulfill`                         | max( $1.00, 10% of ship_cost_year1 ) |
| `third_party_fulfillment`              | max( $2.50, 30% of ship_cost_year1 ) |
| `dropship_pod`                         |  max( $0.50, 5% of ship_cost_year1 ) |

#### Working capital enums → days

**Customer payment terms → AR days**

| `working_capital.customer_payment_terms` | default `ar_days` |
| ---------------------------------------- | ----------------: |
| `upfront`                                |                 0 |
| `mostly_upfront`                         |                 3 |
| `invoice`                                |                30 |

**Supplier payment terms → AP days**

| `working_capital.supplier_payment_terms` | default `ap_days` |
| ---------------------------------------- | ----------------: |
| `15_days`                                |                15 |
| `30_days`                                |                30 |
| `45_60_days`                             |              52.5 |

**Inventory intensity → inventory days (Year 1) + improvement**

| `working_capital.inventory_intensity` | default `inventory_days_year1` | default `inventory_turns_improvement` |
| ------------------------------------- | -----------------------------: | ------------------------------------: |
| `no_stock`                            |                              0 |                                    0% |
| `1_2_months`                          |                             45 |                                    5% |
| `3_plus_months`                       |                            120 |                                    8% |

#### Overhead inflation band → numeric rate

| `team_overhead.overhead_inflation_band` | default `sal_prof_inflation` |
| --------------------------------------- | ---------------------------: |
| `flat`                                  |                           0% |
| `3_5`                                   |                           4% |
| `5_10`                                  |                         7.5% |

#### Loan interest band → numeric interest rate

| `funding_tax.loan_interest_band` | default `interest_rate` |
| -------------------------------- | ----------------------: |
| `5_8`                            |                    6.5% |
| `8_12`                           |                   10.0% |
| `gt_12`                          |                   14.0% |

---

### Canonical decision anchors (V1)

#### Year-1 demand anchor

- Use `demand.year1_orders_bucket` as the primary demand anchor.
- Choose a specific Year-1 total orders target within the bucket:
  - `strategy.growth_ambition = conservative` → low end of bucket
  - `strategy.growth_ambition = base` → middle of bucket
  - `strategy.growth_ambition = aggressive` → high end of bucket

#### Fulfilment mode (Year 1)

- Intake field: `unit_economics.fulfilment_mode_year1`.
- If `not_sure`, resolve deterministically using:
  - If `working_capital.inventory_intensity = no_stock` → `dropship_pod`
  - Else if inventory is heavy (`3_plus_months`) or ambition+scale is high → `third_party_fulfillment`
  - Else → `self_fulfill`

---

### Traffic + conversion policy

#### Channel mix

- Inputs: `acquisition.primary_channels`, `acquisition.use_standard_mix`, `strategy.financial_priority`.
- Produce a paid/organic/retention mix that sums to 1.0.
- Keep mix constant across forecast years.
  - If the user has no paid acquisition (`acquisition.cac_mode = none` or `paid_ads` not in `acquisition.primary_channels`), set `traffic_mix_paid_pct = 0` and re-normalize the remaining mix across organic/retention.

#### Conversion rates

- Input: `acquisition.conv_difficulty` (+ category/region benchmarks).
- Maintain sensible ordering unless strong evidence suggests otherwise:
  - `conv_retention` > `conv_organic` > `conv_paid`
- Treat conversions as a Year-1 baseline and keep constant across forecast years (V1).

#### Traffic Year 1

- Compute traffic from the Year-1 orders target and the chosen mix+conversion:
  - weighted_conv = mix_paid*conv_paid + mix_organic*conv_organic + mix_retention\*conv_retention
  - traffic_total_year1 = total_orders_year1_target / weighted_conv

#### Traffic growth

- Set `traffic_yoy_growth` as a single flat YoY rate after Year 1.
- Map ambition to a conservative/base/aggressive range (category/region-adjusted):
  - conservative: 5–15%
  - base: 15–30%
  - aggressive: 30–60%

---

### Order economics policy

#### AOV

- `aov_year1` comes from `pricing.aov_year1` when `pricing.aov_mode = explicit`, otherwise map `pricing.aov_band` to a numeric pick-point; refine by category/region.
- `aov_inflation` is a flat YoY rate (keep constant). Suggested range: 0–5% unless category suggests otherwise.

#### Gross margin / COGS

- Use `unit_economics.gross_margin_target_pct` (explicit) or map `unit_economics.gross_margin_band` to a concrete GM%.
- Compute: `cogs_pct = 1 - gross_margin_target_pct`.
- Keep `cogs_pct` constant across forecast years (V1).

#### Discounts & promotions

- `discounts_promos_pct` is inferred from category + positioning.
- Keep constant across forecast years (V1). Suggested guardrails:
  - low-discount brands: 0–10%
  - typical: 10–25%
  - promo-heavy: 25–40%

---

### Paid marketing policy

#### CAC → CPC

- Intake: `acquisition.cac_mode` (+ band/explicit) and `acquisition.has_paid_ads_experience`.
- Choose a paid CAC target (or benchmark it if unknown).
- Compute CPC using paid conversion:
  - CPC ≈ CAC_paid × conv_paid (assumes 1 paid click ≈ 1 paid site visit)

#### CPC inflation

- `cpc_inflation` is a flat YoY rate (keep constant).
- Suggested range: 5–15% depending on category/competition and growth ambition.

---

### Fulfilment costs + rent policy

#### Shipping

- `ship_cost_year1` comes from `unit_economics.shipping_plus_packaging_per_order` when `unit_economics.shipping_cost_mode = explicit`, otherwise map `unit_economics.shipping_cost_band` to a numeric pick-point; refine by category/region.
- `ship_inflation` is a flat YoY rate; suggested range: 3–8%.

#### Handling

- `handling_cost_year1` depends strongly on `unit_economics.fulfilment_mode_year1`:
  - self_fulfill: lower, often a smaller % of shipping
  - third_party_fulfillment: higher per order
  - dropship_pod: typically embedded; still include a small handling proxy if needed

#### Warehouse rent

- If fulfilment is `third_party_fulfillment` or `dropship_pod`: set warehouse rent to 0 for all years (V1).
- If `self_fulfill`: introduce warehouse rent only when scale + inventory intensity justify it; start year is often later in the window (e.g., 2028–2029) for aggressive/high-inventory cases.
- Note: `warehouse_rent_start_year` is a calendar year within 2026–2031. If `warehouse_rent_amount_when_active = 0`, the specific start year is economically irrelevant (rent remains 0); pick any valid year deterministically (default to 2026).

#### Office/workspace rent

- Often 0 or a small home-office allocation early.
- Introduce dedicated office rent later based on hiring trajectory and fixed-cost posture.
- Office/warehouse rent inflation is a flat YoY rate; suggested range: 2–6%.
- Note: `office_rent_start_year` is a calendar year within 2026–2031. If `office_rent_amount_when_active = 0`, the specific start year is economically irrelevant (rent remains 0); pick any valid year deterministically (default to 2026).

#### Fixed overhead allocation (important to avoid double counting)

- The intake question `team_overhead.other_fixed_costs_*` is treated as a **non-rent fixed-overhead budget** in Year 1 (software/tools/admin and accounting/legal). It should **not** be treated as a total-overhead budget that includes office or warehouse rent.
- `office_rent_amount_when_active` and `warehouse_rent_amount_when_active` are modeled separately (and can start later). Do **not** back them out of `misc_ga_year1` (i.e., the non-rent overhead budget is independent of rent timing).
- Populate the model’s Year-1 fixed-overhead lines by allocating that budget across:
  - `prof_fees_year1`
  - `misc_ga_year1`

---

### Working capital policy (high level)

- Map customer payment terms to AR days (ecom often near zero).
- Map supplier payment terms to AP days.
- Map inventory intensity to Year-1 inventory days and an inventory turns improvement rate.

---

### Capex + depreciation policy (high level)

- `capex_pct_of_net_rev` is an internal driver (not collected from UI). Keep it stable and modest for pre-launch ecommerce:
  - profit_first: ~0.5–1.5%
  - balanced: ~1–3%
  - growth_first: ~2–5%
  - (adjust slightly by category if physical equipment needs are higher)
- `dep_period_years` is an internal default. Use a typical ecommerce asset life (software + small equipment):
  - default: 3–5 years
  - cap at the `driver_catalog.jsonc` bounds

---

### Financing + tax (high level)

- Financing is one-time equity injection and optional one-time loan at start.
- **Loan start year is fixed in the Excel template**: in this model the loan (if any) can only start in **2026** (Year 1). Do not output or vary a loan start-year driver; vary `initial_loan_amount` instead.
- Use tax country + typical rate unless explicit.

- Equity:
  - If `funding_tax.equity_mode = explicit`: use `funding_tax.equity_injection`.
  - If `funding_tax.equity_mode = suggest`: choose a sensible starting equity level based on early burn + buffer.
- Loan:
  - If `funding_tax.loan_plan = none`: set `initial_loan_amount = 0` and do not create a loan schedule.
  - If `funding_tax.loan_plan = term_loan`:
    - set `initial_loan_amount = funding_tax.loan_amount`
    - set `loan_term_years = funding_tax.loan_term_years`
    - map interest:
      - if `funding_tax.loan_interest_mode = explicit`: `interest_rate = funding_tax.loan_interest_pct`
      - if `funding_tax.loan_interest_mode = band`: choose a representative rate within the band (`5_8`, `8_12`, `gt_12`) consistent with region and stage
- Tax:
  - if `funding_tax.tax_rate_mode = explicit`: `tax_rate = funding_tax.tax_rate_pct`
  - if `funding_tax.tax_rate_mode = typical`: infer a blended effective rate from `business_profile.tax_country`
