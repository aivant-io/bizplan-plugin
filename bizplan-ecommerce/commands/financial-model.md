# /financial-model — Excel Financial Model Only

Generate a 6-year ecommerce financial model without writing the narrative business plan.

## Pipeline

Run the first 3 skills only:

### Step 1: Intake Questionnaire
Use skill: `ecommerce-intake`

Walk the founder through the structured questionnaire to collect all inputs.

### Step 2: Resolve Assumptions
Use skill: `ecommerce-assumptions`

Resolve all 49 financial model drivers from the intake JSON.

### Step 3: Populate Financial Model
Use skill: `ecommerce-financial-model`

Write values to the Excel template, recalculate formulas, run equity optimization, and extract model outputs.

**Install dependencies first:**
```bash
pip install openpyxl>=3.1.2 xlcalculator>=0.5.0
```

## Deliverable

**Excel financial model** (.xlsx) — 6-year forecast with:
- Assumptions sheet (49 editable drivers)
- Orders & traffic build
- Income statement
- Balance sheet
- Cash flow statement
- Key metrics (CAC, contribution margin, payback, burn rate)

## Output Location

Save to: `{StoreName}_Financial_Model.xlsx`

## After Generation

Summarize key metrics for the founder:
- Year 1 revenue and orders
- Break-even year
- Initial funding (equity + loan)
- Year 1 burn rate and runway
- Revenue CAGR (5-year)

Run `scripts/validate_model.py` to verify the model is valid.
