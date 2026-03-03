# E‑Commerce V1 – Onboarding Question Flow

This document defines the finalized list of questions for the **V1 e‑commerce business plan + model generator**, including:

- The exact question wording as it should appear in the UI
- Response type / options
- Where branching occurs (follow‑up questions shown conditionally)

The goal is: **minimal but high‑leverage inputs**, optimized for early‑stage / pre‑launch e‑commerce founders. Missing details will be filled using a deep‑research agent and internal defaults.

---

## Section 1 – Business Basics

**Q1 – Store / brand name**

- **Type:** Short text input
- **Prompt:** `What is your store or brand name (or working name)?`
- **Branching:** None
- **If empty:** Use a generic name like "Your Store" in the written plan.

---

**Q2 – What are you selling?**

- **Type:** Short paragraph input
- **Prompt:** `In one or two sentences, what are you selling and who is it for?`
- **Motivation text:** `This is the foundation of your entire business plan. A specific answer helps us write a much sharper plan.`
- **Example:** `Freeze-dried dog treats made from single-ingredient, human-grade meat for health-conscious pet owners who read ingredient labels.`
- **Branching:** None
- **Usage:** Core context for the business plan narrative and for the deep‑research agent (to infer category nuances).
- **Stored as:** `business_profile.description` (string)

---

**Q2a – Target customer**

- **Type:** Short paragraph (1-3 sentences)
- **Prompt:** `Describe your ideal customer — who are they, and what problem or desire does your product solve for them?`
- **Motivation text:** `Your business plan needs a clear picture of who you are selling to. This shapes everything from marketing strategy to pricing.`
- **Examples:**
  - `Millennial moms (ages 28-38) who want clean, organic baby skincare but are overwhelmed by options and don't trust big brands.`
  - `Male remote workers aged 25-40 who sit at a desk 8+ hours and want affordable ergonomic accessories that don't look like medical equipment.`
- **Branching:** If founder says "I'm not sure" → store as `null` and reassure: "No problem — we'll build a customer profile from market research."
- **Usage:** Feeds the Business Overview target customer persona paragraph and shapes market research queries.
- **Stored as:** `business_profile.target_customer` (string | null)

---

**Q2b – Competitive differentiation**

- **Type:** Short paragraph (1-3 sentences)
- **Prompt:** `What makes your products different from what customers can already buy? This could be ingredients, design, price, sourcing, experience, or anything else.`
- **Motivation text:** `We use this to position your business against competitors in the plan. Even small differences matter.`
- **Examples:**
  - `We source high-end fabrics from Italian mills but sell direct-to-consumer, so we can offer $200 quality at $80 price points.`
  - `Most competitors sell generic formulas. We use clinically tested fermented ingredients and publish our lab results on every product page.`
- **Branching:** If founder says "I'm not sure" → store as `null` and reassure: "No problem — we'll identify positioning opportunities from market research."
- **Usage:** Anchors the competitive positioning paragraphs in Business Overview and Market Opportunity sections.
- **Stored as:** `business_profile.differentiation` (string | null)

---

**Q2c – Founder background**

- **Type:** Short paragraph (1-3 sentences)
- **Prompt:** `What relevant experience or connections do you bring to this business? This could be industry experience, a professional skill, an existing audience, supplier relationships, or personal passion.`
- **Motivation text:** `Your background is part of your competitive advantage. The plan will explain why you are the right person to build this business.`
- **Examples:**
  - `I spent 6 years as a buyer for Nordstrom in the accessories category, so I have deep supplier relationships and know what sells.`
  - `I'm a licensed esthetician with 12k Instagram followers who already ask me for product recommendations.`
- **Branching:** If founder says "I don't have industry experience" or similar → store as `null` and reassure: "That's completely fine — many successful founders start fresh. We'll focus on other strengths."
- **Usage:** Feeds the Business Overview founder/team paragraph. If null, paragraph is omitted entirely.
- **Stored as:** `business_profile.founder_background` (string | null)

