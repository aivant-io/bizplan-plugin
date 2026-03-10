# /financial-model — Excel Financial Model Only

Generate a 6-year ecommerce financial model without writing the narrative business plan.

## Pipeline

Run the first 3 skills. Step 1 runs inline (user interaction), Steps 2-3 run in isolated subagent contexts reading/writing files from disk.

### Step 1: Intake Questionnaire (inline)
Use skill: `ecommerce-intake`

Walk the founder through the structured questionnaire to collect all inputs.

After this skill completes, **save the intake JSON to `{StoreName}_intake.json`** in the current working directory. Extract the store name from `business_profile.store_name` — this is passed as the argument to subsequent skills.

### Step 2: Resolve Assumptions (forked subagent)
Use skill: `ecommerce-assumptions` with the store name as the argument.

Reads `{StoreName}_intake.json` from disk, resolves all 49 financial model drivers, writes `{StoreName}_assumptions.json`.

### Step 3: Populate Financial Model (forked subagent)
Use skill: `ecommerce-financial-model` with the store name as the argument.

Reads `{StoreName}_assumptions.json` from disk, populates the Excel template, runs equity optimization, writes `{StoreName}_Financial_Model.xlsx` and `{StoreName}_model_outputs.json`.

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

Save to the current working directory:
- `{StoreName}_intake.json`
- `{StoreName}_assumptions.json`
- `{StoreName}_Financial_Model.xlsx`
- `{StoreName}_model_outputs.json`

## After Generation

Summarize key metrics for the founder:
- Year 1 revenue and orders
- Break-even year
- Initial funding (equity + loan)
- Year 1 burn rate and runway
- Revenue CAGR (5-year)

Run `scripts/validate_model.py` to verify the model is valid.
