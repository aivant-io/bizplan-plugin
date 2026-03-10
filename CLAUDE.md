# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Claude plugin marketplace containing business plan and financial model generators for pre-launch founders. Each vertical (ecommerce, SaaS, etc.) is a self-contained plugin in its own directory, following the Claude Code plugin format (`.claude-plugin/plugin.json` + skills + commands + hooks). The marketplace manifest at `.claude-plugin/marketplace.json` registers all available plugins.

## Dependencies

- Python 3.11+
- `openpyxl>=3.1.2` and `xlcalculator>=0.5.0` (financial model — `bizplan-ecommerce/skills/ecommerce-financial-model/requirements.txt`)
- `python-docx>=1.1.0` (DOCX post-processing — `bizplan-ecommerce/skills/ecommerce-document-export/requirements.txt`)
- Pandoc (optional, for DOCX export; falls back to markdown delivery)

## Commands

- `/bizplan` — Full 5-stage pipeline: intake → assumptions → Excel model → business plan → DOCX export
- `/financial-model` — Stages 1-3 only (intake → assumptions → Excel model)
- `/business-plan` — Narrative plan only (from existing model or from scratch via full pipeline)

### Scripts

```bash
# Validate a populated model (49 inputs, balance sheet, traffic mix, conversion hierarchy)
python bizplan-ecommerce/skills/ecommerce-financial-model/scripts/validate_model.py <path_to_model.xlsx>

# Convert markdown business plan to styled DOCX
python bizplan-ecommerce/skills/ecommerce-document-export/scripts/export_docx.py <input.md> <output.docx> --title "StoreName" [--date "March 2026"]

# Regenerate the Pandoc reference.docx template
python bizplan-ecommerce/skills/ecommerce-document-export/scripts/create_reference_doc.py
```

## Plugin Structure

Each vertical plugin follows the same layout:
```
bizplan-{vertical}/
├── .claude-plugin/plugin.json     # Plugin metadata
├── commands/                      # User-facing slash commands (markdown)
├── hooks/hooks.json               # Event hooks (currently empty)
└── skills/                        # Sequential skill processors
    └── {skill-name}/
        ├── SKILL.md               # Full skill instructions
        ├── TROUBLESHOOTING.md     # Known issues (assumptions, financial-model)
        ├── references/            # Schemas and maps (JSONC)
        ├── templates/             # Excel/DOCX templates
        ├── scripts/               # Python scripts
        ├── data/                  # Curated benchmark data
        └── requirements.txt       # Python dependencies
```

Output files are named `{StoreName}_intake.json`, `{StoreName}_assumptions.json`, `{StoreName}_Financial_Model.xlsx`, `{StoreName}_model_outputs.json`, `{StoreName}_Business_Plan.md/.docx`.

## Pipeline Architecture (Ecommerce)

The ecommerce vertical runs 5 sequential skills with **subagent isolation**. Step 1 runs inline (requires user interaction); Steps 2-5 run in forked subagent contexts (`context: fork`) with per-skill model routing. Each forked skill reads inputs from disk, operates in a clean context window, and writes outputs to disk.

