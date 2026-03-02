# /business-plan — Narrative Business Plan Only

Write a professional business plan narrative. Can work with an existing Excel model or run the full pipeline first.

## Usage Modes

### Mode A: With Existing Excel Model

If the user provides an existing populated Excel model (.xlsx):

1. Extract model outputs from the Excel file using `references/output_map.jsonc` cell addresses
2. Ask the user for any missing intake context (business name, category, region, channels)
3. Skip to Step 4 below

### Mode B: From Scratch

If no existing model is provided, run the full pipeline:

### Step 1: Intake Questionnaire
Use skill: `ecommerce-intake`

### Step 2: Resolve Assumptions
Use skill: `ecommerce-assumptions`

### Step 3: Populate Financial Model
Use skill: `ecommerce-financial-model`

### Step 4: Write Business Plan
Use skill: `ecommerce-business-plan`

Generate a 5,500-7,000 word plan with 7 sections, bracket citations, and market research.

### Step 5: Export to DOCX (Optional)
Use skill: `ecommerce-document-export`

Convert to styled Word document if Pandoc is available.

## Deliverable

**Business plan** (.docx or .md) — Professional narrative with:
- 7 required sections (Executive Summary through Appendix)
- Market research with sourced citations
- Financial projections table
- Investor-ready formatting

## Output Location

Save to: `{StoreName}_Business_Plan.docx` (or `.md` if Pandoc unavailable)
