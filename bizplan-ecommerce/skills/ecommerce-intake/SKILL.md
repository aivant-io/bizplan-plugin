---
name: ecommerce-intake
description: >
  Guides a pre-launch ecommerce founder through a structured questionnaire to
  collect all inputs needed for a financial model and business plan. Covers
  business basics, growth strategy, demand, pricing, acquisition, unit economics,
  working capital, and funding. Uses conditional branching to minimize cognitive
  load while gathering high-leverage inputs. Outputs a structured intake JSON.
compatibility: None (conversation only).
---

# Ecommerce Intake Questionnaire

## Overview

This skill walks the founder through 26 questions across 8 sections. The questionnaire uses conditional branching — follow-up questions appear only when relevant based on prior answers. The goal is **minimal but high-leverage inputs**, with missing details filled by the ecommerce-assumptions skill using research and benchmarks.

**Output:** Structured intake JSON matching [references/intake_schema.jsonc](references/intake_schema.jsonc).
For full question wording and branching, see [references/intake_questionnaire.md](references/intake_questionnaire.md).

## Conversation Flow

Present questions conversationally, one section at a time. Explain options briefly when helpful. Accept natural language answers and map them to the correct enum values.

### Section 1: Business Basics (Q1-Q4)

**Q1 — Store/brand name**
- Type: Short text
- Ask: "What is your store or brand name (or working name)?"
- If empty: use "Your Store" as placeholder
- Store as: `business_profile.store_name`

**Q2 — Product description**
- Type: Short paragraph
- Ask: "In one or two sentences, what are you selling and who is it for?"
- Motivation (show to founder): "This is the foundation of your entire business plan. A specific answer helps us write a much sharper plan."
- Example (show as hint): "Freeze-dried dog treats made from single-ingredient, human-grade meat for health-conscious pet owners who read ingredient labels."
- Store as: `business_profile.description`

**Q2a — Target customer**
- Type: Short paragraph (1-3 sentences)
- Ask: "Describe your ideal customer — who are they, and what problem or desire does your product solve for them?"
- Motivation: "Your business plan needs a clear picture of who you are selling to. This shapes everything from marketing strategy to pricing."
- Examples:
  - "Millennial moms (ages 28-38) who want clean, organic baby skincare but are overwhelmed by options and don't trust big brands."
  - "Male remote workers aged 25-40 who sit at a desk 8+ hours and want affordable ergonomic accessories that don't look like medical equipment."
- Store as: `business_profile.target_customer`
- If unsure: store as `null` and reassure: "No problem — we'll build a customer profile from market research."

**Q2b — Competitive differentiation**
- Type: Short paragraph (1-3 sentences)
- Ask: "What makes your products different from what customers can already buy? This could be ingredients, design, price, sourcing, experience, or anything else."
- Motivation: "We use this to position your business against competitors in the plan. Even small differences matter."
- Examples:
  - "We source high-end fabrics from Italian mills but sell direct-to-consumer, so we can offer $200 quality at $80 price points."
  - "Most competitors sell generic formulas. We use clinically tested fermented ingredients and publish our lab results on every product page."
- Store as: `business_profile.differentiation`
- If unsure: store as `null` and reassure: "No problem — we'll identify positioning opportunities from market research."

**Q2c — Founder background**
- Type: Short paragraph (1-3 sentences)
- Ask: "What relevant experience or connections do you bring to this business? This could be industry experience, a professional skill, an existing audience, supplier relationships, or personal passion."
- Motivation: "Your background is part of your competitive advantage. The plan will explain why you are the right person to build this business."
- Examples:
  - "I spent 6 years as a buyer for Nordstrom in the accessories category, so I have deep supplier relationships and know what sells."
  - "I'm a licensed esthetician with 12k Instagram followers who already ask me for product recommendations."
- Store as: `business_profile.founder_background`
- If unsure: store as `null` and reassure: "That's completely fine — many successful founders start fresh. We'll focus on other strengths."

**Q2d — Why now**
- Type: Short paragraph (1-3 sentences)
- Ask: "Why is now a good time to launch this business? Think about trends, changes in consumer behavior, new technology, or gaps you've noticed in the market."
- Motivation: "Timing matters. Even a quick observation about a trend you've noticed helps the plan explain why this business makes sense right now."
- Examples:
  - "The clean beauty market is growing 15% year-over-year and big retailers like Target are expanding their clean beauty shelf space."
  - "Remote work has become permanent for millions of people, and most home office furniture is either ugly or expensive — there's a huge gap in the $50-$150 range."
- Store as: `business_profile.why_now`
- If unsure: store as `null` and reassure: "No problem — our market research will identify relevant trends for your category."

