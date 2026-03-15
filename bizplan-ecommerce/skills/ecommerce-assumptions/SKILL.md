---
name: ecommerce-assumptions
description: >
  Resolves all financial model drivers for a pre-launch ecommerce business from
  founder intake data. Maps qualitative inputs (order volume bands, margin bands,
  difficulty levels) to specific numeric values using curated industry benchmarks
  across 11 product categories and 5 regions. Calculates derived values including
  traffic, CPC, equity needs, and overhead allocation. Use when building ecommerce
  financial models, resolving business plan assumptions, or analyzing ecommerce
  startup financials.
---

# Ecommerce Assumptions Resolution

## Overview

This skill resolves **49 writable financial model drivers** from a founder's intake questionnaire responses. It converts qualitative band selections (e.g., "low margin", "1-5k orders") into specific numeric values using mapping tables, curated benchmark data, and calculation formulas.

**Inputs:** Founder intake JSON (from the ecommerce-intake skill or user-provided data)
**Outputs:** Resolved assumptions JSON — one entry per driver with value, source attribution, and confidence

For full driver definitions (types, bounds, semantics), see [references/driver_catalog.jsonc](references/driver_catalog.jsonc).
For detailed heuristics and category adjustments, see [references/deep_research_policy.md](references/deep_research_policy.md).
For the rationale behind each mapping table value, see [references/heuristic_rationale.md](references/heuristic_rationale.md).

## Script Execution