---

**Q2d – Why now**

- **Type:** Short paragraph (1-3 sentences)
- **Prompt:** `Why is now a good time to launch this business? Think about trends, changes in consumer behavior, new technology, or gaps you've noticed in the market.`
- **Motivation text:** `Timing matters. Even a quick observation about a trend you've noticed helps the plan explain why this business makes sense right now.`
- **Examples:**
  - `The clean beauty market is growing 15% year-over-year and big retailers like Target are expanding their clean beauty shelf space.`
  - `Remote work has become permanent for millions of people, and most home office furniture is either ugly or expensive — there's a huge gap in the $50-$150 range.`
- **Branching:** If founder says "I'm not sure" → store as `null` and reassure: "No problem — our market research will identify relevant trends for your category."
- **Usage:** Anchors the "Why now" paragraph in Business Overview and supports the Market Opportunity narrative.
- **Stored as:** `business_profile.why_now` (string | null)

---

**Q3 – Main product category**

- **Type:** Single‑select dropdown
- **Prompt:** `Which category best describes your main products?`
- **Options:**
  - `Apparel & accessories` (`apparel`)
  - `Beauty & personal care` (`beauty_personal_care`)
  - `Food & beverage` (`food_beverage`)
  - `Home & living` (`home_living`)
  - `Consumer electronics & gadgets` (`consumer_electronics`)
  - `Other physical products` (`other_physical_products`)
- **Branching:** None
- **If "Other physical products" is selected:** Deep‑research agent uses generic e‑commerce benchmarks.
- **Stored as:** `business_profile.category` (enum)

---

**Q4 – Customer region (and tax base override)**

- **Type:** Single‑select + optional sub‑question
- **Prompt (main):** `Where will most of your customers live?`
- **Options (main):**

  - `United States` (`US`)
  - `Canada` (`Canada`)
  - `United Kingdom` (`UK`)
  - `European Union` (`EU`)
  - `Other` (`Other`)

- **Prompt (optional toggle inside the same block):**  
  `Will your business be taxed in a different country than your main customers?`

  - Options:
    - `No, use this country for tax as well` (default)
    - `Yes – my tax home is different`

- **Branching:**

  - If user selects `Yes – my tax home is different`, show:
    - **Q4a – Tax country**
      - **Type:** Country dropdown or text input
      - **Prompt:** `Which country will this business be taxed in?`

- **Usage:** Sets base region for benchmarks (conversion, AOV, shipping, salaries) and tax rate.
- **Stored as:** `business_profile.customer_region` (enum) and optional `business_profile.tax_country` (enum/string)

---

## Section 2 – Ambition & Growth Style

**Q5 – Financial priority**

- **Type:** Single‑select
- **Prompt:** `For the next few years, what matters most to you financially?`
- **Options:**
  - `Profit‑first (keep burn low, focus on margins)` (`profit_first`)
  - `Balanced (some growth, some profit)` (`balanced`)
  - `Growth‑first (happy to invest heavily for faster growth)` (`growth_first`)
- **Branching:** None
- **Usage:** Guides how aggressive growth, marketing spend, and burn can be.
- **Stored as:** `strategy.financial_priority` (enum)

---

**Q6 – Growth ambition for the first few years**

- **Type:** Single‑select
- **Prompt:** `How ambitious do you want your growth to be over the first 3–5 years?`
- **Options:**
  - `Conservative` (`conservative`)
  - `Base / realistic` (`base`)
  - `Aggressive` (`aggressive`)
- **Branching:** None
- **Usage:** Deep‑research + model agent translate this into a Year‑1 growth profile and a starting range for annual traffic / orders growth.
- **Stored as:** `strategy.growth_ambition` (enum)

---

## Section 3 – Demand & Orders

**Q7 – Year‑1 order volume goal (bucket)**

