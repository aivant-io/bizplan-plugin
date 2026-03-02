# Troubleshooting: Ecommerce Financial Model

## Common Issues

### 1. openpyxl save corrupts the workbook

**Symptom:** Charts disappear, conditional formatting lost, file won't open properly.

**Fix:** Never use `wb.save()` from openpyxl. Use direct XML editing: open the .xlsx as a ZIP, replace cell values via regex in the XML, write back to ZIP. This preserves all formatting, charts, and Excel internals.

### 2. Formulas show stale/old values when opened in Excel

**Symptom:** Output file shows template defaults instead of computed values.

**Fix:** Two things must happen:
1. Remove cached `<v>` tags from ALL formula cells on ALL sheets (not just the Assumptions sheet)
2. Delete `xl/calcChain.xml` from the ZIP to force Excel to rebuild the calculation chain

### 3. xlcalculator can't resolve absolute references ($D$9)

**Symptom:** `KeyError` or formula evaluation returns wrong values for cells using absolute references.

**Fix:** Create aliases for all reference variants when building the evaluator:
```python
# For each cell like "Assumptions!D9", also register:
# "Assumptions!$D$9", "Assumptions!$D9", "Assumptions!D$9"
```
Also set input values using all four variants.

### 4. Cell not found in template XML

**Symptom:** `ValueError: Cell B5 not found in template XML` during XML writing.

**Fix:** The cell must already exist in the template XML with a `<v>` tag. Ensure the template has placeholder values in all 49 input cells. If a cell is truly missing, it may be on a different sheet or the sheet XML path resolution failed.

### 5. Balance sheet doesn't balance (check != 0)

**Symptom:** Validation reports balance check values > 0.01.

**Possible causes:**
- A required input was not written (missing cell)
- A percentage was written as a whole number instead of decimal
- An integer driver was written as a float with decimals
- Formula evaluation error in xlcalculator

**Fix:** Re-run validation script (`scripts/validate_model.py`) to identify which inputs are missing or malformed. Fix the input values and regenerate.

### 6. Equity optimization doesn't converge

**Symptom:** After 5 iterations, cash balance is still negative.

**Fix:** The equity formula increases by `(deficit + $1,000) * 1.15` each iteration. If it doesn't converge in 5 iterations, the business model likely has structural issues (costs far exceed revenue potential). Check:
- Are COGS% and discount rates reasonable?
- Is the team cost proportional to revenue?
- Are there excessive fixed costs?

### 7. loan_start_year written to Excel

**Symptom:** Cell B73 modified from its hardcoded 2026 value.

**Fix:** `loan_start_year` is in the `driver_catalog.jsonc` but deliberately NOT in `input_map.jsonc`. It's in the EXCLUDED set. Never write to B73. The template has it hardcoded to 2026.

### 8. Wrong sheet XML path resolved

**Symptom:** Values written to wrong cells or not appearing.

**Fix:** Sheet names in `workbook.xml` may not match the XML file names (e.g., "Assumptions" sheet might be in `sheet2.xml`). Always resolve the path by:
1. Parse `xl/workbook.xml` → find `<sheet name="Assumptions" ... r:id="rId2"/>`
2. Parse `xl/_rels/workbook.xml.rels` → find `<Relationship Id="rId2" ... Target="worksheets/sheet2.xml"/>`
3. Use the resolved path `xl/worksheets/sheet2.xml`

### 9. ZIP write produces corrupted file

**Symptom:** Excel can't open the output file, or reports it's corrupted.

**Fix:** When writing back to ZIP:
- Use `zipfile.ZIP_DEFLATED` compression
- Write ALL files from the original ZIP (not just modified ones)
- Don't include `xl/calcChain.xml` (deliberately deleted)
- Ensure UTF-8 encoding for all XML content

### 10. Output extraction returns None for all metrics

**Symptom:** Model outputs are all null/None after extraction.

**Fix:** Check that:
- xlcalculator evaluator was created from the OUTPUT file (after writing), not the template
- All input values were set in the evaluator before evaluating output cells
- The sheet name in cell references matches exactly (case-sensitive): "Model" not "model"
- All reference variants ($D$9 etc.) were registered

### 11. Excel shows ERROR or blank cells on open (requires manual Cmd+Shift+F9)

**Symptom:** When opening the generated .xlsx in Excel, formula cells (especially on the balance sheet, e.g., E3) show "ERROR" or are blank. Pressing Cmd+Shift+F9 (macOS) or Ctrl+Shift+F9 (Windows) fixes everything.

**Root cause:** The file has all cached formula `<v>` tags removed and `calcChain.xml` deleted, but `xl/workbook.xml` is missing the `fullCalcOnLoad="1"` attribute on `<calcPr>`. Without this attribute, Excel does not know it needs to recalculate every formula from scratch on open.

**Fix:** After deleting `calcChain.xml`, also modify `xl/workbook.xml` to add `fullCalcOnLoad="1"`:
```python
wb_xml = files["xl/workbook.xml"].decode("utf-8")
wb_xml = re.sub(r'\s*fullCalcOnLoad="[^"]*"', '', wb_xml)  # avoid duplication
wb_xml = re.sub(r'<calcPr\b', r'<calcPr fullCalcOnLoad="1"', wb_xml)
files["xl/workbook.xml"] = wb_xml.encode("utf-8")
```

**Verification:** Open the generated .xlsx in Excel. All formula cells should display computed values immediately without any manual recalculation.

## Validation Script Usage

```bash
# Run validation on a populated model
python scripts/validate_model.py output/my_model.xlsx

# Expected output for a valid model:
# PASSED
#   Total input cells checked: 49
#   Errors: 0
#   Warnings: 0
```
