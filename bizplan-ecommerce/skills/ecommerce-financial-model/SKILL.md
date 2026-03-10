---
name: ecommerce-financial-model
description: >
  Populates a pre-built Excel financial model template with 49 resolved driver
  values using direct XML editing (preserves formatting and charts). Recalculates
  all formulas in-memory via xlcalculator, extracts computed outputs (revenue,
  margins, cash flow, unit economics), and validates balance sheet integrity.
  Includes equity optimization loop to ensure positive cash balance. Use after
  the ecommerce-assumptions skill has resolved all driver values.
context: fork
model: sonnet
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Ecommerce Financial Model

## Overview

This skill takes resolved assumptions (49 driver values from the ecommerce-assumptions skill) and populates a pre-built Excel template to produce a 6-year financial model with income statement, balance sheet, cash flow statement, and key metrics.

**Inputs:** Resolved assumptions JSON (from the ecommerce-assumptions skill)
**Outputs:** Populated Excel file (.xlsx) + extracted model outputs JSON

For cell-to-driver mappings, see [references/input_map.jsonc](references/input_map.jsonc).
For output extraction addresses, see [references/output_map.jsonc](references/output_map.jsonc).
Template file: [templates/eCommerce_Model_v1.xlsx](templates/eCommerce_Model_v1.xlsx).

## File Inputs & Outputs

This skill is invoked with the store name as its argument: `$ARGUMENTS`

**Read from the current working directory:**
- Assumptions JSON file, named `{StoreName}_assumptions.json` (using the store name provided above)

**Read from the skill directory:**
- `${CLAUDE_SKILL_DIR}/references/input_map.jsonc` — driver-to-cell address mappings
- `${CLAUDE_SKILL_DIR}/references/output_map.jsonc` — output cell addresses for extraction
- `${CLAUDE_SKILL_DIR}/templates/eCommerce_Model_v1.xlsx` — Excel template (copy, never modify original)
- `${CLAUDE_SKILL_DIR}/requirements.txt` — Python dependencies

**Write to the current working directory:**
- `{StoreName}_Financial_Model.xlsx` — populated Excel model
- `{StoreName}_model_outputs.json` — extracted metrics for the business plan writer

## Architecture

The Excel writer uses **direct XML editing** instead of openpyxl's load/save cycle. This is critical because openpyxl's save corrupts formatting, charts, conditional formatting, and other Excel internals. By editing the raw XML inside the .xlsx ZIP archive, we preserve everything.

```
Resolved Assumptions
    |
    [1] Build cell updates (input_id -> cell_address -> value)
    |
    [2] Write values via XML replacement (surgical, preserves formatting)
    |
    [3] Remove cached formula values (force recalculation)
    |
    [4] Extract outputs via xlcalculator (in-memory formula evaluation)
    |
    [5] Validate balance sheet (Assets - Liabilities - Equity ~ 0)
    |
    [6] Equity optimization (iterate if needed)
    |
Populated Excel + Model Outputs
```

## Step-by-Step Process

### Step 1: Install Dependencies

Ensure Python packages are available:

```bash
pip install openpyxl>=3.1.2 xlcalculator>=0.5.0
```

### Step 2: Build Cell Updates

Read `references/input_map.jsonc` to map each `input_id` to its cell address. For each resolved assumption, create a cell update entry.

**All 49 inputs are on the "Assumptions" sheet** in column B:

| Section | Cell Range | Drivers |
|---------|-----------|---------|
| Traffic | B5-B11 | total visits, YoY growth, paid/organic/retention mix |
| Conversion | B15-B17 | paid, organic, retention conversion rates |
| Repeat Purchase | B20-B22 | repeat rate, frequency, retention improvement |
| Order Economics | B25-B32 | AOV, AOV inflation, COGS%, COGS improvement, discounts, returns, payment fee, platform fee |
| Marketing | B35-B36 | CPC Year 1, CPC inflation |
| Fulfillment | B39-B43 | shipping cost, shipping inflation, handling, packaging, support |
| Warehouse Rent | B46-B48 | amount, start year, inflation |
| Office & G&A | B51-B59 | office rent (amount, start year, inflation), salaries, months to full team, prof fees, salary inflation, misc G&A, monthly SaaS |
| Working Capital | B62-B65 | AR days, inventory days, inventory improvement, AP days |
| Capex | B68-B69 | capex % of net revenue, depreciation period |
| Financing | B72-B76 | loan amount, interest rate, loan term, equity injection |
| Tax | B79 | tax rate |