- **Type:** Single‑select
- **Prompt:** `By the end of Year 1, which best matches your goal for total orders?`
- **Options:**
  - `Test the waters: a few hundred orders (< 1,000)` (`lt_1k`)
  - `Getting going: around 1–5k orders` (`1_5k`)
  - `Serious volume: around 5–20k orders` (`5_20k`)
  - `Very high volume: 20k+ orders` (`gt_20k`)
- **Branching:** None
- **Usage:** Used to estimate Year‑1 order count, which is then translated into traffic using conversion assumptions.
- **Stored as:** `demand.year1_orders_bucket` (enum)

---

## Section 4 – Customer Spend (AOV)

**Q8 – Do you know your typical order value?**

- **Type:** Single‑select (with follow‑up)
- **Prompt:** `How much do you expect a typical customer to spend per order (before discounts)?`
- **Options:**

  - `I have a rough number` → sets `pricing.aov_mode = explicit`
  - `I'm not sure – estimate for me` → sets `pricing.aov_mode = band`

- **Branching:**

  - If `I have a rough number`:

    **Q9a – Typical order value (Year 1)**

    - **Type:** Numeric currency input
    - **Prompt:** `Enter your best guess for average order value in Year 1 (before discounts).`

  - If `I'm not sure – estimate for me`:

    **Q9b – Order value range**

    - **Type:** Single‑select
    - **Prompt:** `Roughly where do you expect your average order value to land?`
    - **Options:**
      - `< $30`
      - `$30–$80`
      - `$80–$200`
      - `> $200`

- **Usage:** Sets Year‑1 AOV; deep‑research agent refines it using category + region.
- **Stored as:** `pricing.aov_mode` plus `pricing.aov_year1` (if explicit) or `pricing.aov_band` (if band)

---

## Section 5 – Acquisition & Conversion

**Q9 – Main acquisition channels (Year 1)**

- **Type:** Multi‑select (choose up to 2)
- **Prompt:** `Which channels will matter most for acquiring customers in Year 1? (Pick up to 2)`
- **Options:**

  - `Paid ads (Meta, Google, TikTok, etc.)` (`paid_ads`)
  - `Organic & direct (SEO, content, social, influencers)` (`organic_direct`)
  - `Retention (email & SMS)` (`retention_email_sms`)
  - `Not sure – use a standard mix` → sets `acquisition.use_standard_mix = true`

- **Branching / usage:**
  - If `Not sure – use a standard mix` is selected:
    - Ignore other selections and use a default channel mix for their category + region.
  - Otherwise:
    - Use the chosen channels + Q5 (financial priority) to infer the % split across:
      - Paid acquisition
      - Organic & direct
      - Retention (email & SMS)
- **Stored as:** `acquisition.primary_channels` (enum list) and `acquisition.use_standard_mix` (bool)

---

**Q10 – How hard will it be to convert visitors to first‑time buyers?**

- **Type:** Single‑select
- **Prompt:** `How easy or hard do you expect it to be to convert a visitor into a paying customer (first purchase)?`
- **Options:**

  - `Hard – customers will need a lot of convincing` (`hard`)
  - `Average – similar to a typical online store` (`average`)
  - `Easy – strong demand or niche` (`easy`)
  - `Very easy – strong brand, trust, or urgency` (`very_easy`)

- **Branching:** None
- **Usage:** Determines the overall conversion assumptions; model agent sets per‑channel conversion rates with sensible relative levels (retention > organic > paid).
- **Stored as:** `acquisition.conv_difficulty` (enum)

---

**Q11 – Experience with paid ads & CAC**

- **Type:** Single‑select (with optional follow‑up)
- **Prompt:** `Have you run paid ads before for this or a similar product?`
- **Options:**

  - `Yes` → sets `acquisition.has_paid_ads_experience = true`
  - `No` → sets `acquisition.has_paid_ads_experience = false` and `acquisition.cac_mode = none`

