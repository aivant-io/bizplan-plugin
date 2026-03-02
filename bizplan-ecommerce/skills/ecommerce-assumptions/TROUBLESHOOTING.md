# Troubleshooting: Ecommerce Assumptions

## Common Issues

### 1. Percentages written as whole numbers (e.g., 15 instead of 0.15)

**Symptom:** Model shows wildly wrong values (1500% growth, 200% conversion).

**Fix:** All `float_pct` values must be decimals. Write `0.15` for 15%, not `15`. Check every percentage driver before outputting.

### 2. Traffic mix doesn't sum to 1.0

**Symptom:** Validation error on traffic mix constraint.

**Fix:** After deriving channel mix weights, always normalize: divide each by the sum of all three. Verify `traffic_mix_paid_pct + traffic_mix_organic_pct + traffic_mix_retention_pct = 1.0` (within 0.01 tolerance).

### 3. Conversion hierarchy violated

**Symptom:** Warning that `conv_paid > conv_organic` or `conv_organic > conv_retention`.

**Fix:** Maintain the hierarchy `retention >= organic >= paid`. If category benchmarks suggest otherwise, note it but adjust to maintain the hierarchy. Retention visitors (email/SMS subscribers) should always convert at higher rates than cold paid traffic.

### 4. Equity suggestion produces $0 or negative value

**Symptom:** Equity calculation returns nonsensical value.

**Fix:** Check the equity formula inputs:
- Ensure `monthly_burn` is positive (costs should be > 0)
- Ensure `runway_months` is set (conservative=6, base=9, aggressive=12)
- Apply the $10,000 floor: `equity_final = max(10000, rounded_value)`
- Subtract loan amount only after applying the buffer

### 5. Missing benchmark data for category

**Symptom:** No benchmark file found in `data/us/{category}.json`.

**Fix:** Fall back to `data/global_defaults.json`. If the category is not in the 11 supported categories, use `other` as the category key.

### 6. Year drivers outside 2026-2031

**Symptom:** Validation error on year range.

**Fix:** All year-type drivers must be between 2026 and 2031 inclusive. If a start year calculates to before 2026, use 2026. If after 2031, cap at 2031.

### 7. Start year set to distant future when amount is 0

**Symptom:** Warehouse or office rent start year is 2030+ but the amount is $0.

**Fix:** When the associated rent amount is $0, always default the start year to 2026. The year is economically irrelevant when the amount is zero.

### 8. Double-counting fixed overhead and rent

**Symptom:** Total fixed costs are unreasonably high.

**Fix:** The `other_fixed_costs_*` budget is for non-rent overhead only (software, admin, accounting/legal). Rent is modeled separately via `warehouse_rent_*` and `office_rent_*` drivers. Never include rent in the `prof_fees_year1` or `misc_ga_year1` allocation.

### 9. Channel mix with no paid channels

**Symptom:** Paid mix is non-zero even though user selected no paid channels.

**Fix:** If `paid_ads` is NOT in `primary_channels` or `cac_mode = none`, set `traffic_mix_paid_pct = 0` and use the fallback split: organic=0.60, retention=0.40.

### 10. CPC calculated as 0

**Symptom:** CPC Year 1 is $0 even though paid channels are active.

**Fix:** CPC formula is `cpc_year1 = cac_paid_target * conv_paid`. If CAC or conversion is 0, CPC will be 0. Ensure both values are resolved before computing CPC.

## Validation Quick Checks

Before outputting resolved assumptions, verify:

- [ ] All 49 `input_id` values present
- [ ] All percentages are decimals (0.0 to 1.0 range)
- [ ] Traffic mix sums to 1.0
- [ ] Years between 2026-2031
- [ ] Currency values are plain numbers (no $ prefix)
- [ ] Conversion hierarchy maintained
- [ ] `__internal_targets` included but NOT in the inputs array
- [ ] `loan_start_year` is NOT in the inputs array (hardcoded in template)
