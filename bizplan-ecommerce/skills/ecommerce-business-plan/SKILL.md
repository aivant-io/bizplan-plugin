---
name: ecommerce-business-plan
description: >
  Writes a professional, citation-verified business plan for a pre-launch
  ecommerce founder. Uses a 3-stage pipeline: market research with source
  tracking, narrative writing with bracket citations, and mechanical citation
  verification. Produces a 5,500-7,000 word plan with 7 required sections
  incorporating Excel model outputs and web-researched market context.
compatibility: Web search for market research (max 8 searches).
---

# Ecommerce Business Plan Writer

## Overview

This skill generates a professional business plan narrative using the founder's intake data, resolved assumptions, and Excel model outputs. The plan is written in first-person plural ("we", "our") and incorporates sourced market data alongside the founder's own projections.

**Inputs:**
- Intake JSON (from ecommerce-intake skill)
- Resolved assumptions JSON (from ecommerce-assumptions skill)
- Model outputs JSON (from ecommerce-financial-model skill)

**Outputs:** Business plan in markdown format with bracket citations `[1]`, `[2]`, etc.

## 3-Stage Pipeline

The plan writer uses three distinct stages to ensure citation accuracy.

### Stage 1: Market Research & Source Collection

Perform focused web searches to gather market context for the founder's category and region. Track all sources with sequential IDs.

**Guidelines:**
- Max 8 web searches
- Target 10-15 unique sources
- Focus on: market size, growth rates, consumer trends, competitive landscape, industry benchmarks
- Track each source: `{id: 1, title: "...", url: "...", snippet: "...", accessed_at: "..."}`
- De-duplicate by URL
- Assign sequential IDs: 1, 2, 3, etc.

**Source priority:**
1. Industry reports (Statista, IBISWorld, Grand View Research)
2. Trade publications (eMarketer, Retail Dive, Shopify reports)
3. Market analysis (McKinsey, Bain, Deloitte retail reports)
4. News articles (recent market developments)

### Stage 2: Plan Writing

Write the narrative using ONLY sources collected in Stage 1. Web search is NOT allowed during writing — this prevents citation hallucinations.

**Citation rules:**
- Use `[N]` bracket format mapped to Stage 1 source IDs
- **CITE**: Market size, growth rates, demographics, competitive landscape, industry trends, external benchmarks
- **DO NOT CITE**: Company projections from the Excel model (revenue, orders, margins, CAC/LTV — these are our own numbers)
- **Key distinction**: "Industry average CAC is $45 [3]" vs "Our target CAC is $45" (no citation)
- Never invent citation numbers — only use IDs from Stage 1 sources
- Target citation density: 8-15 citations across the full plan

### Stage 3: Citation Verification

Mechanically verify all citations after writing:

1. Extract all `[N]` references from the plan text
2. Check each maps to a source from Stage 1
3. Remove any "orphan" citations (no matching source) — remove the `[N]` marker but keep the surrounding text
4. Generate the final "Sources Cited" section with clean numbered list

## Required Sections (7)

### 1. Executive Summary
- Write this LAST (after all other sections)
- 1-2 pages, standalone summary of the entire plan
- Include: business concept, target market, revenue model, Year 1-3 trajectory, funding need
- Key metrics: Year 1 revenue, Year 3 revenue, break-even year, initial funding

### 2. Business Overview
- Value proposition and product description
- Target customer profile
- DTC model and sales platform choice
- Category positioning and competitive angle
- Why now — timing and market opportunity

### 3. Market Opportunity
- **CITE HEAVILY** — this is where most citations belong
- Total addressable market (TAM) with source
- Market growth rate and trends
- Consumer behavior shifts relevant to the category
- Competitive landscape: key players, market fragmentation
- Regional market context (founder's customer region)

### 4. Go-to-Market Strategy
- Primary acquisition channels and rationale
- Channel mix breakdown (paid %, organic %, retention %)
- Unit economics: AOV, CAC, contribution margin, payback period
- Customer retention strategy and repeat purchase approach
- Scaling plan: how channels evolve over Years 1-5

### 5. Operations
- Fulfillment approach (self-fulfill, 3PL, dropship)
- Inventory management and working capital
- Technology stack and SaaS tools
- Team structure and hiring plan
- Scaling operations as volume grows

### 6. Financial Plan
- Revenue trajectory (Year 1-5 with specific numbers)
- Path to profitability (EBITDA and net income timeline)
- Gross margin profile and COGS management
- Capital requirements and use of funds
- Key financial assumptions and sensitivity
- Cash flow management and runway

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

## Writing Style

- **Voice**: First-person plural ("we", "our", "us") — founder perspective
- **Tone**: Professional but accessible, confident but not overselling
- **Tense**: Future/aspirational for pre-launch: "we target 4.8% conversion" not "we achieve"
- **Format**: Flowing prose with selective use of bullets and tables
- **Length**: 5,500-7,000 words total
- **Specificity**: Always use exact numbers from the model, never round vaguely

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
6. **Max 8 web searches** — be focused and efficient with research
7. **Remove orphan citations** — any `[N]` without a matching source must be cleaned