**Q3 — Product category**
- Type: Single-select
- Ask: "Which category best describes your main products?"
- Options:
  - Apparel & accessories → `apparel`
  - Beauty & personal care → `beauty_personal_care`
  - Food & beverage → `food_beverage`
  - Home & living → `home_living`
  - Consumer electronics & gadgets → `consumer_electronics`
  - Other physical products → `other_physical_products`
- Store as: `business_profile.category`

**Q4 — Customer region**
- Type: Single-select + optional follow-up
- Ask: "Where will most of your customers live?"
- Options: United States (`US`), Canada (`Canada`), United Kingdom (`UK`), European Union (`EU`), Other (`Other`)
- Store as: `business_profile.customer_region`
- Follow-up: "Will your business be taxed in a different country?"
  - If yes → ask Q4a for tax country
  - If no → `business_profile.tax_country` = same as customer_region

### Section 2: Ambition & Growth Style (Q5-Q6)

**Q5 — Financial priority**
- Ask: "For the next few years, what matters most to you financially?"
- Options:
  - Profit-first (keep burn low, focus on margins) → `profit_first`
  - Balanced (some growth, some profit) → `balanced`
  - Growth-first (happy to invest heavily for faster growth) → `growth_first`
- Store as: `strategy.financial_priority`

**Q6 — Growth ambition**
- Ask: "How ambitious do you want your growth to be over the first 3-5 years?"
- Options: Conservative (`conservative`), Base/realistic (`base`), Aggressive (`aggressive`)
- Store as: `strategy.growth_ambition`

### Section 3: Demand & Orders (Q7)

**Q7 — Year-1 order volume goal**
- Ask: "By the end of Year 1, which best matches your goal for total orders?"
- Options:
  - Test the waters: a few hundred orders (< 1,000) → `lt_1k`
  - Getting going: around 1-5k orders → `1_5k`
  - Serious volume: around 5-20k orders → `5_20k`
  - Very high volume: 20k+ orders → `gt_20k`
- Store as: `demand.year1_orders_bucket`

**Q7b — Repeat purchase expectation**
- Ask: "How often do you expect customers to come back and buy again?"
- Options: None (`none`), Low (`low`), Medium (`medium`), High (`high`)
- Store as: `demand.repeat_expectation`

### Section 4: Customer Spend (Q8-Q9)

**Q8 — AOV mode**
- Ask: "How much do you expect a typical customer to spend per order (before discounts)?"
- Options:
  - "I have a rough number" → `pricing.aov_mode = explicit` → ask Q9a
  - "I'm not sure - estimate for me" → `pricing.aov_mode = band` → ask Q9b

**Q9a — Explicit AOV** (if `aov_mode = explicit`)
- Ask: "Enter your best guess for average order value in Year 1."
- Type: Currency input
- Store as: `pricing.aov_year1`

**Q9b — AOV band** (if `aov_mode = band`)
- Ask: "Roughly where do you expect your average order value to land?"
- Options: < $30 (`lt_30`), $30-$80 (`30_80`), $80-$200 (`80_200`), > $200 (`gt_200`)
- Store as: `pricing.aov_band`

### Section 5: Acquisition & Conversion (Q9-Q11)

**Q9 — Sales platform**
- Ask: "Where will you primarily sell?"
- Options:
  - Own website (Shopify, WooCommerce, etc.) → `dtc_website`
  - Amazon → `amazon`
  - Etsy → `etsy`
  - Multiple channels → `multi_channel`
- Store as: `unit_economics.sales_platform`

**Q10 — Primary acquisition channels**
- Type: Multi-select (up to 2)
- Ask: "Which channels will matter most for acquiring customers in Year 1? (Pick up to 2)"
- Options:
  - Paid ads (Meta, Google, TikTok, etc.) → `paid_ads`
  - Organic & direct (SEO, content, social, influencers) → `organic_direct`
  - Retention (email & SMS) → `retention_email_sms`
  - Not sure - use a standard mix → sets `acquisition.use_standard_mix = true`
- Store as: `acquisition.primary_channels` and `acquisition.use_standard_mix`

**Q11 — Conversion difficulty**
- Ask: "How easy or hard do you expect it to be to convert a visitor into a paying customer?"
- Options:
  - Hard - customers will need a lot of convincing → `hard`
  - Average - similar to a typical online store → `average`
  - Easy - strong demand or niche → `easy`
  - Very easy - strong brand, trust, or urgency → `very_easy`
- Store as: `acquisition.conv_difficulty`