This skill runs as a Python script — **do not interpret the resolution pipeline manually**. Run:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/resolve_assumptions.py" "$ARGUMENTS"
```

Where `$ARGUMENTS` is the store name. The script reads `{StoreName}_intake.json` from the current working directory and writes `{StoreName}_assumptions.json`.

The script reads all benchmark data from the skill's bundled data files (`data/us/{category}.json`, `data/regional_defaults.json`) and validates outputs against `references/driver_catalog.jsonc`.

## File Inputs & Outputs

**Read from the current working directory:**
- Intake JSON file, named `{StoreName}_intake.json`

**Read from the skill directory (by the script automatically):**
- `${CLAUDE_SKILL_DIR}/data/us/{category}.json` — curated category benchmarks (category from intake JSON)
- `${CLAUDE_SKILL_DIR}/data/regional_defaults.json` — regional tax rates, salary multipliers
- `${CLAUDE_SKILL_DIR}/references/driver_catalog.jsonc` — driver definitions and bounds

**Write to the current working directory:**
- `{StoreName}_assumptions.json` — resolved assumptions with all 49 drivers

## Resolution Pipeline

Follow these steps in order. Each step may depend on values resolved in prior steps.

### Step 1: Extract User Inputs

Read the intake JSON. Extract values for: `product_category`, `customer_region`, `sales_platform`, `year1_orders_bucket`, `growth_ambition`, `financial_priority`, `aov_band` (or explicit), `gross_margin_band` (or explicit), `conv_difficulty`, `primary_channels`, `cac_mode`, `cac_band` (or explicit), `shipping_cost_band`, `fulfilment_mode`, `inventory_intensity`, `customer_payment_terms`, `supplier_payment_terms`, `team_size_bucket`, `salary_level`, `fixed_costs_band`, `overhead_inflation_band`, `repeat_expectation`, `equity_mode`, `loan_amount`, `loan_interest_band`, `loan_term_years`.

### Step 2: Load Curated Benchmarks

Read the benchmark file for the user's category from `data/us/{category}.json`. These contain sourced industry averages for conversion rates, AOV, margins, CAC, and other metrics. Use these to validate and adjust resolved values.

### Step 3: Resolve Internal Targets

These are computed first because other drivers depend on them.

**3a. Year-1 Orders Target** — Map `year1_orders_bucket` + `growth_ambition`:

| Bucket   | Conservative | Base    | Aggressive |
|----------|-------------|---------|------------|
| lt_1k    | 300         | 700     | 1,000      |
| 1_5k     | 1,500       | 3,000   | 5,000      |
| 5_20k    | 6,000       | 12,000  | 20,000     |
| gt_20k   | 25,000      | 40,000  | 60,000     |

**3b. Gross Margin Target** — Use explicit value if provided, otherwise map band:

| Band   | Margin |
|--------|--------|
| low    | 0.35   |
| medium | 0.50   |
| high   | 0.65   |

**3c. Fulfillment Mode Resolution** — If `not_sure`, resolve:
- `inventory_intensity = no_stock` → `dropship_pod`
- `inventory_intensity = 3_plus_months` → `third_party`
- `aggressive` ambition AND orders in `5_20k`/`gt_20k` → `third_party`
- Otherwise → `self_fulfill`

**3d. CAC Paid Target** — Use explicit value if provided, otherwise map band:

| Band   | CAC ($) |
|--------|---------|
| lt_10  | 7.50    |
| 10_30  | 20.00   |
| 30_80  | 55.00   |
| gt_80  | 100.00  |

**3e. Fixed Costs Total** — Map `fixed_costs_band`:

| Band     | Annual ($) |
|----------|-----------|
| lean     | 6,000     |
| moderate | 18,000    |
| heavy    | 42,000    |

### Step 4: Resolve Conversion Rates

Map `conv_difficulty` to baseline rates:

| Difficulty | conv_paid | conv_organic | conv_retention |
|-----------|-----------|-------------|----------------|
| hard      | 0.010     | 0.020       | 0.080          |
| average   | 0.015     | 0.030       | 0.100          |
| easy      | 0.020     | 0.040       | 0.120          |
| very_easy | 0.025     | 0.050       | 0.150          |

**Hierarchy rule:** Always maintain `retention > organic > paid`.

### Step 5: Derive Channel Mix

**Base weights by financial_priority:**

| Priority     | Paid | Organic | Retention |
|-------------|------|---------|-----------|
| profit_first | 0.25 | 0.35    | 0.40      |
| balanced     | 0.40 | 0.35    | 0.25      |
| growth_first | 0.55 | 0.30    | 0.15      |

**Adjustment algorithm:**
1. Start with base weights for the user's `financial_priority`
2. If `paid_ads` NOT in `primary_channels`: set paid = 0
3. Boost selected channels: organic × 1.2 if selected, retention × 1.3 if selected, paid × 1.1 if selected
4. Floor unselected: organic min 10% (× 0.6), retention min 5% (× 0.5)
5. **Normalize all three to sum = 1.0** (divide each by total)

If no paid: fallback split is organic=0.60, retention=0.40.

### Step 6: Calculate Traffic

```
weighted_conv = mix_paid × conv_paid + mix_organic × conv_organic + mix_retention × conv_retention
traffic_total_year1 = round(total_orders_year1_target / weighted_conv)
```

### Step 7: Resolve Order Economics

**AOV** — Use explicit value or map band:

| Band   | AOV ($) |
|--------|---------|
| lt_30  | 25      |
| 30_80  | 55      |
| 80_200 | 140     |
| gt_200 | 275     |

**COGS:** `cogs_pct = 1.0 - gross_margin_target_pct`

**Discount/Promo Rate** by financial_priority:

| Priority     | Default % |
|-------------|----------|
| profit_first | 0.05     |
| balanced     | 0.10     |
| growth_first | 0.20     |

**Return Rate** by category:

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

**Payment Processing Fee** by platform:

| Platform      | Fee   |
|--------------|-------|
| dtc_website   | 0.029 |
| amazon        | 0.00  |
| etsy          | 0.029 |
| multi_channel | 0.015 |

**Platform Fee** by platform:

| Platform      | Fee  |
|--------------|------|
| dtc_website   | 0.00 |
| amazon        | 0.15 |
| etsy          | 0.065|
| multi_channel | 0.08 |

**Shipping Cost** — Map band:

| Band     | $/order |
|----------|---------|
| very_low | 4       |
| normal   | 8       |
| high     | 15      |

**Handling Cost** — By resolved fulfillment mode:

| Mode          | Formula                          |
|--------------|----------------------------------|
| self_fulfill  | max($1.00, 10% of ship_cost)     |
| third_party   | max($2.50, 30% of ship_cost)     |
| dropship_pod  | max($0.50, 5% of ship_cost)      |

**Packaging Cost Per Order** — By category type:

| Category type | $/order | Categories |
|--------------|---------|-----------|
| lightweight/simple | 1.50 | beauty_personal_care, health_wellness, jewelry_accessories, food_beverage |
| standard | 2.50 | home_garden, pets, toys_kids, electronics_gadgets, other |
| bulky/fragile | 4.00 | sports_outdoors, fashion_apparel |

**Support Cost Per Order** — By platform:

| Platform      | $/order |
|--------------|---------|
| dtc_website   | 1.50    |
| amazon        | 0.50    |
| etsy          | 1.00    |
| multi_channel | 1.75    |

**Repeat Purchase** — By expectation:

| Expectation | Rate | Frequency |
|------------|------|-----------|
| none       | 0.00 | 1.0       |
| low        | 0.10 | 1.5       |
| medium     | 0.25 | 2.5       |
| high       | 0.40 | 4.0       |

**Retention Improvement** — By ambition: conservative=0.03, base=0.05, aggressive=0.08

**COGS Improvement** — By ambition: conservative=0.005, base=0.01, aggressive=0.02

### Step 8: Resolve Marketing Drivers

**CPC:** `cpc_year1 = cac_paid_target × conv_paid`

**CPC Inflation** by ambition: conservative=0.06, base=0.08, aggressive=0.12

**Traffic YoY Growth** by ambition (use mid-point): conservative=0.10, base=0.225, aggressive=0.45

### Step 9: Resolve G&A

**Team Cost:** `headcount × base_salary × 1.25 burden_multiplier`

Headcount by bucket: 0_1=0.5, 2_3=2.5, 4_7=5.5, 8_plus=10.0
Base salary: low=$40k, mid=$65k, high=$100k

**Months to Full Team:** 0_1=0, 2_3=3, 4_7=6, 8_plus=9

**Monthly SaaS Costs** by platform: dtc=$250, amazon=$100, etsy=$50, multi_channel=$350

**Fixed Overhead Allocation:**
```
prof_fees_year1 = fixed_costs_total × 0.40
misc_ga_year1 = fixed_costs_total × 0.60 - (monthly_saas × 12)
```
Ensure misc_ga_year1 does not go negative. If it would, set misc_ga_year1 = 0.

**Overhead Inflation** — Map band: flat=0.00, 3_5=0.04, 5_10=0.075

**Warehouse Rent** — By team size and inventory:

| Condition | Annual ($) |
|-----------|-----------|
| no_stock (dropship/POD) | 0 |
| 0_1 team + 1_2_months inventory | 0 |
| 2_3 team OR 3_plus_months inventory | 12,000 |
| 4_7 team | 24,000 |
| 8_plus team | 42,000 |

**Office Rent** — Pre-launch ecommerce works remotely:

| Condition | Annual ($) |
|-----------|-----------|
| team_size_bucket < 8_plus | 0 |
| team_size_bucket = 8_plus | 18,000 |

**Rent Start Years** — If rent amount = 0, default to 2026. Otherwise:
- Conservative: start year = 2028 (2-year delay)
- Aggressive with heavy inventory: start year = 2027 (1-year delay)
- Aggressive without heavy inventory: start year = 2026
- Base: start year = 2027 (1-year delay)
- Cap at 2031.

**Rent/Ship Inflation Defaults:** rent_inflation=0.03, ship_inflation=0.06, aov_inflation=0.025

### Step 10: Resolve Working Capital

**AR Days** — By customer payment terms: upfront=0, mostly_upfront=3, invoice=30

**AP Days** — By supplier terms: 15_days=15, 30_days=30, 45_60_days=52.5

**Inventory Days** — By intensity: no_stock=0, 1_2_months=45, 3_plus_months=120

**Inventory Improvement** — By intensity: no_stock=0.00, 1_2_months=0.05, 3_plus_months=0.08

### Step 11: Resolve Capex & Depreciation

**Capex %** by financial priority (use mid-point): profit_first=0.01, balanced=0.02, growth_first=0.035

**Depreciation Period:** If capex% < 1.5% → 3 years; if > 3.5% → 5 years; else → 4 years

### Step 12: Resolve Financing

**Loan Amount:** Use user's explicit value (0 if no loan)
**Loan Start Year:** Always 2026 (fixed, not variable — do NOT write to Excel)
**Loan Interest Rate** — Map band: 5_8=0.065, 8_12=0.10, gt_12=0.14
**Loan Term:** Use user's value (default 5 years if not specified)

**Tax Rate** by region (aligned with regional_defaults.json): US=0.26, UK=0.19, EU=0.213, CA=0.122, AU=0.25, other=0.25

**Equity** — If `equity_mode = explicit`: use user's stated amount.
If `equity_mode = suggest`: calculate using the equity suggestion algorithm:

```
annual_fixed = team_cost_year1 + fixed_overhead_year1
annual_variable = estimated_marketing + estimated_fulfillment
effective_annual = annual_fixed + (annual_variable × 0.6)
monthly_burn = effective_annual / 12