- **Branching:**

  - If `Yes`:

    **Q11a – Rough customer acquisition cost (CAC)**

    - **Type:** Single‑select (with optional numeric)
    - **Prompt:** `Roughly how much does it cost you in ads to get one paying customer (CAC)?`
    - **Options:**
      - `< $10 per customer` (`lt_10`) → sets `acquisition.cac_mode = band`
      - `$10–$30 per customer` (`10_30`) → sets `acquisition.cac_mode = band`
      - `$30–$80 per customer` (`30_80`) → sets `acquisition.cac_mode = band`
      - `> $80 per customer` (`gt_80`) → sets `acquisition.cac_mode = band`
      - `I want to enter a custom estimate` → reveals numeric input and sets `acquisition.cac_mode = explicit`
      - `I'm not sure` → sets `acquisition.cac_mode = none`

- **If Q11 == "No" or Q11a is skipped / "I'm not sure":**  
  Deep‑research agent sets CAC/CPC assumptions using category + region + growth style.

- **Usage:** Translates into CPC / CAC assumptions that drive paid acquisition costs in the model.
- **Stored as:** `acquisition.has_paid_ads_experience` (bool), `acquisition.cac_mode` (enum), and either `acquisition.cac_band` (if band) or `acquisition.cac_explicit` (if explicit)

---

## Section 6 – Unit Economics & Fixed Costs

**Q12 – Gross margin target**

- **Type:** Single‑select (with follow‑up)
- **Prompt:** `What gross margin would you like to aim for on your products (after product cost, before shipping and marketing)?`
- **Options:**

  - `I have a target % in mind` → sets `unit_economics.gross_margin_mode = explicit`
  - `I'm not sure – pick a typical range for my category` → sets `unit_economics.gross_margin_mode = band`

- **Branching:**

  - If `I have a target % in mind`:

    **Q13a – Gross margin target (%)**

    - **Type:** Percent input
    - **Prompt:** `Enter your target gross margin (e.g. 60%).`
    - **Stored as:** `unit_economics.gross_margin_target_pct` (number)

  - If `I'm not sure – pick a typical range for my category`:

    **Q13b – Gross margin band**

    - **Type:** Single‑select
    - **Prompt:** `Roughly which margin band feels right for your products?`
    - **Options:**
      - `Low (around 20–40%)` (`low`)
      - `Medium (around 40–60%)` (`medium`)
      - `High (around 60–80%)` (`high`)
    - **Stored as:** `unit_economics.gross_margin_band` (enum)

- **Usage:** Converted to `Cost of goods sold %` in the model.
- **Stored as:** `unit_economics.gross_margin_mode` plus either `unit_economics.gross_margin_target_pct` (if explicit) or `unit_economics.gross_margin_band` (if band)

---

**Q13 – Shipping & packaging cost per order (Year 1)**

- **Type:** Single‑select (with follow‑up)
- **Prompt:** `What will your average shipping + packaging cost per order be in Year 1?`
- **Options:**

  - `I have a rough number` → sets `unit_economics.shipping_cost_mode = explicit`
  - `I'm not sure – estimate for me` → sets `unit_economics.shipping_cost_mode = band`

- **Branching:**

  - If `I have a rough number`:

    **Q14a – Shipping + packaging per order (Year 1)**

    - **Type:** Numeric currency input
    - **Stored as:** `unit_economics.shipping_plus_packaging_per_order` (number)

  - If `I'm not sure – estimate for me`:

    **Q14b – Shipping & packaging cost band**

    - **Type:** Single‑select
    - **Prompt:** `Which of these best describes your products and shipping?`
    - **Options:**
      - `Very low (print‑on‑demand / dropship)` (`very_low`)
      - `Normal parcel shipping` (`normal`)
      - `High (heavy or bulky items)` (`high`)
    - **Stored as:** `unit_economics.shipping_cost_band` (enum)