**Q12 — Paid ads experience & CAC**
- Ask: "Have you run paid ads before for this or a similar product?"
- If No → `acquisition.has_paid_ads_experience = false`, `acquisition.cac_mode = none`
- If Yes → ask Q12a:
  - "Roughly how much does it cost in ads to get one paying customer?"
  - Options:
    - < $10/customer → `cac_mode = band`, `cac_band = lt_10`
    - $10-$30/customer → `cac_mode = band`, `cac_band = 10_30`
    - $30-$80/customer → `cac_mode = band`, `cac_band = 30_80`
    - > $80/customer → `cac_mode = band`, `cac_band = gt_80`
    - Custom estimate → `cac_mode = explicit`, ask for `cac_explicit` (numeric)
    - Not sure → `cac_mode = none`

### Section 6: Unit Economics & Fixed Costs (Q12-Q16)

**Q13 — Gross margin**
- Ask: "What gross margin would you like to aim for (after product cost, before shipping and marketing)?"
- Options:
  - "I have a target % in mind" → `gross_margin_mode = explicit` → ask for `gross_margin_target_pct`
  - "I'm not sure" → `gross_margin_mode = band` → ask for band:
    - Low (around 20-40%) → `low`
    - Medium (around 40-60%) → `medium`
    - High (around 60-80%) → `high`

**Q14 — Shipping cost**
- Ask: "What will your average shipping + packaging cost per order be in Year 1?"
- Options:
  - "I have a rough number" → `shipping_cost_mode = explicit` → ask for `shipping_plus_packaging_per_order`
  - "I'm not sure" → `shipping_cost_mode = band` → ask for band:
    - Very low (print-on-demand/dropship) → `very_low`
    - Normal parcel shipping → `normal`
    - High (heavy or bulky items) → `high`

**Q14b — Fulfillment approach**
- Ask: "In Year 1, how do you plan to fulfill customer orders?"
- Options:
  - Self-fulfill → `self_fulfill`
  - Use a 3PL / fulfillment partner → `third_party_fulfillment`
  - Dropship / print-on-demand → `dropship_pod`
  - Not sure → `not_sure`
- Store as: `unit_economics.fulfilment_mode_year1`

**Q15 — Team cost**
- Ask: "In Year 1, what do you expect to spend per year on salaries, wages, and contractors?"
- Options:
  - "I have a rough yearly budget" → `team_cost_mode = explicit` → ask for `team_cost_year1`
  - "I'm not sure - help me estimate" → `team_cost_mode = estimate` → ask:
    - Q15b: Team size → `0_1`, `2_3`, `4_7`, `8_plus`
    - Q15c: Salary level → `low`, `mid`, `high`

**Q16 — Other fixed costs**
- Ask: "In Year 1, what do you expect to spend on everything else fixed (software, tools, accounting, admin)?"
- Options:
  - "I have a rough yearly budget" → `other_fixed_costs_mode = explicit` → ask for `other_fixed_costs_year1`
  - "I'm not sure" → `other_fixed_costs_mode = band` → ask for band:
    - Lean (< $20k/year) → `lean`
    - Moderate ($20-$70k/year) → `moderate`
    - Heavy (> $70k/year) → `heavy`

**Q16b — Overhead inflation**
- Ask: "How quickly do you expect salaries and fixed overhead to increase each year?"
- Options: Stay roughly flat (`flat`), 3-5%/year (`3_5`), 5-10%/year (`5_10`)
- Store as: `team_overhead.overhead_inflation_band`

### Section 7: Inventory & Working Capital (Q17-Q19)

**Q17 — Inventory intensity**
- Ask: "How much inventory do you expect to hold, on average?"
- Options:
  - Don't hold stock (print-on-demand/dropship) → `no_stock`
  - About 1-2 months → `1_2_months`
  - 3+ months → `3_plus_months`
- Store as: `working_capital.inventory_intensity`

**Q18 — Customer payment terms**
- Ask: "When do customers usually pay you?"
- Options:
  - Upfront at checkout → `upfront`
  - Mostly upfront, some pay later → `mostly_upfront`
  - Often on invoice → `invoice`
- Store as: `working_capital.customer_payment_terms`

**Q19 — Supplier payment terms**
- Ask: "How quickly do you expect to pay your suppliers?"
- Options:
  - Within about 15 days → `15_days`
  - Around 30 days → `30_days`
  - Often 45-60 days → `45_60_days`
- Store as: `working_capital.supplier_payment_terms`

### Section 8: Funding & Initial Capital (Q20-Q22)

**Q20 — Initial equity**
- Ask: "How much cash (equity) do you plan to put into the business at the start?"
- Options:
  - "I have a rough amount" → `equity_mode = explicit` → ask for `equity_injection`
  - "I'm not sure - let the model suggest" → `equity_mode = suggest`

**Q21 — Loan**
- Ask: "Do you plan to take a loan at the start (in addition to equity)?"
- If No → `loan_plan = none`, set loan amount to 0
- If Yes → `loan_plan = term_loan` → ask:
  - Q21a: Loan amount (currency)
  - Q21b: Interest rate — band (`5_8`, `8_12`, `gt_12`), custom rate, or "not sure"
  - Q21c: Loan term in years