1. **ecommerce-intake** (inline, user's model) — 22-question founder questionnaire across 8 sections with conditional branching → `{StoreName}_intake.json`
2. **ecommerce-assumptions** (`context: fork`, Sonnet) — Resolves all 49 financial drivers using category benchmarks from `data/us/{category}.json`, global/regional defaults, and calculation formulas → `{StoreName}_assumptions.json`
3. **ecommerce-financial-model** (`context: fork`, Sonnet) — Populates Excel template via XML editing, recalculates with xlcalculator, runs equity optimization loop → `{StoreName}_Financial_Model.xlsx` + `{StoreName}_model_outputs.json`
4. **ecommerce-business-plan** (`context: fork`, Opus) — 3-stage writer: market research (curated benchmarks + structured web search across 4 research areas), narrative (6,000-7,500 words, 7 sections), citation verification → `{StoreName}_Business_Plan.md`
5. **ecommerce-document-export** (`context: fork`, Haiku) — Pandoc conversion with `reference.docx` template → `{StoreName}_Business_Plan.docx`

The plan writer (Step 4) benefits most from isolation — it starts with a clean context window containing only its SKILL.md and the three JSON input files, giving maximum context budget to web research and 7k-word narrative generation.

### Key Schema Files (source of truth — never guess values)

| Schema | Location | Purpose |
|--------|----------|---------|
| `intake_schema.jsonc` | `ecommerce-intake/references/` | Questionnaire data structure, enums, validation rules |
| `driver_catalog.jsonc` | `ecommerce-assumptions/references/` | All 49 driver IDs, types, bounds (master reference) |
| `input_map.jsonc` | `ecommerce-financial-model/references/` | 49 driver → Excel cell address mappings (Assumptions sheet, column B, B5-B79) |
| `output_map.jsonc` | `ecommerce-financial-model/references/` | Model sheet output addresses (columns E-J for 2026-2031) |

## Critical Technical Rules

### Excel Writer — Use XML Editing, NOT openpyxl.save()
openpyxl's save corrupts charts and conditional formatting. Instead:
1. Open `.xlsx` as ZIP archive
2. Replace cell `<v>` tags via regex in sheet XML
3. Remove ALL cached `<v>` tags from formula cells across ALL sheets (forces recalculation)
4. Delete `xl/calcChain.xml` AND remove its entry from `[Content_Types].xml`
5. Set `fullCalcOnLoad="1"` on `<calcPr>` in `workbook.xml`
6. Write back to ZIP with `ZIP_DEFLATED` compression

### xlcalculator Workaround
Create aliases for all reference variants (`$D$9`, `D$9`, `$D9`, `D9`) when setting input values — xlcalculator doesn't normalize reference styles.

### Equity Optimization Loop
When equity mode is SUGGEST, iterate up to 5 times: if `min_cash < $1,000`, set `new_equity = (current_equity + abs(min_cash) + $1,000) × 1.15`, round to nearest $1,000, re-run full Excel write cycle. Output includes `equity_audit` with iteration history.

### DOCX Export Preprocessing
Before Pandoc conversion, the markdown is preprocessed: heading promotion (`## N. Section` → `# Section`), citation conversion (`[N]` → `^[N]^`), URL linking, horizontal rule removal, YAML front matter + static TOC insertion. After Pandoc, python-docx styles the cover page and adds table borders.

## Key Conventions

- Percentages are ALWAYS decimals (0.15 for 15%, NOT 15)
- Currency values are plain numbers (50000, NOT "$50,000")
- Year drivers are calendar years 2026-2031 (NOT "Year 1-6")
- Forecast period is always 6 years
- B73 (`loan_start_year`) is hardcoded to 2026 in the template — do NOT write it
- Business plan uses first-person plural ("we", "our") and pre-launch tense
- Business plan citations: CITE external market data, DO NOT CITE internal model projections
- Nullable intake fields (`target_customer`, `differentiation`, `founder_background`, `why_now`) — use `null` if founder was unsure; never fabricate qualitative context

## Data Layer

- 11 product categories with curated benchmarks: `bizplan-ecommerce/skills/ecommerce-assumptions/data/us/`
  - beauty_personal_care, baby_kids, electronics_gadgets, fashion_apparel, food_beverage, health_wellness, home_living, jewelry_accessories, other, pet_supplies, sports_outdoors
- Each category file has conversion rates (paid/organic/retention), CAC, AOV, margins, return rates, methodology, confidence scores, and source citations
- `global_defaults.json` — inflation rates (CPC 6%, shipping 6%, rent 3%)
- `regional_defaults.json` — 5 regions: US, UK, EU, Canada, Australia (tax rates, region-specific settings)

## Adding a New Vertical

1. Copy `bizplan-ecommerce/` as a starting point
2. Modify all 5 skills (SKILL.md), schemas, templates, and benchmark data for the new domain
3. Update commands in `commands/` for the new pipeline
4. Register the new plugin in `.claude-plugin/marketplace.json`