- **Usage:** Sets shipping/fulfilment cost per order; deep‑research + category refine the exact value.
- **Stored as:** `unit_economics.shipping_cost_mode` plus either `unit_economics.shipping_plus_packaging_per_order` (if explicit) or `unit_economics.shipping_cost_band` (if band)

---

**Q13c – Fulfilment approach (Year 1)**

- **Type:** Single‑select
- **Prompt:** `In Year 1, how do you plan to fulfill customer orders?`
- **Options:**
  - `I’ll fulfill myself (from home / small space)` (`self_fulfill`)
  - `Use a 3PL / fulfillment partner` (`third_party_fulfillment`)
  - `Dropship / print‑on‑demand` (`dropship_pod`)
  - `Not sure` (`not_sure`)
- **Branching:** None
- **Usage:** Guides handling-cost assumptions and whether/when warehouse rent is introduced.
- **Stored as:** `unit_economics.fulfilment_mode_year1` (enum)

---

**Q14 – Team cost (salaries, wages & contractors) in Year 1**

- **Type:** Single‑select (with follow‑up)
- **Prompt:** `In Year 1, what do you expect to spend per year on salaries, wages, and contractors (including yourself)?`
- **Options:**

  - `I have a rough yearly budget` → sets `team_overhead.team_cost_mode = explicit`
  - `I'm not sure – estimate using a few bands (team size + salary level)` → sets `team_overhead.team_cost_mode = estimate`
  - `I'm not sure – help me estimate` → sets `team_overhead.team_cost_mode = estimate`

- **Branching:**

  - If `I have a rough yearly budget`:

    **Q15a – Team cost – Year 1**

    - **Type:** Numeric currency input
    - **Stored as:** `team_overhead.team_cost_year1` (number)

  - If `I'm not sure – help me estimate`:

    **Q15b – Team size**

    - **Type:** Single‑select
    - **Prompt:** `Roughly how many full‑time people (including you) do you expect in Year 1?`
    - **Options:**
      - `0–1` (`0_1`)
      - `2–3` (`2_3`)
      - `4–7` (`4_7`)
      - `8+` (`8_plus`)
    - **Stored as:** `team_overhead.team_size_bucket` (enum)

    **Q15c – Typical salary level for these roles**

    - **Type:** Single‑select
    - **Prompt:** `Roughly what salary level fits your team (for your region)?`
    - **Options:**
      - `Lower cost (junior roles, emerging market)` (`low`)
      - `Mid‑range` (`mid`)
      - `Higher cost (senior roles or expensive market)` (`high`)
    - **Stored as:** `team_overhead.salary_level` (enum)

- **Usage:** Used to estimate and then set `Salaries, wages & benefits – Year 1`.
- **Stored as:** `team_overhead.team_cost_mode` plus either `team_overhead.team_cost_year1` (if explicit) or (`team_overhead.team_size_bucket` + `team_overhead.salary_level`) (if estimate)

---

**Q15 – Other fixed operating costs in Year 1**

- **Type:** Single‑select (with follow‑up)
- **Prompt:** `In Year 1, what do you expect to spend per year on everything else fixed (software, tools, rent, accounting, admin, etc.)?`
- **Options:**

  - `I have a rough yearly budget` → sets `team_overhead.other_fixed_costs_mode = explicit`
  - `I'm not sure – estimate for me` → sets `team_overhead.other_fixed_costs_mode = band`

- **Branching:**

  - If `I have a rough yearly budget`:

    **Q16a – Other fixed costs – Year 1**

    - **Type:** Numeric currency input
    - **Stored as:** `team_overhead.other_fixed_costs_year1` (number)

  - If `I'm not sure – estimate for me`:

    **Q16b – Cost band**

    - **Type:** Single‑select
    - **Prompt:** `Which range feels closest to your situation?`
    - **Options:**
      - `Lean stack (< $20k per year)` (`lean`)
      - `Moderate tools & rent ($20k–$70k per year)` (`moderate`)
      - `Heavy fixed costs (> $70k per year)` (`heavy`)
    - **Stored as:** `team_overhead.other_fixed_costs_band` (enum)