**Excluded:** `loan_start_year` is hardcoded to 2026 in the template. Do NOT write it.

### Step 3: Type Conversion

Convert each value to the correct type before writing:

| Schema Type | Python Type | Example |
|-------------|-------------|---------|
| `int` | `int` | `12000` |
| `float` | `float` | `45.5` |
| `float_pct` | `float` (decimal) | `0.15` for 15% |
| `currency` | `float` (no prefix) | `50000.0` |
| `year` | `int` | `2026` |

**CRITICAL:** Percentages are ALWAYS decimals. Write `0.15` for 15%, NOT `15`. Excel cells are pre-formatted to display as percentages.

### Step 4: Write Values via Direct XML Editing

Write a Python script that:

1. **Opens the .xlsx as a ZIP archive** — `.xlsx` files are ZIP archives containing XML files
2. **Resolves sheet XML paths** — Parse `xl/workbook.xml` to find sheet name-to-rId mapping, then `xl/_rels/workbook.xml.rels` to find rId-to-file mapping
3. **Replaces cell values via regex** — For each cell update, find and replace the `<v>` tag value:

```python
import re, zipfile, shutil
from pathlib import Path

def write_cells_via_xml(template_path, output_path, cell_updates):
    """Write cell values by directly editing XML inside the xlsx ZIP."""
    shutil.copy2(template_path, output_path)

    # Read all files from the ZIP
    with zipfile.ZipFile(output_path, "r") as zf:
        files = {name: zf.read(name) for name in zf.namelist()}

    # Resolve sheet XML path
    sheet_xml_path = resolve_sheet_path(files, "Assumptions")
    xml = files[sheet_xml_path].decode("utf-8")

    # Replace each cell value
    for cell_ref, value in cell_updates.items():
        pattern = rf'(<c[^>]*\sr="{cell_ref}"[^>]*>.*?<v>)[^<]*(</v>)'
        xml, count = re.subn(pattern, rf'\g<1>{value}\g<2>', xml, count=1, flags=re.DOTALL)
        if count == 0:
            # Cell may not have existing <v> tag — handle insertion
            raise ValueError(f"Cell {cell_ref} not found in template XML")

    files[sheet_xml_path] = xml.encode("utf-8")

    # Remove cached formula values from ALL sheets (critical!)
    for name in list(files.keys()):
        if name.startswith("xl/worksheets/") and name.endswith(".xml"):
            sheet_xml = files[name].decode("utf-8")
            # Remove <v>...</v> from cells that have <f>...</f> formulas
            sheet_xml = re.sub(
                r'(<c[^>]*>(?:<is>.*?</is>)?<f[^/]*>.*?</f>)<v>[^<]*</v>',
                r'\1', sheet_xml, flags=re.DOTALL
            )
            # Also handle self-closing formula tags <f/>
            sheet_xml = re.sub(
                r'(<c[^>]*><f/>)<v>[^<]*</v>',
                r'\1', sheet_xml, flags=re.DOTALL
            )
            files[name] = sheet_xml.encode("utf-8")

    # Delete calcChain.xml to force full recalculation
    files.pop("xl/calcChain.xml", None)

    # Also remove the calcChain reference from [Content_Types].xml
    if "[Content_Types].xml" in files:
        ct = files["[Content_Types].xml"].decode("utf-8")
        ct = re.sub(r'<Override[^>]*calcChain[^>]*/>', '', ct)
        files["[Content_Types].xml"] = ct.encode("utf-8")

    # Force Excel to recalculate all formulas on open
    if "xl/workbook.xml" in files:
        wb_xml = files["xl/workbook.xml"].decode("utf-8")
        wb_xml = re.sub(r'\s*fullCalcOnLoad="[^"]*"', '', wb_xml)  # avoid duplication
        wb_xml = re.sub(r'<calcPr\b', r'<calcPr fullCalcOnLoad="1"', wb_xml)
        files["xl/workbook.xml"] = wb_xml.encode("utf-8")

    # Write back to ZIP
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
```

