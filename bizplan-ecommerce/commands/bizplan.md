# /bizplan — Full Ecommerce Business Plan Pipeline

Generate a complete ecommerce business plan and 6-year financial model from scratch.

## Pipeline

Run all 5 skills in sequence. Each step depends on the output of the previous step. **Steps 2, 3, and 5 run as Python scripts** (fast, deterministic, zero LLM tokens). **Step 4 runs in a forked subagent** (`context: fork`, Opus) for clean-context narrative writing.

### Step 1: Intake Questionnaire (inline)
Use skill: `ecommerce-intake`

Walk the founder through the structured questionnaire (8 sections, ~26 questions with conditional branching). Collect all inputs and produce the intake JSON.

After this skill completes, **save the intake JSON to `{StoreName}_intake.json`** in the current working directory. Extract the store name from `business_profile.store_name` in the intake output — this store name is used in all subsequent steps.

### Step 2: Resolve Assumptions (Python script)
Run the assumptions resolution script:

```bash
python "${CLAUDE_SKILL_DIR}/../ecommerce-assumptions/scripts/resolve_assumptions.py" "{StoreName}"
```

This reads `{StoreName}_intake.json`, resolves all 49 financial model drivers using curated benchmarks and mapping tables, and writes `{StoreName}_assumptions.json`. Takes ~2 seconds.

### Step 3: Populate Financial Model (Python script)
Install dependencies and run the model population script:

```bash
pip install openpyxl>=3.1.2 xlcalculator>=0.5.0
python "${CLAUDE_SKILL_DIR}/../ecommerce-financial-model/scripts/populate_model.py" "{StoreName}"
```

This reads `{StoreName}_assumptions.json`, populates the Excel template via direct XML editing, recalculates formulas, runs equity optimization if needed, and writes:
- `{StoreName}_Financial_Model.xlsx`
- `{StoreName}_model_outputs.json`

Takes ~5 seconds.

### Step 4: Write Business Plan (forked subagent)
Use skill: `ecommerce-business-plan` with the store name as the argument.

This skill runs in an isolated context with a clean context window — no accumulated conversation history from prior steps. It reads all three JSON files from disk (`{StoreName}_intake.json`, `{StoreName}_assumptions.json`, `{StoreName}_model_outputs.json`), performs structured market research (curated benchmarks + web search), writes the narrative with bracket citations, verifies citations, and saves `{StoreName}_Business_Plan.md`.

### Step 5: Export to DOCX (Python script, optional)
Run the DOCX export script:

```bash
pip install python-docx>=1.1.0
python "${CLAUDE_SKILL_DIR}/../ecommerce-document-export/scripts/export_docx.py" \
  "{StoreName}_Business_Plan.md" \
  "{StoreName}_Business_Plan.docx" \
  --title "{StoreName}" \
  --date "$(date +'%B %Y')"
```

Skip if Pandoc is not installed — deliver markdown instead.

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
- `{StoreName}_intake.json`
- `{StoreName}_assumptions.json`
- `{StoreName}_Financial_Model.xlsx`
- `{StoreName}_model_outputs.json`
- `{StoreName}_Business_Plan.md`
- `{StoreName}_Business_Plan.docx`