- **Usage:** Allocated across rent / professional fees / misc within the model.
- **Stored as:** `team_overhead.other_fixed_costs_mode` plus either `team_overhead.other_fixed_costs_year1` (if explicit) or `team_overhead.other_fixed_costs_band` (if band)

---

**Q16 – Salaries & overhead inflation**

- **Type:** Single‑select
- **Prompt:** `How quickly do you expect salaries and fixed overhead to increase each year?`
- **Options:**
  - `Stay roughly flat` (`flat`)
  - `Increase by about 3–5% per year` (`3_5`)
  - `Increase by about 5–10% per year` (`5_10`)
- **Branching:** None
- **Usage:** Sets inflation on salaries and overhead assumptions.
- **Stored as:** `team_overhead.overhead_inflation_band` (enum)

---

## Section 7 – Inventory & Working Capital

**Q17 – Inventory intensity**

- **Type:** Single‑select
- **Prompt:** `How much inventory do you expect to hold, on average?`
- **Options:**
  - `We don't really hold stock (print‑on‑demand / dropship)` (`no_stock`)
  - `About 1–2 months of stock on hand` (`1_2_months`)
  - `Often 3+ months of stock on hand` (`3_plus_months`)
- **Branching:** None
- **Usage:** Sets initial inventory days and improvement assumption over time.
- **Stored as:** `working_capital.inventory_intensity` (enum)

---

**Q18 – When do customers pay you?**

- **Type:** Single‑select
- **Prompt:** `When do customers usually pay you?`
- **Options:**
  - `Upfront at checkout (card / PayPal, etc.)` (`upfront`)
  - `Mostly upfront, some pay later` (`mostly_upfront`)
  - `Often on invoice / payment terms` (`invoice`)
- **Branching:** None
- **Usage:** Sets accounts receivable days (very low vs moderate vs higher).
- **Stored as:** `working_capital.customer_payment_terms` (enum)

---

**Q19 – When do you pay suppliers?**

- **Type:** Single‑select
- **Prompt:** `How quickly do you expect to pay your suppliers?`
- **Options:**
  - `Quickly (within about 15 days)` (`15_days`)
  - `Around 30 days` (`30_days`)
  - `Often 45–60 days` (`45_60_days`)
- **Branching:** None
- **Usage:** Sets accounts payable days.
- **Stored as:** `working_capital.supplier_payment_terms` (enum)

---

## Section 8 – Funding & Initial Capital

**Q20 – Initial equity injection**

- **Type:** Single‑select (with follow‑up)
- **Prompt:** `How much cash (equity) do you plan to put into the business at the start?`
- **Options:**

  - `I have a rough amount` → sets `funding_tax.equity_mode = explicit`
  - `I'm not sure – let the model suggest a starting amount` → sets `funding_tax.equity_mode = suggest`

- **Branching:**

  - If `I have a rough amount`:

    **Q21a – Equity amount**

    - **Type:** Numeric currency input
    - **Stored as:** `funding_tax.equity_injection` (number)

  - If `I'm not sure – let the model suggest a starting amount`:
    - No further input; model will choose a starting equity level sufficient to cover early burn with some buffer, based on previous answers.

- **Usage:** Sets initial equity injection in the financing assumptions.
- **Stored as:** `funding_tax.equity_mode` plus `funding_tax.equity_injection` (if explicit)

---

**Q21 – Do you plan to take a loan at the start?**

- **Type:** Single‑select (with follow‑up)
- **Prompt:** `Do you plan to take a loan at the start (in addition to equity)?`
- **Options:**

  - `No loan at the start` → sets `funding_tax.loan_plan = none`
  - `Yes – I plan to take a term loan` → sets `funding_tax.loan_plan = term_loan`

