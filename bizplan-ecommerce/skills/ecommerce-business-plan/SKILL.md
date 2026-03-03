---
name: ecommerce-business-plan
description: >
  Writes a professional, citation-verified business plan for a pre-launch
  ecommerce founder. Uses a 3-stage pipeline: market research with source
  tracking, narrative writing with bracket citations, and mechanical citation
  verification. Produces a 6,000-7,500 word plan with 7 required sections
  incorporating Excel model outputs and web-researched market context.
compatibility: Web search for market research.
---

# Ecommerce Business Plan Writer

## Overview

This skill generates a professional business plan narrative using the founder's intake data, resolved assumptions, and Excel model outputs. The plan is written in first-person plural ("we", "our") and incorporates sourced market data alongside the founder's own projections.

**Inputs:**
- Intake JSON (from ecommerce-intake skill) — includes `business_profile.target_customer`, `business_profile.differentiation`, `business_profile.founder_background`, and `business_profile.why_now` (all nullable — may be `null` if founder was unsure)
- Resolved assumptions JSON (from ecommerce-assumptions skill)
- Model outputs JSON (from ecommerce-financial-model skill)

**Outputs:** Business plan in markdown format with bracket citations `[1]`, `[2]`, etc.

## 3-Stage Pipeline

The plan writer uses three distinct stages to ensure citation accuracy.

### Stage 1: Market Research & Source Collection

Gather market context for the founder's category and region using a two-phase approach: curated benchmarks first, then targeted web research for gaps.

#### Phase 1 — Load Curated Benchmarks (before any web search)

Read the founder's category benchmark file from `bizplan-ecommerce/skills/ecommerce-assumptions/data/us/{category}.json` and extract citable data points:
- Conversion rates (paid, organic, retention) with source citations
- CAC, AOV, gross margin ranges with source citations
- Methodology notes and confidence scores

Also load `data/global_defaults.json` (inflation rates with sources) and `data/regional_defaults.json` (tax rates, shipping costs with sources).

Register these as the **first source entries** in the source tracker (sequential IDs starting at 1). These are pre-vetted, high-confidence benchmarks — cite them when contextualizing the founder's model assumptions in the narrative.

