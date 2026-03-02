# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Claude plugin marketplace containing business plan and financial model generators for pre-launch founders. Each vertical (ecommerce, SaaS, etc.) is a self-contained plugin in its own directory, following the Claude Code plugin format (`.claude-plugin/plugin.json` + skills + commands + hooks). The marketplace manifest at `.claude-plugin/marketplace.json` registers all available plugins.

## Dependencies

- Python 3.11+
- `openpyxl>=3.1.2` and `xlcalculator>=0.5.0` (see `bizplan-ecommerce/skills/ecommerce-financial-model/requirements.txt`)
- Pandoc (optional, for DOCX export; falls back to markdown delivery)

## Commands

- `/bizplan` — Full 5-stage pipeline: intake → assumptions → Excel model → business plan → DOCX export
- `/financial-model` — Stages 1-3 only (intake → assumptions → Excel model)
- `/business-plan` — Narrative plan only (from existing model or from scratch)

### Validation

```bash
python bizplan-ecommerce/skills/ecommerce-financial-model/scripts/validate_model.py <path_to_model.xlsx>
```
Checks: all 49 inputs populated, type correctness, balance sheet balances, traffic mix sums to 1.0, conversion hierarchy (retention ≥ organic ≥ paid).

## Pipeline Architecture (Ecommerce)

The ecommerce vertical runs 5 sequential skills, each consuming the prior stage's output:

1. **ecommerce-intake** — 22-question founder questionnaire across 8 sections with conditional branching → intake JSON (`intake_schema.jsonc`)
2. **ecommerce-assumptions** — Resolves all 49 financial drivers using category benchmarks from `data/us/{category}.json`, global/regional defaults, and calculation formulas → assumptions JSON
3. **ecommerce-financial-model** — Populates Excel template via XML editing, recalculates with xlcalculator, runs equity optimization loop → `.xlsx` + model outputs JSON
4. **ecommerce-business-plan** — 3-stage writer: market research (curated benchmarks + structured web search across 4 research areas), narrative (5,500-7,000 words, 7 sections), citation verification → markdown
5. **ecommerce-document-export** — Pandoc conversion with `reference.docx` template → `.docx`

## Critical Technical Rules

### Excel Writer — Use XML Editing, NOT openpyxl.save()
openpyxl's save corrupts charts and conditional formatting. Instead:
1. Open `.xlsx` as ZIP archive
2. Replace cell `<v>` tags via regex in sheet XML
3. Remove ALL cached `<v>` tags from formula cells (forces recalculation)
4. Delete `xl/calcChain.xml` (forces Excel to rebuild calculation chain)
5. Write back to ZIP with `ZIP_DEFLATED` compression

### xlcalculator Workaround
Create aliases for all reference variants (`$D$9`, `D$9`, `$D9`, `D9`) when setting input values — xlcalculator doesn't normalize reference styles.

### Equity Optimization Loop
When equity mode is SUGGEST, iterate up to 5 times: if `min_cash < $1,000`, set `new_equity = current_equity + abs(min_cash) + $1,000) × 1.15`, round to nearest $1,000, re-run full Excel write cycle.

## Key Conventions

- Percentages are ALWAYS decimals (0.15 for 15%, NOT 15)
- Currency values are plain numbers (50000, NOT "$50,000")
- Year drivers are calendar years 2026-2031 (NOT "Year 1-6")
- Forecast period is always 6 years
- All 49 drivers defined in `driver_catalog.jsonc` — source of truth for IDs, types, bounds
- All 49 cell addresses defined in `input_map.jsonc` — never guess cells (all on Assumptions sheet, column B, rows B5-B79)
- Model outputs extracted per `output_map.jsonc` (Model sheet, columns E-J for years 2026-2031)

## Data Layer

- 11 product categories with curated benchmarks: `bizplan-ecommerce/skills/ecommerce-assumptions/data/us/`
- Each category file has conversion rates, return rates, methodology, confidence scores, and source citations
- `global_defaults.json` — inflation rates (CPC 6%, shipping 6%, rent 3%)
- `regional_defaults.json` — region-specific settings

## Adding a New Vertical

1. Copy `bizplan-ecommerce/` as a starting point
2. Modify all skills, schemas, templates, and benchmark data for the new domain
3. Register in `.claude-plugin/marketplace.json`