- **Branching:**

  - If `No loan at the start`:

    - Set initial loan amount to 0; no follow‑up questions needed.

  - If `Yes – I plan to take a term loan`:

    **Q22a – Loan amount**

    - **Type:** Numeric currency input
    - **Prompt:** `How much do you plan to borrow at the start?`
    - **Stored as:** `funding_tax.loan_amount` (number)

    **Q22b – Interest rate (%)**

    - **Type:** Single‑select or numeric
    - **Prompt:** `What annual interest rate do you expect on this loan?`
    - **Options (suggested bands):**
      - `Around 5–8%` (`5_8`) → sets `funding_tax.loan_interest_mode = band`
      - `Around 8–12%` (`8_12`) → sets `funding_tax.loan_interest_mode = band`
      - `Higher than 12%` (`gt_12`) → sets `funding_tax.loan_interest_mode = band`
      - `I want to enter a custom rate` → reveals numeric input and sets `funding_tax.loan_interest_mode = explicit`
      - `I'm not sure` → sets `funding_tax.loan_interest_mode = band` (deep‑research will pick a band‑appropriate rate)

    **Q22c – Years to repay**

    - **Type:** Numeric input
    - **Prompt:** `Over how many years do you plan to repay this loan?`
    - **Stored as:** `funding_tax.loan_term_years` (int)

- **Usage:** Populates the debt schedule assumptions (single loan, starting in Year 1).
- **Stored as:** `funding_tax.loan_plan` plus `funding_tax.loan_amount`, `funding_tax.loan_interest_mode` (and either `funding_tax.loan_interest_band` if band or `funding_tax.loan_interest_pct` if explicit), and `funding_tax.loan_term_years`

---

**Q22 – Effective tax rate**

- **Type:** Single‑select (with optional numeric)
- **Prompt:** `What effective corporate tax rate should we assume for this business?`
- **Options:**

  - `Use a typical rate for my tax country` → sets `funding_tax.tax_rate_mode = typical`
  - `I want to enter my own rate` → sets `funding_tax.tax_rate_mode = explicit`

- **Branching:**

  - If `Use a typical rate for my tax country`:

    - No follow‑up; deep‑research agent infers a reasonable effective rate from tax country.

  - If `I want to enter my own rate`:

    **Q23a – Tax rate (%)**

    - **Type:** Percent input
    - **Prompt:** `Enter the effective tax rate you want us to use (e.g. 25%).`
    - **Stored as:** `funding_tax.tax_rate_pct` (number)

- **Usage:** Sets the tax rate used in the income statement and cash‑flow projections.
- **Stored as:** `funding_tax.tax_rate_mode` plus `funding_tax.tax_rate_pct` (if explicit)

---

### Summary of Branching Logic

- **Q4 → Q4a** appears only if user says tax country differs from customer region.
- **Q9 → Q9a or Q9b** depending on whether they know their AOV.
- **Q11 → Q11a** only if they have run paid ads before.
- **Q12 → Q13a or Q13b** depending on whether they know their margin target.
- **Q13 → Q14a or Q14b** depending on whether they know their shipping cost.
- **Q13c** captures fulfilment approach in Year 1.
- **Q14 → Q15a or Q15b/Q15c** depending on whether they know their team cost.
- **Q15 → Q16a or Q16b** depending on whether they know their other fixed costs.
- **Q20 → Q21a** only if they want to specify an equity amount.
- **Q21 → Q22a/Q22b/Q22c** only if they plan to take a loan.
- **Q22 → Q23a** only if they want to enter their own tax rate.

This question set keeps V1 focused on early‑stage e‑commerce, minimizes cognitive load for non‑finance founders, and still gives the agents enough signal to build a coherent model and narrative, with research‑backed defaults filling the gaps.
