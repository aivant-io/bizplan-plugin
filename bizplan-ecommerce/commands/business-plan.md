# /business-plan — Narrative Business Plan Only

Write a professional business plan narrative. Can work with an existing Excel model or run the full pipeline first.

## Usage Modes

### Mode A: With Existing Excel Model

If the user provides an existing populated Excel model (.xlsx):

1. Extract model outputs from the Excel file using `references/output_map.jsonc` cell addresses
2. Ask the user for any missing intake context (business name, category, region, channels)
3. Save the intake data to `{StoreName}_intake.json` and model outputs to `{StoreName}_model_outputs.json`
4. Skip to Step 4 below

### Mode B: From Scratch

If no existing model is provided, run the full pipeline:

### Step 1: Intake Questionnaire (inline)
Use skill: `ecommerce-intake`

After this skill completes, **save the intake JSON to `{StoreName}_intake.json`** in the current working directory. Extract the store name from `business_profile.store_name`.

### Step 2: Resolve Assumptions (Python script)

```bash
python "${CLAUDE_SKILL_DIR}/../ecommerce-assumptions/scripts/resolve_assumptions.py" "{StoreName}"
```

Reads `{StoreName}_intake.json`, writes `{StoreName}_assumptions.json`.

### Step 3: Populate Financial Model (Python script)

```bash
pip install openpyxl>=3.1.2 xlcalculator>=0.5.0
python "${CLAUDE_SKILL_DIR}/../ecommerce-financial-model/scripts/populate_model.py" "{StoreName}"
```

Reads `{StoreName}_assumptions.json`, writes `{StoreName}_Financial_Model.xlsx` and `{StoreName}_model_outputs.json`.

### Step 4: Write Business Plan (forked subagent)
Use skill: `ecommerce-business-plan` with the store name as the argument.

Runs in an isolated context with a clean context window. Reads `{StoreName}_intake.json`, `{StoreName}_assumptions.json`, and `{StoreName}_model_outputs.json` from disk. Performs market research, writes narrative, verifies citations. Saves `{StoreName}_Business_Plan.md`.

### Step 5: Export to DOCX (Python script, optional)

```bash
pip install python-docx>=1.1.0
python "${CLAUDE_SKILL_DIR}/../ecommerce-document-export/scripts/export_docx.py" \
  "{StoreName}_Business_Plan.md" \
  "{StoreName}_Business_Plan.docx" \
  --title "{StoreName}" \
  --date "$(date +'%B %Y')"
```

Skip if Pandoc is not available — deliver markdown instead.

## Deliverable

**Business plan** (.docx or .md) — Professional narrative with:
- 7 required sections (Executive Summary through Appendix)
- Market research with sourced citations
- Financial projections table
- Investor-ready formatting

## Output Location

Save to: `{StoreName}_Business_Plan.docx` (or `.md` if Pandoc unavailable)
