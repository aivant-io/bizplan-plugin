# /bizplan — Full Ecommerce Business Plan Pipeline

Generate a complete ecommerce business plan and 6-year financial model from scratch.

## Pipeline

Run all 5 skills in sequence. Each step depends on the output of the previous step.

### Step 1: Intake Questionnaire
Use skill: `ecommerce-intake`

Walk the founder through the structured questionnaire (8 sections, ~22 questions with conditional branching). Collect all inputs and produce the intake JSON.

### Step 2: Resolve Assumptions
Use skill: `ecommerce-assumptions`

Take the intake JSON and resolve all 49 financial model drivers using mapping tables, curated benchmarks, and calculation formulas. Produce the resolved assumptions JSON.

### Step 3: Populate Financial Model
Use skill: `ecommerce-financial-model`

Write the 49 resolved driver values to the Excel template via direct XML editing. Recalculate formulas with xlcalculator. Run equity optimization if needed (suggest mode: iterate to positive cash; explicit mode: generate warning). Extract model outputs.

**Install dependencies first:**
```bash
pip install openpyxl>=3.1.2 xlcalculator>=0.5.0
```

### Step 4: Write Business Plan
Use skill: `ecommerce-business-plan`

Generate a 5,500-7,000 word business plan with 7 required sections. Perform structured market research (curated category benchmarks, then web search for market sizing, consumer trends, competitive landscape, and category-specific factors), write the narrative with bracket citations, and verify all citations mechanically. Include equity warning if applicable.

### Step 5: Export to DOCX (Optional)
Use skill: `ecommerce-document-export`

Convert the markdown business plan to a styled Word document using Pandoc and the reference.docx template. Skip this step if Pandoc is not installed — deliver markdown instead.

## Deliverables

1. **Excel financial model** (.xlsx) — 6-year forecast with income statement, balance sheet, cash flow, and key metrics
2. **Business plan** (.docx or .md) — Professional narrative with market analysis and citations

## Error Handling

- If any step fails, inform the user which step failed and why
- If Excel generation fails, the plan can still be written using resolved assumptions (without model outputs)
- If Pandoc is not available, deliver markdown and inform the user
- If equity optimization doesn't converge after 5 iterations, proceed with a warning

## Output Location

Save all output files to the current working directory:
- `{StoreName}_Financial_Model.xlsx`
- `{StoreName}_Business_Plan.docx` (or `.md`)