**Q22 — Tax rate**
- Ask: "What effective corporate tax rate should we assume?"
- Options:
  - "Use a typical rate for my country" → `tax_rate_mode = typical`
  - "I want to enter my own rate" → `tax_rate_mode = explicit` → ask for `tax_rate_pct`

## Output Format

After collecting all answers, output the intake as a JSON object matching the schema in `references/intake_schema.jsonc`. Example structure:

```json
{
  "business_profile": {
    "store_name": "GlowHaus",
    "description": "Clean skincare products for women in their 20s-30s who want transparent ingredients and no synthetic fragrances",
    "target_customer": "Health-conscious women aged 24-35 who read ingredient labels, follow clean beauty influencers, and are willing to pay a premium for transparency",
    "differentiation": "Every product has a publicly available third-party lab report and we use only fermented botanical ingredients",
    "founder_background": "Licensed esthetician with 5 years in a dermatology clinic and 12k Instagram followers who ask for product recommendations",
    "why_now": "Clean beauty growing 15% annually and major retailers expanding shelf space, but most brands still don't publish lab results",
    "category": "beauty_personal_care",
    "customer_region": "US",
    "tax_country": "US"
  },
  "strategy": {
    "financial_priority": "growth_first",
    "growth_ambition": "aggressive"
  },
  "demand": {
    "year1_orders_bucket": "1_5k",
    "repeat_expectation": "low"
  },
  "pricing": {
    "aov_mode": "band",
    "aov_year1": null,
    "aov_band": "30_80"
  },
  "acquisition": {
    "primary_channels": ["paid_ads", "retention_email_sms"],
    "use_standard_mix": false,
    "conv_difficulty": "average",
    "has_paid_ads_experience": true,
    "cac_mode": "band",
    "cac_band": "10_30",
    "cac_explicit": null
  },
  "unit_economics": {
    "gross_margin_mode": "band",
    "gross_margin_target_pct": null,
    "gross_margin_band": "high",
    "shipping_cost_mode": "band",
    "shipping_plus_packaging_per_order": null,
    "shipping_cost_band": "normal",
    "sales_platform": "dtc_website",
    "fulfilment_mode_year1": "not_sure"
  },
  "team_overhead": {
    "team_cost_mode": "estimate",
    "team_cost_year1": null,
    "team_size_bucket": "2_3",
    "salary_level": "mid",
    "other_fixed_costs_mode": "band",
    "other_fixed_costs_year1": null,
    "other_fixed_costs_band": "moderate",
    "overhead_inflation_band": "3_5"
  },
  "working_capital": {
    "inventory_intensity": "1_2_months",
    "customer_payment_terms": "upfront",
    "supplier_payment_terms": "30_days"
  },
  "funding_tax": {
    "equity_mode": "explicit",
    "equity_injection": 80000,
    "loan_plan": "none",
    "loan_amount": null,
    "loan_interest_mode": null,
    "loan_interest_band": null,
    "loan_interest_pct": null,
    "loan_term_years": null,
    "tax_rate_mode": "typical",
    "tax_rate_pct": null
  }
}
```

## Validation Rules

Before passing the intake to the assumptions skill:

1. **Required fields**: `category`, `customer_region`, `financial_priority`, `growth_ambition`, `year1_orders_bucket`, `conv_difficulty`, `equity_mode`
2. **Conditional fields**: If `aov_mode = explicit`, then `aov_year1` must be provided. If `loan_plan = term_loan`, then `loan_amount` must be provided.
3. **Enum validation**: All enum values must match the defined options in the schema
4. **Numeric bounds**: AOV > 0, equity >= 0, loan >= 0, tax rate 0-50%
5. **Null handling**: Fields not applicable based on branching should be `null`, not omitted
6. **Nullable text fields**: `target_customer`, `differentiation`, `founder_background`, and `why_now` may be `null` if the founder is unsure. They should never be omitted from the JSON — use `null` explicitly.
7. **Text length**: Business context fields (Q2a-Q2d) should be 1-3 sentences. If a founder writes a long response, summarize to 3 sentences and confirm with them.

## Conversation Guidelines

- Present one section at a time (not all questions at once)
- Explain technical terms when they appear (e.g., "gross margin", "CAC", "working capital")
- Accept natural language and map to correct enums (e.g., "beauty products" → `beauty_personal_care`)
- If the founder seems unsure, recommend the "estimate for me" / band option
- Summarize all answers at the end and ask for confirmation before proceeding
- Keep the tone founder-friendly — avoid jargon where possible
- For business context questions (Q2a-Q2d), accept "I'm not sure" or "I don't know yet" gracefully — store as `null` and reassure the founder. Do not push for an answer if they genuinely don't have one.