Available curated sources (use only those relevant to the founder's category):
- IRP Commerce — conversion rates by category (Nov 2025)
- Dynamic Yield XP2 / Mastercard — conversion benchmarks, 200M+ users (Dec 2024)
- Klaviyo — CAC benchmarks by category (Sep 2024)
- Oberlo — AOV benchmarks by industry (Sep 2024)
- Drivepoint — DTC ecommerce margin analysis (2024)

#### Phase 2 — Web Search for Gaps

Allocate searches across these research areas (the benchmarks don't cover these):

1. **Market sizing & growth** (2-4 searches) — TAM, SAM, growth rate, and forecast data for the founder's specific category and region. Prioritize reports with quantified market values.
2. **Consumer trends** (2-3 searches) — Behavioral shifts, demographic trends, and demand drivers relevant to the category. Look for data from the last 2 years.
3. **Competitive landscape** (2-4 searches) — Identify 3-5 direct competitors or comparable DTC brands. Gather: positioning, approximate revenue/scale, pricing strategy, key differentiators, funding history if available.
4. **Regulatory or category-specific** (0-2 searches) — Only if relevant (e.g., FDA for supplements, import tariffs, sustainability certifications).

Adapt depth to the market: well-documented categories (beauty, fashion) may need fewer searches; niche or emerging categories may need more. Stop when you have sufficient coverage across all areas, not at an arbitrary number.

**Source quality rules:**
- Target 12-20 unique sources total (curated benchmarks + web research combined)
- **Prefer recent sources** (2024-2026). Deprioritize anything older than 3 years unless it is a foundational market report.
- De-duplicate by URL
- Track each source: `{id: N, title: "...", url: "...", snippet: "...", accessed_at: "..."}`
- Continue sequential IDs from where the curated benchmark sources left off

**Source priority (for web searches):**
1. Industry reports (Statista, IBISWorld, Grand View Research, Mordor Intelligence)
2. Trade publications (eMarketer, Retail Dive, Shopify reports, CB Insights)
3. Market analysis (McKinsey, Bain, Deloitte retail reports)
4. Competitor profiles (Crunchbase, brand websites, press coverage)
5. News articles (recent market developments, funding rounds)

### Stage 2: Plan Writing

Write the narrative using ONLY sources collected in Stage 1. Web search is NOT allowed during writing — this prevents citation hallucinations.

**Citation rules:**
- Use `[N]` bracket format mapped to Stage 1 source IDs
- **CITE**: Market size, growth rates, demographics, competitive landscape, industry trends, external benchmarks, competitor data
- **DO NOT CITE**: Company projections from the Excel model (revenue, orders, margins, CAC/LTV — these are our own numbers)
- **Key distinction**: "Industry average CAC is $45 [3]" vs "Our target CAC is $45" (no citation)
- Never invent citation numbers — only use IDs from Stage 1 sources

**Per-section citation guidance:**

| Section | Target citations | Notes |
|---------|-----------------|-------|
| Executive Summary | 1-2 | Only headline market stats |
| Business Overview | 2-5 | Market timing, category context, competitive positioning |
| Market Opportunity | 6-10 | Heaviest — TAM, growth, trends, competitors |
| Go-to-Market Strategy | 2-4 | Channel benchmarks, industry CAC/conversion data |
| Operations | 0-2 | Fulfillment trends, logistics benchmarks if available |
| Financial Plan | 2-5 | Industry benchmarks, risk context, sensitivity comparisons |
| Appendix | 0 | Sources listed here, not cited |

### Stage 3: Citation Verification

Mechanically verify all citations after writing:

1. Extract all `[N]` references from the plan text
2. Check each maps to a source from Stage 1
3. Remove any "orphan" citations (no matching source) — remove the `[N]` marker but keep the surrounding text
4. Generate the final "Sources Cited" section with clean numbered list

## Required Sections (7)

### 1. Executive Summary
- Write this LAST (after all other sections)
- 1-2 pages (400-600 words), standalone summary of the entire plan
- **Narrative arc** — build this as a story, not a checklist:
  1. **The opportunity**: What problem exists or what shift is happening? (1-2 sentences from `business_profile.why_now` + market research. If `why_now` is null, lead with a market insight from Stage 1 research.)
  2. **The solution**: What are we building and for whom? (From `business_profile.description` + `business_profile.target_customer`)
  3. **The business model**: How do we make money? (AOV, order volume, channel strategy — 2-3 sentences)
  4. **The trajectory**: Where does this go? (From model outputs: `gross_revenue` Year 1 and Year 3, `break_even_year`, `revenue_cagr` — stated as milestones, not a data dump)
  5. **The ask**: What resources do we need? (Initial funding amount and key use of funds)
- **Tone**: After reading this section, the founder should think: "Yes, that's exactly what I'm building and why." This is NOT a list of metrics — it is a story with numbers as supporting evidence.

### 2. Business Overview
- **Value proposition and product description** (1-2 paragraphs): What we sell, how it works, and why it matters to our customer. Use `business_profile.description` and `business_profile.differentiation` to ground this in the founder's own words, then expand with market context.
- **Target customer persona** (1 paragraph): Build a concrete portrait of the ideal customer using `business_profile.target_customer`. Include demographics, psychographics (values, habits, frustrations), and buying behavior. Make it specific enough that the founder could picture a real person. If `target_customer` is null, build a brief persona from category research and market data.
- **Founder and team** (1 paragraph): If `business_profile.founder_background` is provided, explain why the founder is positioned to execute this business. Connect their background to specific advantages it creates (supplier relationships, audience, domain expertise). If `founder_background` is null, omit this paragraph entirely — do not fabricate founder credentials.
- **DTC model and sales platform choice** (1 paragraph): Why the chosen platform fits this product and customer.
- **Competitive positioning** (1-2 paragraphs): How our products differ from what is available. Use `business_profile.differentiation` as the anchor, then validate with competitive intelligence from Stage 1. If differentiation is null, build positioning from web research findings.
- **Why now** (1 paragraph): The market timing argument. Use `business_profile.why_now` as the anchor if provided, then reinforce with cited market data. If `why_now` is null, build entirely from Stage 1 market research.

### 3. Market Opportunity
- **CITE HEAVILY** — this section should carry the majority of citations
- Total addressable market (TAM) with source, and serviceable addressable market (SAM) if data available
- Market growth rate and forecasted trajectory
- Consumer behavior shifts relevant to the category (last 2-3 years)
- **Competitive landscape** (dedicate 2-3 paragraphs):
  - Name 3-5 direct competitors or comparable DTC brands
  - For each: positioning, approximate scale, pricing tier, key differentiator
  - Identify whitespace or positioning gaps the founder can exploit
  - Note any recent market entries, exits, or funding rounds
- Regional market context (founder's customer region)
- **"So what?" connection**: After presenting the market data, connect it back to this specific business. Don't just report that the market is large — explain what it means for our positioning, growth potential, and competitive window. End this section with 1-2 sentences bridging from "the market is attractive" to "here is where we fit."

### 4. Go-to-Market Strategy

Use the founder's intake data and model outputs as the primary source for all claims in this section. External benchmarks from Stage 1 research should contextualize and validate, not replace, the founder's own numbers.

- **Primary acquisition channels and rationale** (1-2 paragraphs): Start from `acquisition.primary_channels` (the founder's chosen channels — paid ads, organic/direct, retention/email/SMS). Explain why these channels fit the product and customer. If the founder selected `use_standard_mix`, note that the plan uses a balanced industry-standard allocation. Reference `acquisition.conv_difficulty` and `acquisition.has_paid_ads_experience` to calibrate tone — a founder with paid ads experience and "easy" conversion warrants a more confident channel narrative than one with no experience targeting a "hard" conversion product.
- **Channel mix and traffic plan** (1 paragraph): State the resolved traffic mix from assumptions: `traffic_mix_paid_pct`, `traffic_mix_organic_pct`, `traffic_mix_retention_pct`. Explain what each percentage means in practice — e.g., "We allocate 60% of traffic investment to paid acquisition, primarily through [channel], with 25% from organic content and SEO, and 15% from repeat-customer email and SMS flows." Reference `strategy.financial_priority` to explain the mix rationale: a growth-first strategy justifies heavier paid allocation; a profit-first strategy justifies higher organic and retention emphasis.
- **Unit economics** (1-2 paragraphs): Use model outputs: `cac` (Year 1), `contribution_margin_per_order` (Year 1), `payback_orders` (Year 1). State AOV from the resolved assumptions (originally from `pricing.aov_year1` or resolved from `pricing.aov_band`). Walk through the math: "At an average order value of $X and a customer acquisition cost of $Y, each new customer generates $Z in contribution margin per order, requiring N orders to recover acquisition cost." Compare CAC and conversion rates to Stage 1 curated benchmarks where relevant.
- **Customer retention strategy** (1 paragraph): Ground in `demand.repeat_expectation` from intake (none, low, medium, high). If the founder expects repeat purchases, describe the retention approach (email flows, loyalty program, subscription) and connect to the retention traffic percentage. If `repeat_expectation` is "none," acknowledge the single-purchase model and explain how the business sustains growth through new customer acquisition instead.
- **Scaling plan** (1 paragraph): Describe how channels evolve over Years 1-5. Reference `strategy.growth_ambition` (conservative, base, aggressive) to set the scaling pace. Connect to the model's traffic growth rates and explain how the channel mix shifts as the brand matures — e.g., paid percentage decreasing as organic and retention grow with brand recognition.

### 5. Operations

Use the founder's intake data and model outputs as the primary source for all claims in this section. External benchmarks from Stage 1 research should contextualize and validate, not replace, the founder's own numbers.

- **Fulfillment approach** (1 paragraph): Start from `unit_economics.fulfilment_mode_year1` (self-fulfill, 3PL, dropship/POD, or "not sure"). If the founder chose a specific mode, describe how it works for their product and scale. If "not sure," recommend an approach based on the product category and Year 1 order volume (from `demand.year1_orders_bucket`), then explain the tradeoffs. Connect fulfillment costs to `unit_economics.shipping_cost_band` or `unit_economics.shipping_plus_packaging_per_order` if provided explicitly.
- **Inventory and working capital** (1 paragraph): Reference `working_capital.inventory_intensity` (no stock, 1-2 months, 3+ months) to describe the inventory strategy. Connect to `working_capital.supplier_payment_terms` and `working_capital.customer_payment_terms` to explain cash conversion cycle. Use model outputs for inventory days and working capital requirements. If the founder chose dropship/POD fulfillment with no stock, this paragraph should be brief and focus on supplier reliability instead.
- **Technology stack and sales platform** (1 paragraph): Ground in `unit_economics.sales_platform` (DTC website, Amazon, Etsy, multi-channel). Explain why the chosen platform fits the product and target customer. Describe the supporting SaaS stack appropriate for the platform — e.g., Shopify + Klaviyo for DTC, FBA tools for Amazon, Etsy Ads for marketplace sellers. Keep recommendations proportional to `team_overhead.other_fixed_costs_band` (lean, moderate, heavy).
- **Team structure and hiring plan** (1 paragraph): Reference `team_overhead.team_size_bucket` (0-1, 2-3, 4-7, 8+) and `team_overhead.salary_level` (low, mid, high) from intake. Describe who the team is at launch and how it grows. For solo founders (0-1), emphasize outsourcing and automation. For larger teams, outline key roles and hiring timeline. Connect team costs to the model's overhead projections.
- **Scaling operations** (1 paragraph): Connect operational scaling to the model's order growth trajectory. Identify the inflection points — e.g., "As order volume grows from X in Year 1 to Y in Year 3, we anticipate transitioning from [current approach] to [scaled approach]." Reference `strategy.growth_ambition` to calibrate the pace of operational investment.

### 6. Financial Plan

This section presents the financial case clearly enough for any reader — founder, investor, or advisor — to follow the logic. Every projection should be accompanied by the reasoning that makes it credible.

All financial figures in this section must come from the model outputs JSON. Never estimate, round, or generate financial numbers — use the exact values from the model. External benchmarks from Stage 1 research should contextualize and validate, not replace, the model's projections.

- **Revenue trajectory** (2-3 paragraphs): Use model outputs: `total_orders`, `gross_revenue`, `net_revenue` (Years 1-6), and `revenue_cagr`. Walk through the logic: "We project $X in Year 1 revenue based on Y orders at $Z average order value. Revenue grows to $A by Year 3 as we scale traffic by B% annually and improve conversion through [strategy]." The narrative should make clear WHY revenue grows, not just THAT it grows.
- **Path to profitability** (1-2 paragraphs): Use model outputs: `ebitda`, `ebitda_margin_pct`, `net_income` (Years 1-6), and `break_even_year`. Check `break_even_year` and choose the appropriate narrative:
  - **If breakeven is Year 1** (immediately profitable): Lead with the strength — the business model generates positive EBITDA from launch. Explain why: high gross margins, lean overhead, strong unit economics, or favorable CAC-to-LTV ratio. Then pivot to sustainability — what maintains profitability as the business scales (e.g., fixed costs growing slower than revenue, retention reducing acquisition dependency, margin improvements from supplier scale).
  - **If breakeven is Year 2+** (early losses expected): Frame early losses as intentional investment: "We expect to operate at a loss of $X in Year 1 as we invest in [customer acquisition / inventory / team]. We reach EBITDA breakeven in Year N as [specific mechanism — fixed costs spread across more orders, CAC declines with brand recognition, repeat purchases reduce acquisition dependency]."
- **Gross margin profile** (1 paragraph): Use model outputs: `gross_margin_pct` (Years 1-6). Describe gross margin trajectory and COGS management. Compare to industry benchmarks from Stage 1 research. Explain any expected margin improvement and the mechanism behind it.
- **Capital requirements and use of funds** (1-2 paragraphs): Use model outputs: `initial_equity_injection` and `initial_loan_amount`. Reference `funding_tax.loan_plan` from intake for loan context. Provide clear allocation: "Of the $X initial investment, approximately $Y is allocated to pre-launch inventory, $Z to first-quarter marketing, and $W held as operating cash buffer." When `equity_audit` is present in model outputs, use its `monthly_burn`, `runway_months`, and iteration data to ground the capital explanation in the actual calculation rather than reconstructing it.
- **What could go wrong** (2-3 paragraphs): Identify 3-4 material risks and the founder's response for each. Frame as clear-eyed awareness, not pessimism. For each risk: state it, estimate impact, describe mitigation or pivot. Risks to consider:
- Customer acquisition costs higher than projected (what if CAC is 50% above target?)
- Slower-than-expected demand (what if Year 1 orders are 30% below target?)
- Margin pressure from competitors or input costs
- Supply chain disruption or inventory challenges
- Platform dependency (if selling primarily on Amazon/Etsy)
Draw from the model's sensitivity — use `cac`, `total_orders`, and `break_even_year` to quantify specific risk scenarios: "If CAC rises from $X to $Y, breakeven shifts from Year N to Year N+1, requiring an additional $Z in runway."
- **Cash flow and runway** (1 paragraph): Use model outputs: `closing_cash_balance` (Years 1-6), `burn_rate` (Year 1), `runway_months`. State monthly burn rate, runway in months, and cash position trajectory. Highlight the lowest projected cash balance and when it occurs.

### 7. Appendix
- **Financial Projections Table**: 6-year summary with key metrics
- **Sources Cited**: Numbered list of all cited sources with URLs
- **Key Assumptions**: Summary of major model inputs

## Model Outputs to Incorporate

Use these Excel model outputs throughout the narrative:

**Revenue & Orders:**
- `total_orders` (Years 1-6)
- `gross_revenue`, `net_revenue` (Years 1-6)
- `revenue_cagr` (5-year compound annual growth rate)

**Profitability:**
- `gross_margin_pct` (Years 1-6)
- `ebitda`, `ebitda_margin_pct` (Years 1-6)
- `net_income` (Years 1-6)
- `break_even_year`

**Unit Economics:**
- `cac` (Year 1)
- `contribution_margin_per_order` (Year 1)
- `payback_orders` (Year 1)

**Cash & Funding:**
- `closing_cash_balance` (Years 1-6)
- `burn_rate` (Year 1)
- `runway_months`
- `initial_equity_injection` and `initial_loan_amount`

**Format numbers professionally:**
- Currency: "$165,000" or "$1.2M" for large values
- Percentages: "48%" (whole numbers in narrative)
- Orders: "3,000 orders" with commas
- Growth: "35% CAGR"

**Integration approach:**
- **Headline metrics** (feature in key sentences): Year 1 revenue, Year 3 revenue, break-even year, initial funding, revenue CAGR, gross margin. These should appear in topic sentences or summary statements.
- **Supporting metrics** (provide depth): Unit economics (CAC, contribution margin, payback), cash flow details, expense breakdowns. Use these in explanatory paragraphs or comparison tables.
- **Contextual contrast**: Where possible, pair a model output with a sourced benchmark: "We target a 48% gross margin, consistent with the 50-60% range typical of DTC beauty brands [5]."
- **Qualitative intake integration**: Where the intake provides qualitative context (`target_customer`, `differentiation`, `founder_background`, `why_now`), use the founder's own words as the anchor and expand with research. If a field is `null`, rely on web research or omit that specific paragraph (for `founder_background`). Never fabricate qualitative context the founder did not provide.

## Writing Style

- **Voice**: First-person plural ("we", "our", "us") — this is the founder's plan, written as if the founder is speaking
- **Tone**: Clear-eyed and confident. This means:
  - Show strengths honestly — don't hedge good numbers with unnecessary qualifiers
  - Acknowledge challenges directly — don't hide risks or gloss over early losses
  - Be specific, not vague — "we target 3,000 orders in Year 1" not "we expect solid demand"
  - Present the business honestly — the plan is a strategic document, not a marketing brochure
  - Every section should answer "so what?" — why does this information matter for the business?
  - Avoid cliches: no "rapidly growing market," "best-in-class," "revolutionary," "disruptive," or "game-changing." Use specific data instead.
- **Tense**: Future/aspirational for pre-launch: "we target 4.8% conversion" not "we achieve"
- **Format**: Flowing prose with selective use of bullets and tables. Use tables only for multi-year financial data and competitor comparisons.
- **Length**: 6,000-7,500 words total
- **Specificity**: Always use exact numbers from the model, never round vaguely
- **Narrative coherence**: The plan should read as a single connected argument, not seven independent sections. Each section builds on the previous one. The thread: "Here is an opportunity, here is how we will capture it, here is what it takes, and here is what we expect."

## Equity Warning Integration

If the equity optimizer generated a warning (explicit mode with negative cash), append it to the Financial Plan section:

```markdown
**Funding Note:** Based on current projections, cash balance is projected to go
negative in Year 3 (-$12,000). Consider securing an additional $15,000 in funding
to maintain operational runway.
```

## Financial Projections Table Format

Include in the Appendix:

```markdown
| Metric | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 |
|--------|------|------|------|------|------|------|
| Total Orders | 3,000 | 4,200 | 5,880 | ... | ... | ... |
| Gross Revenue | $165K | $245K | $360K | ... | ... | ... |
| Net Revenue | $152K | $228K | $338K | ... | ... | ... |
| Gross Margin | 50% | 51% | 52% | ... | ... | ... |
| EBITDA | ($12K) | $8K | $45K | ... | ... | ... |
| Net Income | ($15K) | $5K | $38K | ... | ... | ... |
| Closing Cash | $35K | $28K | $55K | ... | ... | ... |
```

## Sources Cited Format

```markdown
## Sources Cited

1. "US Beauty & Personal Care Market Size Report" — Grand View Research, 2025. [https://example.com/report]
2. "Ecommerce Conversion Rate Benchmarks" — Shopify, 2025. [https://example.com/benchmarks]
3. ...
```

## Critical Rules

1. **Write Executive Summary LAST** — it needs content from all other sections
2. **Never cite company projections** — only cite external market data
3. **Never invent citations** — only use source IDs from Stage 1 research
4. **Use exact model numbers** — don't round "$152,340" to "about $150,000"
5. **Pre-launch tense** — "we plan to", "we target", "we expect" (not "we achieved")
6. **Purposeful research** — every search should target a specific research area from the Stage 1 strategy; do not search aimlessly or repeat failed queries
7. **Remove orphan citations** — any `[N]` without a matching source must be cleaned
