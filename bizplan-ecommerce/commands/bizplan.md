# /bizplan — Full Ecommerce Business Plan Pipeline

Generate a complete ecommerce business plan and 6-year financial model from scratch.

## Pipeline

Run all 5 skills in sequence. Each step depends on the output of the previous step. **Steps 2-5 run in isolated subagent contexts** (`context: fork`) — they read inputs from disk and write outputs to disk. Step 1 runs inline because it requires user interaction.

### Step 1: Intake Questionnaire (inline)
Use skill: `ecommerce-intake`

Walk the founder through the structured questionnaire (8 sections, ~22 questions with conditional branching). Collect all inputs and produce the intake JSON.

After this skill completes, **save the intake JSON to `{StoreName}_intake.json`** in the current working directory. Extract the store name from `business_profile.store_name` in the intake output — this store name is passed as the argument to all subsequent skills.

### Step 2: Resolve Assumptions (forked subagent)
Use skill: `ecommerce-assumptions` with the store name as the argument.

This skill runs in an isolated context. It reads `{StoreName}_intake.json` from disk, resolves all 49 financial model drivers using mapping tables, curated benchmarks, and calculation formulas, and writes `{StoreName}_assumptions.json` to disk.

### Step 3: Populate Financial Model (forked subagent)
Use skill: `ecommerce-financial-model` with the store name as the argument.

This skill runs in an isolated context. It reads `{StoreName}_assumptions.json` from disk, populates the Excel template via direct XML editing, recalculates formulas with xlcalculator, runs equity optimization if needed, and writes:
- `{StoreName}_Financial_Model.xlsx`
- `{StoreName}_model_outputs.json`

**Install dependencies first:**
```bash
pip install openpyxl>=3.1.2 xlcalculator>=0.5.0
```

### Step 4: Write Business Plan (forked subagent)
Use skill: `ecommerce-business-plan` with the store name as the argument.

This skill runs in an isolated context with a clean context window — no accumulated conversation history from prior steps. It reads all three JSON files from disk (`{StoreName}_intake.json`, `{StoreName}_assumptions.json`, `{StoreName}_model_outputs.json`), performs structured market research (curated benchmarks + web search), writes the narrative with bracket citations, verifies citations, and saves `{StoreName}_Business_Plan.md`.

### Step 5: Export to DOCX (forked subagent, optional)
Use skill: `ecommerce-document-export` with the store name as the argument.

This skill runs in an isolated context. It reads `{StoreName}_Business_Plan.md`, converts to styled Word document using Pandoc and the reference.docx template, and writes `{StoreName}_Business_Plan.docx`. Skip if Pandoc is not installed — deliver markdown instead.

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