**Why remove cached formula values?** The template contains stale `<v>` tags for formula cells. If not removed, Excel/Numbers/Google Sheets will show old values until the user manually recalculates. Removing them forces recalculation on open.

**Why delete calcChain.xml?** This file tells Excel the order to calculate formulas. Deleting it forces Excel to rebuild the chain, ensuring all formulas reflect the new input values. Also remove the calcChain reference from `[Content_Types].xml` to prevent Excel from showing a repair dialog.

**Why add `fullCalcOnLoad="1"`?** After removing cached `<v>` tags and deleting `calcChain.xml`, Excel needs an explicit signal to perform a full recalculation when opening the file. The `fullCalcOnLoad="1"` attribute on the `<calcPr>` element in `xl/workbook.xml` provides this signal. Without it, Excel may show blank or ERROR cells that require the user to manually press Cmd+Shift+F9 (macOS) or Ctrl+Shift+F9 (Windows).

### Step 5: Extract Model Outputs via xlcalculator

After writing values, use xlcalculator to evaluate formulas in Python (without needing Excel installed):

```python
from xlcalculator import ModelCompiler as compiler
from xlcalculator import Evaluator

def extract_outputs(output_path, cell_updates):
    """Evaluate formulas and extract computed outputs."""
    model = compiler.read_and_parse_archive(str(output_path))

    # WORKAROUND: xlcalculator can't resolve absolute references ($D$9)
    # Create aliases for all reference styles
    for key in list(model.cells.keys()):
        if "!" not in key:
            continue
        sheet_part, cell_ref = key.split("!", 1)
        match = re.match(r"([A-Z]+)(\d+)", cell_ref)
        if not match:
            continue
        col, row = match.groups()
        # Create $D$9, $D9, D$9 variants
        model.cells[f"{sheet_part}!${col}${row}"] = model.cells[key]
        model.cells[f"{sheet_part}!${col}{row}"] = model.cells[key]
        model.cells[f"{sheet_part}!{col}${row}"] = model.cells[key]

    evaluator = Evaluator(model)

    # Set all input values (with all reference variants)
    for cell_ref, value in cell_updates.items():
        set_xlcalc_input(evaluator, "Assumptions", cell_ref, value)

    # Read outputs from Model sheet using output_map.jsonc addresses
    outputs = {}
    # Example: read net_revenue for all years
    for year_num, col in [(1, "E"), (2, "F"), (3, "G"), (4, "H"), (5, "I"), (6, "J")]:
        cell = f"Model!{col}139"
        try:
            outputs[f"net_revenue_year_{year_num}"] = evaluator.evaluate(cell)
        except Exception:
            outputs[f"net_revenue_year_{year_num}"] = None

    return outputs

def set_xlcalc_input(evaluator, sheet_name, cell_address, value):
    """Set value in evaluator with all reference variants."""
    match = re.match(r"([A-Z]+)(\d+)", cell_address)
    col, row = match.groups()
    variants = [
        f"{sheet_name}!{cell_address}",
        f"{sheet_name}!${col}${row}",
        f"{sheet_name}!${col}{row}",
        f"{sheet_name}!{col}${row}",
    ]
    for variant in variants:
        try:
            evaluator.set_cell_value(variant, value)
        except Exception:
            pass  # Some variants may not exist in the model
```

### Step 6: Read All Output Metrics