runway_months = {conservative: 6, base: 9, aggressive: 12}
buffer = 1.15

equity_needed = monthly_burn × runway_months × buffer - loan_amount
equity_final = max($10,000, round(equity_needed to nearest $1,000))
```

For estimated_marketing: `traffic_paid × cpc_year1` where `traffic_paid = traffic_total × mix_paid`
For estimated_fulfillment: `total_orders × (ship_cost + handling_cost)`

### Step 13: Validate All Values

Before outputting, validate every driver against `references/driver_catalog.jsonc`:

- **Type check:** int, float, float_pct, currency, year — use correct type
- **Bounds check:** All values within `min_value` / `max_value`
- **Sum-to-1:** `traffic_mix_paid_pct + traffic_mix_organic_pct + traffic_mix_retention_pct = 1.0` (±0.01)
- **Year range:** All year drivers between 2026–2031
- **Conversion hierarchy:** retention ≥ organic ≥ paid (soft check, warn if violated)
- **Percentages as decimals:** 0.15 for 15%, NOT 15

### Step 14: Output Resolved Assumptions

Output a JSON object with two sections:

**`inputs`** — Array of 49 entries (one per writable driver):
```json
{
  "input_id": "traffic_total_year1",
  "value": 46667,
  "source": "user_band_inferred",
  "confidence": 0.8,
  "notes": "Derived: 700 orders / 0.015 weighted conv"
}
```

Source values: `user_explicit`, `user_band_inferred`, `category_benchmark`, `research_estimate`

**`__internal_targets`** — Internal anchors (NOT written to Excel):
```json
{
  "total_orders_year1_target": 700,
  "gross_margin_target_pct": 0.50,
  "fulfilment_mode_year1_resolved": "self_fulfill",
  "cac_paid_target": 20.0,
  "other_fixed_costs_year1_total": 18000,
  "equity_mode": "suggest",
  "equity_suggestion": {
    "annual_fixed": 233125,
    "annual_variable": 71712,
    "effective_annual_burn": 276152,
    "monthly_burn": 23013,
    "runway_months": 12,
    "buffer_multiplier": 1.15,
    "loan_offset": 0,
    "initial_estimate": 318000
  }
}
```

When `equity_mode = "explicit"`, omit the `equity_suggestion` object and record just the mode:
```json
{
  "equity_mode": "explicit"
}
```

## Critical Rules

1. **Percentages are ALWAYS decimals:** Write 0.15 for 15%, not 15
2. **Currency values are plain numbers:** Write 50000, not "$50,000"
3. **Years are calendar years:** 2026–2031, not Year 1–Year 6
4. **Never guess cell addresses:** Cell mapping is handled by the financial-model skill
5. **Flat-by-design:** Growth rates are single YoY rates held constant across all years
6. **No double-counting:** Fixed overhead (prof_fees + misc_ga) is SEPARATE from rent
7. **Loan start year is always 2026:** It exists in driver_catalog but is NOT in input_map (not written to Excel)
8. **Start-year defaults:** When rent/warehouse amount = 0, always use 2026 (economically irrelevant)