Read outputs from the "Model" sheet using addresses from `references/output_map.jsonc`. Column mapping: E=Year 1 (2026), F=Year 2, G=Year 3, H=Year 4, I=Year 5, J=Year 6.

**Key output sections:**

| Section | Metrics | Row Range |
|---------|---------|-----------|
| Orders | total visits, new orders, repeat orders, total orders | E24, E37-E41 |
| Income Statement | gross/net revenue, gross profit, contribution margin, EBITDA, EBT, net income | E134-E167 |
| Balance Sheet | cash, AR, inventory, total assets/liabilities/equity, balance check | E175-E194 |
| Cash Flow | operating/investing/financing cash flow, closing cash balance | E205-E222 |
| Operating Metrics | CAC, contribution margin/order, payback orders, burn rate | E255-E258 |
| Expenses | marketing, shipping, packaging, support, total variable, total fixed, SaaS, total G&A | E97-E158 |

**Derived metrics** (computed from raw outputs, not from cells):
- **Revenue CAGR**: `((net_revenue_year_6 / net_revenue_year_1) ^ 0.2) - 1`
- **Break-even year**: First year where `net_income > 0` (or null)
- **Runway months**: If `burn_rate_year_1 < 0`: `closing_cash_year_1 / abs(burn_rate_year_1 / 12)`

### Step 7: Validate Balance Sheet

After extracting outputs, validate the balance check row (E194:J194):

```python
def validate_balance(outputs):
    """Balance check: Assets - Liabilities - Equity should be ~0."""
    tolerance = 0.01
    for year in range(1, 7):
        check_value = outputs.get(f"balance_check_year_{year}", 0)
        if abs(check_value) > tolerance:
            return False, f"Balance check failed in Year {year}: {check_value}"
    return True, "Balance sheet validates"
```

### Step 8: Equity Optimization

After the initial Excel write, run the equity optimization loop. This ensures the business has positive cash balance across all forecast years.

**Two modes based on `equity_mode` from intake:**

#### Mode A: SUGGEST (Iterate to Positive Cash)

```
while min_cash < $1,000 buffer AND iterations < 5:
    deficit = abs(min_cash) + $1,000
    new_equity = current_equity + deficit * 1.15
    new_equity = round_to_nearest_$1,000(new_equity)

    Update initial_equity_injection in resolved assumptions
    Re-run Excel Writer (Steps 4-7) with new equity value

    min_cash = minimum closing_cash_balance across all 6 years
    iterations += 1
```

**Cash balance check**: Read `closing_cash_balance` for all years (E222:J222 on Model sheet). Find the minimum value across all years.

**Convergence**: The loop stops when either:
- `min_cash >= $1,000` (positive cash achieved)
- `iterations >= 5` (max attempts reached)

**If max iterations reached without convergence**: Proceed with the final equity value from iteration 5. Append a warning to the equity_warning field in the model outputs:
- Format: `"**Funding Note:** Equity optimization ran 5 iterations without achieving a +$1,000 cash buffer (final min cash: $X). The recommended equity injection of $Y is the best approximation. Consider adjusting pricing, margins, or team costs to improve cash flow, or plan for additional funding rounds."`
- This warning is passed to the business plan writer and included in the Financial Plan section.

#### Mode B: EXPLICIT (User-Specified, No Changes)

Do NOT modify the user's equity amount. If cash goes negative:
- Generate a warning message for the business plan
- Format: `"**Funding Note:** Cash projected negative in Year X ($Y). Consider additional $Z in funding."`
- The warning is appended to the business plan by the orchestrator

### Step 9: Produce Final Outputs

The final output includes:

1. **Excel file** (.xlsx) — saved to the output directory
2. **Model outputs JSON** — structured metrics for the business plan writer:

```json
{
  "orders": {
    "total_orders": {"year_1": 3000, "year_2": 4200, ...},
    "total_visits": {"year_1": 200000, ...},
    "new_orders": {"year_1": 2400, ...},
    "repeat_orders": {"year_1": 600, ...}
  },
  "income_statement": {
    "gross_revenue": {"year_1": 165000, ...},
    "net_revenue": {"year_1": 152000, ...},
    "gross_profit": {"year_1": 76000, ...},
    "gross_margin_pct": {"year_1": 0.50, ...},
    "ebitda": {"year_1": -12000, ...},
    "net_income": {"year_1": -15000, ...}
  },
  "cash_flow": {
    "closing_cash_balance": {"year_1": 35000, ...}
  },
  "operating_metrics": {
    "cac": {"year_1": 20.0, ...},
    "contribution_margin_per_order": {"year_1": 12.5, ...},
    "payback_orders": {"year_1": 1.6, ...},
    "burn_rate": {"year_1": -18000, ...}
  },
  "derived": {
    "revenue_cagr": 0.35,
    "break_even_year": 2028,
    "runway_months": 23.3
  },
  "validation": {
    "balance_check_passed": true,
    "inputs_written": 49
  },
  "equity_audit": {
    "mode": "suggest",
    "initial_estimate": 318000,
    "iterations": [
      {"iteration": 1, "equity_tested": 318000, "min_cash": -1176265, "min_cash_year": 2031, "result": "deficit"},
      {"iteration": 2, "equity_tested": 1672000, "min_cash": 177735, "min_cash_year": 2031, "result": "converged"}
    ],
    "final_equity": 1672000,
    "converged": true,
    "total_iterations": 2,
    "final_min_cash": 177735,
    "final_min_cash_year": 2031
  }
}
```

**`equity_audit` fields:**
- `mode`: `"suggest"` or `"explicit"` — from intake `equity_mode`
- `initial_estimate`: Starting equity from assumptions Step 12 (suggest mode) or user's amount (explicit mode)
- `iterations`: Array of each optimization loop pass — equity tested, resulting min cash, which year, and outcome
- `final_equity`: The value written to cell B76
- `converged`: `true` if min_cash >= $1,000; `false` if max iterations reached; `null` for explicit mode
- `total_iterations`: Number of optimization passes (0 for explicit mode)
- `final_min_cash` / `final_min_cash_year`: Lowest closing cash and when it occurs

For explicit mode, the audit captures the user's amount and the resulting cash position without iteration:
```json
{
  "equity_audit": {
    "mode": "explicit",
    "initial_estimate": 80000,
    "iterations": [],
    "final_equity": 80000,
    "converged": null,
    "total_iterations": 0,
    "final_min_cash": -1176265,
    "final_min_cash_year": 2031
  }
}
```

## Complete Cell Reference

All 49 input cells on the "Assumptions" sheet:

| Cell | input_id | Type | Description |
|------|----------|------|-------------|
| B5 | traffic_total_year1 | int | Total annual site visits |
| B6 | traffic_yoy_growth | float_pct | Annual traffic growth |
| B9 | traffic_mix_paid_pct | float_pct | Paid traffic share |
| B10 | traffic_mix_organic_pct | float_pct | Organic traffic share |
| B11 | traffic_mix_retention_pct | float_pct | Retention traffic share |
| B15 | conv_paid | float_pct | Paid conversion rate |
| B16 | conv_organic | float_pct | Organic conversion rate |
| B17 | conv_retention | float_pct | Retention conversion rate |
| B20 | repeat_purchase_rate_year1 | float_pct | Year 1 repeat rate |
| B21 | repeat_purchase_frequency | float | Repeat orders/year |
| B22 | retention_improvement_annual | float_pct | Annual retention improvement |
| B25 | aov_year1 | currency | Average order value |
| B26 | aov_inflation | float_pct | AOV annual inflation |
| B27 | cogs_pct | float_pct | Cost of goods sold % |
| B28 | cogs_annual_improvement_pct | float_pct | Annual COGS improvement |
| B29 | discounts_promos_pct | float_pct | Discounts & promotions |
| B30 | return_rate_pct | float_pct | Return/refund rate |
| B31 | payment_processing_pct | float_pct | Payment processing fee |
| B32 | platform_fee_pct | float_pct | Platform/marketplace fee |
| B35 | cpc_year1 | currency | Cost per click Year 1 |
| B36 | cpc_inflation | float_pct | CPC annual inflation |
| B39 | ship_cost_year1 | currency | Shipping cost per order |
| B40 | ship_inflation | float_pct | Shipping cost inflation |
| B41 | handling_cost_year1 | currency | Handling cost per order |
| B42 | packaging_cost_per_order | currency | Packaging cost per order |
| B43 | support_cost_per_order | currency | Support cost per order |
| B46 | warehouse_rent_amount_when_active | currency | Warehouse rent |
| B47 | warehouse_rent_start_year | year | Warehouse rent start |
| B48 | warehouse_rent_inflation | float_pct | Warehouse rent inflation |
| B51 | office_rent_amount_when_active | currency | Office rent |
| B52 | office_rent_start_year | year | Office rent start |
| B53 | office_rent_inflation | float_pct | Office rent inflation |
| B54 | salaries_year1 | currency | Total salaries Year 1 |
| B55 | months_to_full_team | int | Months to full headcount |
| B56 | prof_fees_year1 | currency | Professional fees Year 1 |
| B57 | sal_prof_inflation | float_pct | Salary/fees inflation |
| B58 | misc_ga_year1 | currency | Miscellaneous G&A Year 1 |
| B59 | monthly_saas_costs | currency | Monthly SaaS/tech costs |
| B62 | ar_days | float | Accounts receivable days |
| B63 | inventory_days_year1 | float | Inventory days Year 1 |
| B64 | inventory_turns_improvement | float_pct | Inventory improvement |
| B65 | ap_days | float | Accounts payable days |
| B68 | capex_pct_of_net_rev | float_pct | Capex as % of net revenue |
| B69 | dep_period_years | int | Depreciation period |
| B72 | initial_loan_amount | currency | Initial loan amount |
| B74 | interest_rate | float_pct | Loan interest rate |
| B75 | loan_term_years | int | Loan term in years |
| B76 | initial_equity_injection | currency | Initial equity injection |
| B79 | tax_rate | float_pct | Tax rate |

**Note:** B73 (loan start year) is hardcoded to 2026 in the template. Do NOT write to it.

## Validation Checklist

Run `scripts/validate_model.py` after generation to verify:

1. **All 49 inputs written** — no missing cells
2. **Type correctness** — percentages as decimals, years as integers, currency as floats
3. **Balance sheet check** — E194:J194 all within ±0.01 of zero
4. **Traffic mix sum** — B9 + B10 + B11 = 1.0 (±0.01)
5. **Year range** — B47, B52 between 2026 and 2031
6. **Non-negative** — revenue, orders, cash metrics are reasonable
7. **Conversion hierarchy** — B17 >= B16 >= B15 (soft check)

## Critical Rules

1. **Never use openpyxl to save** — it corrupts formatting and charts. Use direct XML editing only.
2. **Always remove cached formula values** — from ALL sheets, not just Assumptions.
3. **Always delete calcChain.xml** — forces Excel to rebuild the calculation chain. Also remove its reference from `[Content_Types].xml`.
4. **Always set `fullCalcOnLoad="1"` in workbook.xml** — after deleting calcChain.xml, add `fullCalcOnLoad="1"` to the `<calcPr>` element so Excel recalculates all formulas on open.
5. **Percentages are ALWAYS decimals** — 0.15 for 15%, NEVER 15.
6. **Currency values are plain numbers** — 50000.0, NOT "$50,000".
7. **Never write loan_start_year** — B73 is hardcoded to 2026, it is in the EXCLUDED set.
8. **xlcalculator absolute reference workaround** — always create $D$9, $D9, D$9 aliases.
9. **Set values in ALL reference variants** — when using xlcalculator's set_cell_value.
10. **Template location** — always copy from `templates/eCommerce_Model_v1.xlsx`, never modify the template.
11. **Equity optimization re-runs the full write cycle** — each iteration writes all 49 values again.
