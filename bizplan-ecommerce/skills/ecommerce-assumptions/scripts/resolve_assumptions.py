#!/usr/bin/env python3
"""Resolve all financial model driver values from a founder's intake JSON.

Reads ``{StoreName}_intake.json`` from the working directory (or ``--output-dir``),
resolves 50 driver values using curated category benchmarks, regional defaults,
and hardcoded mapping tables, then writes ``{StoreName}_assumptions.json``.

Usage::

    python resolve_assumptions.py {StoreName} [--output-dir DIR] [--verbose]

Exit codes:
    0  Success
    1  Validation error (output written but bounds warnings present)
    2  File or IO error (missing intake, missing data files, etc.)
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths relative to this script
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / ".." / "data" / "us"
REGIONAL_DEFAULTS_PATH = SCRIPT_DIR / ".." / "data" / "regional_defaults.json"
DRIVER_CATALOG_PATH = SCRIPT_DIR / ".." / "references" / "driver_catalog.jsonc"

logger = logging.getLogger("resolve_assumptions")

# ---------------------------------------------------------------------------
# JSONC Parser
# ---------------------------------------------------------------------------

def strip_jsonc(text: str) -> str:
    """Strip ``//`` and ``/* */`` comments from JSONC without breaking URLs in strings.

    Uses a character-by-character parser that tracks whether the cursor is
    inside a quoted string (handling ``\\"`` escapes).  After comment removal
    it also strips trailing commas before ``}`` or ``]``.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    in_string = False

    while i < n:
        ch = text[i]

        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                # Escaped character -- emit it and skip
                i += 1
                out.append(text[i])
            elif ch == '"':
                in_string = False
            i += 1
            continue

        # Outside a string
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue

        # Single-line comment
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            # Skip until end of line
            i += 2
            while i < n and text[i] != "\n":
                i += 1
            continue

        # Block comment
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i < n:
                if text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                    i += 2
                    break
                i += 1
            continue

        out.append(ch)
        i += 1

    result = "".join(out)

    # Remove trailing commas before } or ]
    result = re.sub(r",\s*([}\]])", r"\1", result)
    return result


def load_jsonc(path: Path) -> Any:
    """Load a JSONC file, stripping comments before parsing."""
    raw = path.read_text(encoding="utf-8")
    return json.loads(strip_jsonc(raw))


def load_json(path: Path) -> Any:
    """Load a plain JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Lookup / mapping tables (all from the user specification)
# ---------------------------------------------------------------------------

CATEGORY_MAP: dict[str, str] = {
    "apparel": "fashion_apparel",
    "fashion_apparel": "fashion_apparel",
    "beauty_personal_care": "beauty_personal_care",
    "food_beverage": "food_beverage",
    "home_living": "home_living",
    "consumer_electronics": "electronics_gadgets",
    "electronics_gadgets": "electronics_gadgets",
    "other_physical_products": "other",
    "other": "other",
    "health_wellness": "health_wellness",
    "pet_supplies": "pet_supplies",
    "baby_kids": "baby_kids",
    "sports_outdoors": "sports_outdoors",
    "jewelry_accessories": "jewelry_accessories",
}

ORDERS_MAP: dict[str, dict[str, int]] = {
    "lt_1k":  {"conservative": 300,   "base": 700,    "aggressive": 1000},
    "1_5k":   {"conservative": 1500,  "base": 3000,   "aggressive": 5000},
    "5_20k":  {"conservative": 6000,  "base": 12000,  "aggressive": 20000},
    "gt_20k": {"conservative": 25000, "base": 40000,  "aggressive": 60000},
}

GROSS_MARGIN_BAND: dict[str, float] = {"low": 0.35, "medium": 0.50, "high": 0.65}

CAC_BAND: dict[str, float] = {"lt_10": 7.50, "10_30": 20.00, "30_80": 55.00, "gt_80": 100.00}

FIXED_COSTS_BAND: dict[str, float] = {"lean": 6000, "moderate": 18000, "heavy": 42000}

CONV_MAP: dict[str, dict[str, float]] = {
    "hard":      {"paid": 0.010, "organic": 0.020, "retention": 0.080},
    "average":   {"paid": 0.015, "organic": 0.030, "retention": 0.100},
    "easy":      {"paid": 0.020, "organic": 0.040, "retention": 0.120},
    "very_easy": {"paid": 0.025, "organic": 0.050, "retention": 0.150},
}

MIX_BASE: dict[str, dict[str, float]] = {
    "profit_first": {"paid": 0.25, "organic": 0.35, "retention": 0.40},
    "balanced":     {"paid": 0.40, "organic": 0.35, "retention": 0.25},
    "growth_first": {"paid": 0.55, "organic": 0.30, "retention": 0.15},
}

AOV_BAND: dict[str, float] = {"lt_30": 25, "30_80": 55, "80_200": 140, "gt_200": 275}

DISCOUNT_MAP: dict[str, float] = {
    "profit_first": 0.05,
    "balanced": 0.175,
    "growth_first": 0.30,
}

RETURN_RATES: dict[str, float] = {
    "fashion_apparel": 0.20,
    "beauty_personal_care": 0.08,
    "home_living": 0.10,
    "electronics_gadgets": 0.12,
    "food_beverage": 0.03,
    "health_wellness": 0.06,
    "pet_supplies": 0.05,
    "sports_outdoors": 0.12,
    "baby_kids": 0.10,
    "jewelry_accessories": 0.15,
    "other": 0.10,
}

PAYMENT_PROCESSING: dict[str, float] = {
    "dtc_website": 0.029,
    "amazon": 0.00,
    "etsy": 0.029,
    "multi_channel": 0.015,
}

PLATFORM_FEE: dict[str, float] = {
    "dtc_website": 0.00,
    "amazon": 0.15,
    "etsy": 0.065,
    "multi_channel": 0.08,
}

SHIPPING_BAND: dict[str, float] = {"very_low": 4, "normal": 8, "high": 15}

REPEAT_PURCHASE: dict[str, tuple[float, float]] = {
    "none":   (0.00, 1.5),
    "low":    (0.10, 1.5),
    "medium": (0.25, 2.5),
    "high":   (0.40, 4.0),
}

RETENTION_IMPROVEMENT: dict[str, float] = {
    "conservative": 0.03,
    "base": 0.05,
    "aggressive": 0.08,
}

COGS_IMPROVEMENT: dict[str, float] = {
    "conservative": 0.005,
    "base": 0.01,
    "aggressive": 0.02,
}

CPC_INFLATION: dict[str, float] = {
    "conservative": 0.075,
    "base": 0.10,
    "aggressive": 0.125,
}

TRAFFIC_GROWTH: dict[str, float] = {
    "conservative": 0.10,
    "base": 0.225,
    "aggressive": 0.45,
}

HEADCOUNT: dict[str, float] = {"0_1": 0.5, "2_3": 2.5, "4_7": 5.5, "8_plus": 10.0}

SALARY: dict[str, float] = {"low": 40000, "mid": 65000, "high": 100000}

MONTHS_TO_FULL_TEAM: dict[str, int] = {"0_1": 0, "2_3": 3, "4_7": 6, "8_plus": 9}

MONTHLY_SAAS: dict[str, float] = {
    "dtc_website": 200,
    "amazon": 100,
    "etsy": 100,
    "multi_channel": 250,
}

OVERHEAD_INFLATION: dict[str, float] = {"flat": 0.00, "3_5": 0.04, "5_10": 0.075}

AR_DAYS: dict[str, float] = {"upfront": 0, "mostly_upfront": 3, "invoice": 30}

AP_DAYS: dict[str, float] = {"15_days": 15, "30_days": 30, "45_60_days": 52.5}

INVENTORY_DAYS: dict[str, float] = {"no_stock": 0, "1_2_months": 45, "3_plus_months": 120}

INVENTORY_IMPROVEMENT: dict[str, float] = {
    "no_stock": 0.00,
    "1_2_months": 0.05,
    "3_plus_months": 0.08,
}

CAPEX_PCT: dict[str, float] = {
    "profit_first": 0.01,
    "balanced": 0.02,
    "growth_first": 0.035,
}

LOAN_INTEREST_BAND: dict[str, float] = {"5_8": 0.065, "8_12": 0.10, "gt_12": 0.14}

EQUITY_RUNWAY: dict[str, int] = {"conservative": 6, "base": 9, "aggressive": 12}

TAX_REGION_MAP: dict[str, str] = {
    "US": "US",
    "UK": "UK",
    "EU": "EU",
    "Canada": "CA",
    "Australia": "AU",
    "Other": "other",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dicts."""
    current = data
    for k in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(k, default)
        if current is None:
            return default
    return current


def calc_handling(fulfillment: str, ship_cost: float) -> float:
    """Calculate handling cost per order based on fulfillment mode and shipping cost."""
    if fulfillment == "self_fulfill":
        return max(1.00, 0.10 * ship_cost)
    if fulfillment == "third_party_fulfillment":
        return max(1.50, 0.30 * ship_cost)
    # dropship_pod
    return max(1.50, 0.05 * ship_cost)


def _round_pct(value: float, decimals: int = 4) -> float:
    """Round a percentage/float to avoid floating-point noise."""
    return round(value, decimals)


def _round_currency(value: float, decimals: int = 2) -> float:
    """Round a currency amount."""
    return round(value, decimals)


def _entry(
    input_id: str,
    value: Any,
    source: str,
    confidence: float,
    notes: str,
) -> dict[str, Any]:
    """Build a single driver output entry."""
    return {
        "input_id": input_id,
        "value": value,
        "source": source,
        "confidence": confidence,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Channel mix algorithm
# ---------------------------------------------------------------------------

def derive_channel_mix(
    financial_priority: str,
    primary_channels: list[str],
) -> dict[str, float]:
    """Derive the traffic channel mix from priority and selected channels.

    Returns a dict with keys ``paid``, ``organic``, ``retention`` summing to 1.0.
    """
    base = dict(MIX_BASE[financial_priority])  # copy

    has_paid = "paid_ads" in primary_channels
    has_organic = "organic_direct" in primary_channels
    has_retention = "retention_email_sms" in primary_channels

    # Step 2: if paid_ads not selected, zero it out
    if not has_paid:
        base["paid"] = 0.0

    # Step 3: boost selected channels
    if has_paid:
        base["paid"] *= 1.1
    if has_organic:
        base["organic"] *= 1.2
    if has_retention:
        base["retention"] *= 1.3

    # Step 4: floor unselected (organic min 10%, retention min 5%)
    if not has_organic:
        base["organic"] = max(0.10, base["organic"] * 0.6)
    if not has_retention:
        base["retention"] = max(0.05, base["retention"] * 0.5)

    # Step 5: if no paid at all, override
    if not has_paid:
        base["organic"] = 0.60
        base["retention"] = 0.40
        base["paid"] = 0.0

    # Step 6: normalize to 1.0
    total = base["paid"] + base["organic"] + base["retention"]
    if total > 0:
        base["paid"] /= total
        base["organic"] /= total
        base["retention"] /= total

    # Round to 4 decimal places
    base["paid"] = _round_pct(base["paid"])
    base["organic"] = _round_pct(base["organic"])
    base["retention"] = _round_pct(base["retention"])

    # Ensure exact sum = 1.0 by adjusting the largest component
    remainder = _round_pct(1.0 - base["paid"] - base["organic"] - base["retention"])
    if remainder != 0:
        largest = max(base, key=lambda k: base[k])
        base[largest] = _round_pct(base[largest] + remainder)

    return base


# ---------------------------------------------------------------------------
# Fulfillment mode resolution
# ---------------------------------------------------------------------------

def resolve_fulfillment(
    current_mode: str,
    inventory_intensity: str,
    growth_ambition: str,
    orders_bucket: str,
) -> str:
    """Resolve ``not_sure`` fulfillment mode to a concrete value."""
    if current_mode != "not_sure":
        return current_mode

    if inventory_intensity == "no_stock":
        return "dropship_pod"
    if inventory_intensity == "3_plus_months":
        return "third_party_fulfillment"
    if growth_ambition == "aggressive" and orders_bucket in ("5_20k", "gt_20k"):
        return "third_party_fulfillment"
    return "self_fulfill"


# ---------------------------------------------------------------------------
# Rent start year logic
# ---------------------------------------------------------------------------

def resolve_rent_start_year(
    rent_amount: float,
    growth_ambition: str,
    inventory_intensity: str,
) -> int:
    """Determine the rent start year based on amount, ambition, and inventory."""
    if rent_amount == 0:
        return 2026

    if growth_ambition == "conservative":
        year = 2028
    elif growth_ambition == "aggressive" and inventory_intensity == "3_plus_months":
        year = 2027
    elif growth_ambition == "aggressive":
        year = 2026
    elif growth_ambition == "base":
        year = 2027
    else:
        year = 2026

    return min(year, 2031)


# ---------------------------------------------------------------------------
# Core resolution pipeline
# ---------------------------------------------------------------------------

def resolve(intake: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Run the full assumptions resolution pipeline.

    Parameters
    ----------
    intake : dict
        Parsed founder intake JSON.
    output_dir : Path
        Directory for reading auxiliary data (not used directly here; data
        files are located relative to ``SCRIPT_DIR``).

    Returns
    -------
    dict
        Resolved assumptions JSON with ``inputs`` and ``__internal_targets``.
    """

    # ------------------------------------------------------------------
    # Step 1: Extract intake fields
    # ------------------------------------------------------------------
    bp = intake.get("business_profile", {})
    strategy = intake.get("strategy", {})
    demand = intake.get("demand", {})
    pricing = intake.get("pricing", {})
    acquisition = intake.get("acquisition", {})
    unit_econ = intake.get("unit_economics", {})
    team_oh = intake.get("team_overhead", {})
    working_cap = intake.get("working_capital", {})
    funding = intake.get("funding_tax", {})

    raw_category = bp.get("category", "other")
    data_category = CATEGORY_MAP.get(raw_category, "other")
    customer_region = bp.get("customer_region", "US")
    tax_country = bp.get("tax_country", customer_region)
    financial_priority = strategy.get("financial_priority", "balanced")
    growth_ambition = strategy.get("growth_ambition", "base")
    orders_bucket = demand.get("year1_orders_bucket", "1_5k")
    repeat_expectation = demand.get("repeat_expectation", "low")
    aov_mode = pricing.get("aov_mode", "band")
    aov_explicit = pricing.get("aov_year1")
    aov_band_key = pricing.get("aov_band", "30_80")
    primary_channels = acquisition.get("primary_channels", [])
    conv_difficulty = acquisition.get("conv_difficulty", "average")
    cac_mode = acquisition.get("cac_mode", "band")
    cac_band_key = acquisition.get("cac_band")
    cac_explicit = acquisition.get("cac_explicit")
    gm_mode = unit_econ.get("gross_margin_mode", "band")
    gm_explicit = unit_econ.get("gross_margin_target_pct")
    gm_band_key = unit_econ.get("gross_margin_band", "medium")
    ship_mode = unit_econ.get("shipping_cost_mode", "band")
    ship_explicit = unit_econ.get("shipping_plus_packaging_per_order")
    ship_band_key = unit_econ.get("shipping_cost_band", "normal")
    sales_platform = unit_econ.get("sales_platform", "dtc_website")
    fulfilment_raw = unit_econ.get("fulfilment_mode_year1", "not_sure")
    inventory_intensity = working_cap.get("inventory_intensity", "1_2_months")
    team_cost_mode = team_oh.get("team_cost_mode", "estimate")
    team_cost_explicit = team_oh.get("team_cost_year1")
    team_size_bucket = team_oh.get("team_size_bucket", "2_3")
    salary_level = team_oh.get("salary_level", "mid")
    fixed_mode = team_oh.get("other_fixed_costs_mode", "band")
    fixed_explicit = team_oh.get("other_fixed_costs_year1")
    fixed_band_key = team_oh.get("other_fixed_costs_band", "moderate")
    overhead_band_key = team_oh.get("overhead_inflation_band", "3_5")
    customer_terms = working_cap.get("customer_payment_terms", "upfront")
    supplier_terms = working_cap.get("supplier_payment_terms", "30_days")
    equity_mode = funding.get("equity_mode", "suggest")
    equity_explicit = funding.get("equity_injection")
    loan_plan = funding.get("loan_plan", "none")
    loan_amount_raw = funding.get("loan_amount")
    loan_interest_mode = funding.get("loan_interest_mode")
    loan_interest_band_key = funding.get("loan_interest_band")
    loan_interest_explicit = funding.get("loan_interest_pct")
    loan_term_raw = funding.get("loan_term_years")
    tax_mode = funding.get("tax_rate_mode", "typical")
    tax_explicit = funding.get("tax_rate_pct")

    # ------------------------------------------------------------------
    # Step 2: Load benchmark data
    # ------------------------------------------------------------------
    cat_file = DATA_DIR / f"{data_category}.json"
    if not cat_file.exists():
        logger.warning(
            "Category benchmark file not found: %s — falling back to 'other'",
            cat_file,
        )
        data_category_file = "other"
        cat_file = DATA_DIR / "other.json"
    else:
        data_category_file = data_category

    try:
        benchmarks = load_json(cat_file)
    except Exception as exc:
        logger.error("Failed to load category benchmarks from %s: %s", cat_file, exc)
        sys.exit(2)

    try:
        regional = load_json(REGIONAL_DEFAULTS_PATH)
    except Exception as exc:
        logger.error("Failed to load regional defaults: %s", exc)
        sys.exit(2)

    # ------------------------------------------------------------------
    # Step 3: Internal targets
    # ------------------------------------------------------------------

    # 3a — Year-1 orders
    orders_target: int = ORDERS_MAP.get(orders_bucket, ORDERS_MAP["1_5k"])[growth_ambition]
    logger.debug("Year-1 orders target: %d (bucket=%s, ambition=%s)", orders_target, orders_bucket, growth_ambition)

    # 3b — Gross margin
    if gm_mode == "explicit" and gm_explicit is not None:
        gross_margin_target = float(gm_explicit)
        gm_source = "user_explicit"
    else:
        gross_margin_target = GROSS_MARGIN_BAND.get(gm_band_key, 0.50)
        gm_source = "user_band_inferred"
    logger.debug("Gross margin target: %.2f (source=%s)", gross_margin_target, gm_source)

    # 3c — Fulfillment mode
    fulfilment_resolved = resolve_fulfillment(
        fulfilment_raw, inventory_intensity, growth_ambition, orders_bucket,
    )
    logger.debug("Fulfillment resolved: %s (raw=%s)", fulfilment_resolved, fulfilment_raw)

    # 3d — CAC paid target
    if cac_mode == "explicit" and cac_explicit is not None:
        cac_paid_target = float(cac_explicit)
        cac_source = "user_explicit"
    elif cac_mode == "band" and cac_band_key:
        cac_paid_target = CAC_BAND.get(cac_band_key, 20.00)
        cac_source = "user_band_inferred"
    else:
        # Fall back to category benchmark
        cac_paid_target = float(
            _get(benchmarks, "benchmarks", "cac_paid", "value", default=20.00)
        )
        cac_source = "category_benchmark"
    logger.debug("CAC paid target: %.2f (source=%s)", cac_paid_target, cac_source)

    # 3e — Fixed costs total
    if fixed_mode == "explicit" and fixed_explicit is not None:
        fixed_costs_total = float(fixed_explicit)
        fixed_source = "user_explicit"
    else:
        fixed_costs_total = FIXED_COSTS_BAND.get(fixed_band_key, 18000)
        fixed_source = "user_band_inferred"
    logger.debug("Fixed costs total: %.0f (source=%s)", fixed_costs_total, fixed_source)

    # ------------------------------------------------------------------
    # Step 4: Conversion rates
    # ------------------------------------------------------------------
    conv = CONV_MAP.get(conv_difficulty, CONV_MAP["average"])
    conv_paid = conv["paid"]
    conv_organic = conv["organic"]
    conv_retention = conv["retention"]

    # ------------------------------------------------------------------
    # Step 5: Channel mix
    # ------------------------------------------------------------------
    mix = derive_channel_mix(financial_priority, primary_channels)
    mix_paid = mix["paid"]
    mix_organic = mix["organic"]
    mix_retention = mix["retention"]
    logger.debug(
        "Channel mix: paid=%.4f organic=%.4f retention=%.4f",
        mix_paid, mix_organic, mix_retention,
    )

    # ------------------------------------------------------------------
    # Step 6: Traffic
    # ------------------------------------------------------------------
    weighted_conv = (
        mix_paid * conv_paid
        + mix_organic * conv_organic
        + mix_retention * conv_retention
    )
    if weighted_conv <= 0:
        logger.error("Weighted conversion is zero — cannot compute traffic.")
        sys.exit(1)
    traffic_total = round(orders_target / weighted_conv)
    logger.debug("Traffic total: %d (weighted_conv=%.6f)", traffic_total, weighted_conv)

    # ------------------------------------------------------------------
    # Step 7: Order economics
    # ------------------------------------------------------------------

    # AOV
    if aov_mode == "explicit" and aov_explicit is not None:
        aov_year1 = float(aov_explicit)
        aov_source = "user_explicit"
    else:
        aov_year1 = AOV_BAND.get(aov_band_key, 55)
        aov_source = "user_band_inferred"

    # COGS
    cogs_pct = _round_pct(1.0 - gross_margin_target)

    # Discount
    discounts_pct = DISCOUNT_MAP.get(financial_priority, 0.175)

    # Return rate
    return_rate = RETURN_RATES.get(data_category, 0.10)

    # Payment processing & platform fee
    payment_processing = PAYMENT_PROCESSING.get(sales_platform, 0.029)
    platform_fee = PLATFORM_FEE.get(sales_platform, 0.00)

    # Shipping
    if ship_mode == "explicit" and ship_explicit is not None:
        ship_cost = float(ship_explicit)
        ship_source = "user_explicit"
    else:
        ship_cost = SHIPPING_BAND.get(ship_band_key, 8)
        ship_source = "user_band_inferred"

    # Handling
    handling_cost = _round_currency(calc_handling(fulfilment_resolved, ship_cost))

    # Repeat purchase
    rp_rate, rp_freq = REPEAT_PURCHASE.get(repeat_expectation, (0.10, 1.5))

    # Retention improvement
    retention_improvement = RETENTION_IMPROVEMENT.get(growth_ambition, 0.05)
    if rp_rate == 0:
        retention_improvement = 0.0

    # COGS improvement
    cogs_improvement = COGS_IMPROVEMENT.get(growth_ambition, 0.01)

    # Packaging
    packaging_cost = 2.00 if financial_priority in ("balanced", "growth_first") else 1.00

    # Support
    support_cost = 2.50 if sales_platform in ("multi_channel", "amazon") else 2.00

    # ------------------------------------------------------------------
    # Step 8: Marketing
    # ------------------------------------------------------------------
    cpc_year1 = _round_currency(cac_paid_target * conv_paid)
    cpc_inflation = CPC_INFLATION.get(growth_ambition, 0.10)
    traffic_growth = TRAFFIC_GROWTH.get(growth_ambition, 0.225)

    # ------------------------------------------------------------------
    # Step 9: G&A
    # ------------------------------------------------------------------

    # Salary multiplier from regional defaults
    region_key = TAX_REGION_MAP.get(customer_region, "other")
    region_data = _get(regional, "regions", region_key, default={})
    salary_multiplier = float(
        _get(region_data, "salary_multiplier", "value", default=1.0)
    )

    # Team cost
    if team_cost_mode == "explicit" and team_cost_explicit is not None:
        salaries_year1 = float(team_cost_explicit)
        salary_source = "user_explicit"
    else:
        headcount = HEADCOUNT.get(team_size_bucket, 2.5)
        base_salary = SALARY.get(salary_level, 65000)
        salaries_year1 = _round_currency(headcount * base_salary * salary_multiplier * 1.25)
        salary_source = "research_estimate"
    logger.debug("Salaries year 1: %.0f (source=%s)", salaries_year1, salary_source)

    months_to_full = MONTHS_TO_FULL_TEAM.get(team_size_bucket, 3)

    # Monthly SaaS
    monthly_saas = MONTHLY_SAAS.get(sales_platform, 200)

    # Fixed overhead allocation
    prof_fees = _round_currency(fixed_costs_total * 0.40)
    misc_ga = _round_currency(fixed_costs_total * 0.60 - (monthly_saas * 12))
    if misc_ga < 0:
        misc_ga = 0.0

    # Overhead inflation (sal_prof_inflation)
    sal_prof_inflation = OVERHEAD_INFLATION.get(overhead_band_key, 0.04)

    # Warehouse rent
    if fulfilment_resolved in ("dropship_pod", "third_party_fulfillment"):
        warehouse_rent = 0.0
    elif fulfilment_resolved == "self_fulfill":
        warehouse_rent = 0.0  # early-stage self-fulfill — home based
    else:
        warehouse_rent = 0.0

    # Office rent — home-based startup default
    office_rent = 0.0

    # Rent start years
    warehouse_rent_start = resolve_rent_start_year(
        warehouse_rent, growth_ambition, inventory_intensity,
    )
    office_rent_start = resolve_rent_start_year(
        office_rent, growth_ambition, inventory_intensity,
    )

    # Inflation defaults
    rent_inflation = 0.03
    ship_inflation = 0.05
    aov_inflation = 0.025

    # ------------------------------------------------------------------
    # Step 10: Working capital
    # ------------------------------------------------------------------
    ar_days = AR_DAYS.get(customer_terms, 0)
    ap_days = AP_DAYS.get(supplier_terms, 30)
    inv_days = INVENTORY_DAYS.get(inventory_intensity, 45)
    inv_improvement = INVENTORY_IMPROVEMENT.get(inventory_intensity, 0.05)

    # ------------------------------------------------------------------
    # Step 11: Capex & depreciation
    # ------------------------------------------------------------------
    capex_pct = CAPEX_PCT.get(financial_priority, 0.02)
    if capex_pct < 0.015:
        dep_period = 3
    elif capex_pct > 0.035:
        dep_period = 5
    else:
        dep_period = 4

    # ------------------------------------------------------------------
    # Step 12: Financing
    # ------------------------------------------------------------------

    # Loan
    if loan_plan == "none":
        loan_amount = 0.0
        interest_rate = 0.0
        loan_term = 5
    else:
        loan_amount = float(loan_amount_raw) if loan_amount_raw is not None else 0.0
        # Interest rate
        if loan_interest_mode == "explicit" and loan_interest_explicit is not None:
            interest_rate = float(loan_interest_explicit)
        elif loan_interest_mode == "band" and loan_interest_band_key:
            interest_rate = LOAN_INTEREST_BAND.get(loan_interest_band_key, 0.10)
        else:
            interest_rate = 0.10  # default
        # Loan term
        loan_term = int(loan_term_raw) if loan_term_raw is not None else 5

    # Tax
    if tax_mode == "explicit" and tax_explicit is not None:
        tax_rate = float(tax_explicit)
        tax_source = "user_explicit"
    else:
        tax_region_key = TAX_REGION_MAP.get(tax_country, "other")
        tax_region_data = _get(regional, "regions", tax_region_key, default={})
        tax_rate = float(
            _get(tax_region_data, "effective_tax_rate", "value", default=0.25)
        )
        tax_source = "category_benchmark"

    # Equity
    equity_calc: dict[str, Any] | None = None
    if equity_mode == "explicit" and equity_explicit is not None:
        equity_injection = float(equity_explicit)
        equity_source = "user_explicit"
    else:
        # Suggest equity
        annual_fixed = salaries_year1 + prof_fees + misc_ga + (monthly_saas * 12)
        est_marketing = traffic_total * mix_paid * cpc_year1
        est_fulfillment = orders_target * (ship_cost + handling_cost)
        annual_variable = est_marketing + est_fulfillment
        effective_annual = annual_fixed + annual_variable * 0.6
        monthly_burn = effective_annual / 12
        runway = EQUITY_RUNWAY.get(growth_ambition, 9)
        equity_needed = monthly_burn * runway * 1.15 - loan_amount
        equity_injection = max(5000, round(equity_needed / 1000) * 1000)
        equity_source = "research_estimate"

        equity_calc = {
            "annual_fixed": _round_currency(annual_fixed),
            "annual_variable": _round_currency(annual_variable),
            "effective_annual_burn": _round_currency(effective_annual),
            "monthly_burn": _round_currency(monthly_burn),
            "runway_months": runway,
            "buffer_multiplier": 1.15,
            "loan_offset": _round_currency(loan_amount),
            "initial_estimate": _round_currency(equity_injection),
        }
        logger.debug("Equity suggestion: %s", equity_calc)

    # ------------------------------------------------------------------
    # Build output entries
    # ------------------------------------------------------------------
    inputs: list[dict[str, Any]] = []

    # --- Traffic ---
    inputs.append(_entry(
        "traffic_total_year1", traffic_total,
        "research_estimate", 0.8,
        f"Derived: {orders_target} orders / {weighted_conv:.6f} weighted conv",
    ))
    inputs.append(_entry(
        "traffic_yoy_growth", traffic_growth,
        "research_estimate", 0.7,
        f"Mapped from growth_ambition={growth_ambition}",
    ))
    inputs.append(_entry(
        "traffic_mix_paid_pct", mix_paid,
        "research_estimate", 0.75,
        f"Channel mix for priority={financial_priority}, channels={primary_channels}",
    ))
    inputs.append(_entry(
        "traffic_mix_organic_pct", mix_organic,
        "research_estimate", 0.75,
        f"Channel mix for priority={financial_priority}, channels={primary_channels}",
    ))
    inputs.append(_entry(
        "traffic_mix_retention_pct", mix_retention,
        "research_estimate", 0.75,
        f"Channel mix for priority={financial_priority}, channels={primary_channels}",
    ))

    # --- Conversion ---
    inputs.append(_entry(
        "conv_paid", conv_paid,
        "user_band_inferred", 0.8,
        f"Mapped from conv_difficulty={conv_difficulty}",
    ))
    inputs.append(_entry(
        "conv_organic", conv_organic,
        "user_band_inferred", 0.8,
        f"Mapped from conv_difficulty={conv_difficulty}",
    ))
    inputs.append(_entry(
        "conv_retention", conv_retention,
        "user_band_inferred", 0.8,
        f"Mapped from conv_difficulty={conv_difficulty}",
    ))

    # --- Demand (repeat purchase) ---
    inputs.append(_entry(
        "repeat_purchase_rate_year1", rp_rate,
        "user_band_inferred", 0.75,
        f"Mapped from repeat_expectation={repeat_expectation}",
    ))
    inputs.append(_entry(
        "repeat_purchase_frequency", rp_freq,
        "user_band_inferred", 0.7,
        f"Mapped from repeat_expectation={repeat_expectation}",
    ))
    inputs.append(_entry(
        "retention_improvement_annual", retention_improvement,
        "research_estimate", 0.7,
        f"Mapped from growth_ambition={growth_ambition}" + (" (zeroed: no repeat)" if rp_rate == 0 else ""),
    ))

    # --- Order Economics ---
    inputs.append(_entry(
        "aov_year1", aov_year1,
        aov_source, 0.8 if aov_source == "user_explicit" else 0.7,
        f"{'Explicit input' if aov_source == 'user_explicit' else f'Mapped from aov_band={aov_band_key}'}",
    ))
    inputs.append(_entry(
        "aov_inflation", aov_inflation,
        "research_estimate", 0.7,
        "Default AOV inflation 2.5%",
    ))
    inputs.append(_entry(
        "cogs_pct", cogs_pct,
        gm_source, 0.8,
        f"Derived: 1.0 - gross_margin_target ({gross_margin_target})",
    ))
    inputs.append(_entry(
        "cogs_annual_improvement_pct", cogs_improvement,
        "research_estimate", 0.7,
        f"Mapped from growth_ambition={growth_ambition}",
    ))
    inputs.append(_entry(
        "discounts_promos_pct", discounts_pct,
        "research_estimate", 0.65,
        f"Mapped from financial_priority={financial_priority}",
    ))
    inputs.append(_entry(
        "return_rate_pct", return_rate,
        "category_benchmark", 0.75,
        f"Category default for {data_category}",
    ))
    inputs.append(_entry(
        "payment_processing_pct", payment_processing,
        "research_estimate", 0.9,
        f"Mapped from sales_platform={sales_platform}",
    ))
    inputs.append(_entry(
        "platform_fee_pct", platform_fee,
        "research_estimate", 0.9,
        f"Mapped from sales_platform={sales_platform}",
    ))

    # --- Marketing ---
    inputs.append(_entry(
        "cpc_year1", cpc_year1,
        "research_estimate", 0.7,
        f"Derived: CAC ({cac_paid_target}) x conv_paid ({conv_paid})",
    ))
    inputs.append(_entry(
        "cpc_inflation", cpc_inflation,
        "research_estimate", 0.65,
        f"Mapped from growth_ambition={growth_ambition}",
    ))

    # --- Fulfilment Variable ---
    inputs.append(_entry(
        "ship_cost_year1", ship_cost,
        ship_source, 0.8 if ship_source == "user_explicit" else 0.7,
        f"{'Explicit input' if ship_source == 'user_explicit' else f'Mapped from shipping_cost_band={ship_band_key}'}",
    ))
    inputs.append(_entry(
        "ship_inflation", ship_inflation,
        "research_estimate", 0.7,
        "Default shipping inflation 5%",
    ))
    inputs.append(_entry(
        "handling_cost_year1", handling_cost,
        "research_estimate", 0.7,
        f"Derived from fulfillment={fulfilment_resolved}, ship_cost={ship_cost}",
    ))
    inputs.append(_entry(
        "packaging_cost_per_order", packaging_cost,
        "research_estimate", 0.65,
        f"Mapped from financial_priority={financial_priority}",
    ))
    inputs.append(_entry(
        "support_cost_per_order", support_cost,
        "research_estimate", 0.65,
        f"Mapped from sales_platform={sales_platform}",
    ))
    inputs.append(_entry(
        "warehouse_rent_amount_when_active", warehouse_rent,
        "research_estimate", 0.7,
        f"Fulfillment={fulfilment_resolved} — early stage, no dedicated warehouse",
    ))
    inputs.append(_entry(
        "warehouse_rent_start_year", warehouse_rent_start,
        "research_estimate", 0.7,
        f"Rent={warehouse_rent}, ambition={growth_ambition}",
    ))
    inputs.append(_entry(
        "warehouse_rent_inflation", rent_inflation,
        "research_estimate", 0.7,
        "Default rent inflation 3%",
    ))

    # --- G&A Fixed ---
    inputs.append(_entry(
        "office_rent_amount_when_active", office_rent,
        "research_estimate", 0.7,
        "Home-based startup default",
    ))
    inputs.append(_entry(
        "office_rent_start_year", office_rent_start,
        "research_estimate", 0.7,
        f"Rent={office_rent}, ambition={growth_ambition}",
    ))
    inputs.append(_entry(
        "office_rent_inflation", rent_inflation,
        "research_estimate", 0.7,
        "Default rent inflation 3%",
    ))
    inputs.append(_entry(
        "salaries_year1", salaries_year1,
        salary_source, 0.8 if salary_source == "user_explicit" else 0.7,
        f"{'Explicit input' if salary_source == 'user_explicit' else f'Headcount={HEADCOUNT.get(team_size_bucket)}, salary={SALARY.get(salary_level)}, multiplier={salary_multiplier}, burden=1.25'}",
    ))
    inputs.append(_entry(
        "months_to_full_team", months_to_full,
        "research_estimate", 0.8,
        f"Mapped from team_size_bucket={team_size_bucket}",
    ))
    inputs.append(_entry(
        "prof_fees_year1", prof_fees,
        fixed_source, 0.7,
        f"40% of fixed_costs_total ({fixed_costs_total})",
    ))
    inputs.append(_entry(
        "sal_prof_inflation", sal_prof_inflation,
        "user_band_inferred", 0.7,
        f"Mapped from overhead_inflation_band={overhead_band_key}",
    ))
    inputs.append(_entry(
        "misc_ga_year1", misc_ga,
        fixed_source, 0.7,
        f"60% of fixed_costs_total ({fixed_costs_total}) minus SaaS ({monthly_saas}x12)",
    ))
    inputs.append(_entry(
        "monthly_saas_costs", monthly_saas,
        "research_estimate", 0.75,
        f"Mapped from sales_platform={sales_platform}",
    ))

    # --- Working Capital ---
    inputs.append(_entry(
        "ar_days", ar_days,
        "user_band_inferred", 0.85,
        f"Mapped from customer_payment_terms={customer_terms}",
    ))
    inputs.append(_entry(
        "inventory_days_year1", inv_days,
        "user_band_inferred", 0.75,
        f"Mapped from inventory_intensity={inventory_intensity}",
    ))
    inputs.append(_entry(
        "inventory_turns_improvement", inv_improvement,
        "research_estimate", 0.65,
        f"Mapped from inventory_intensity={inventory_intensity}",
    ))
    inputs.append(_entry(
        "ap_days", ap_days,
        "user_band_inferred", 0.85,
        f"Mapped from supplier_payment_terms={supplier_terms}",
    ))

    # --- Capex & Depreciation ---
    inputs.append(_entry(
        "capex_pct_of_net_rev", capex_pct,
        "research_estimate", 0.7,
        f"Mapped from financial_priority={financial_priority}",
    ))
    inputs.append(_entry(
        "dep_period_years", dep_period,
        "research_estimate", 0.7,
        f"Derived from capex_pct={capex_pct}",
    ))

    # --- Financing ---
    inputs.append(_entry(
        "initial_loan_amount", loan_amount,
        "user_explicit" if loan_plan != "none" else "research_estimate", 0.9,
        f"Loan plan={loan_plan}" + (f", amount={loan_amount}" if loan_plan != "none" else ", no loan"),
    ))
    inputs.append(_entry(
        "loan_start_year", 2026,
        "research_estimate", 1.0,
        "Always 2026 (hardcoded in template, not written to Excel)",
    ))
    inputs.append(_entry(
        "interest_rate", interest_rate,
        ("user_explicit" if loan_interest_mode == "explicit" and loan_interest_explicit is not None
         else "user_band_inferred" if loan_interest_mode == "band"
         else "research_estimate"),
        0.85,
        f"Loan interest — mode={loan_interest_mode}" + (f", band={loan_interest_band_key}" if loan_interest_mode == "band" else ""),
    ))
    inputs.append(_entry(
        "loan_term_years", loan_term,
        "user_explicit" if loan_term_raw is not None else "research_estimate",
        0.85,
        f"Loan term={loan_term} years" + (" (default)" if loan_term_raw is None else ""),
    ))
    inputs.append(_entry(
        "initial_equity_injection", equity_injection,
        equity_source, 0.7 if equity_source == "research_estimate" else 0.9,
        f"Equity mode={equity_mode}" + (f", suggested={equity_injection}" if equity_mode == "suggest" else ""),
    ))

    # --- Tax ---
    inputs.append(_entry(
        "tax_rate", tax_rate,
        tax_source, 0.85,
        f"{'Explicit input' if tax_source == 'user_explicit' else f'Regional default for {tax_country}'}",
    ))

    # ------------------------------------------------------------------
    # Step 13: Validation
    # ------------------------------------------------------------------
    warnings = validate_drivers(inputs)
    for w in warnings:
        logger.warning(w)

    # Verify traffic mix sums to 1.0
    mix_sum = mix_paid + mix_organic + mix_retention
    if abs(mix_sum - 1.0) > 0.01:
        logger.warning("Traffic mix does not sum to 1.0: %.4f", mix_sum)

    # Verify conversion hierarchy
    if not (conv_retention >= conv_organic >= conv_paid):
        logger.warning(
            "Conversion hierarchy violated: retention=%.4f, organic=%.4f, paid=%.4f",
            conv_retention, conv_organic, conv_paid,
        )

    # ------------------------------------------------------------------
    # Step 14: Assemble output
    # ------------------------------------------------------------------
    internal_targets: dict[str, Any] = {
        "total_orders_year1_target": orders_target,
        "gross_margin_target_pct": gross_margin_target,
        "fulfilment_mode_year1_resolved": fulfilment_resolved,
        "cac_paid_target": cac_paid_target,
        "other_fixed_costs_year1_total": fixed_costs_total,
    }

    internal_targets["equity_mode"] = equity_mode
    if equity_mode == "suggest" and equity_calc is not None:
        internal_targets["equity_calc"] = equity_calc

    result = {
        "inputs": inputs,
        "__internal_targets": internal_targets,
    }

    return result


# ---------------------------------------------------------------------------
# Validation against driver catalog
# ---------------------------------------------------------------------------

def validate_drivers(inputs: list[dict[str, Any]]) -> list[str]:
    """Validate driver values against bounds in driver_catalog.jsonc.

    Returns a list of warning strings (empty if everything passes).
    """
    warnings: list[str] = []

    try:
        catalog = load_jsonc(DRIVER_CATALOG_PATH)
    except Exception as exc:
        warnings.append(f"Could not load driver catalog for validation: {exc}")
        return warnings

    catalog_entries = catalog.get("inputs", [])
    catalog_map: dict[str, dict[str, Any]] = {
        entry["input_id"]: entry for entry in catalog_entries
    }

    for driver in inputs:
        input_id = driver["input_id"]
        value = driver["value"]
        spec = catalog_map.get(input_id)

        if spec is None:
            warnings.append(f"Driver '{input_id}' not found in catalog")
            continue

        dtype = spec.get("type", "float")
        min_val = spec.get("min_value")
        max_val = spec.get("max_value")

        # Type coercion check
        if dtype == "int":
            if not isinstance(value, int):
                try:
                    # Allow float that is a whole number
                    if isinstance(value, float) and value == int(value):
                        pass  # acceptable
                    else:
                        warnings.append(
                            f"Driver '{input_id}' expected int, got {type(value).__name__}: {value}"
                        )
                except (ValueError, OverflowError):
                    warnings.append(
                        f"Driver '{input_id}' expected int, got {type(value).__name__}: {value}"
                    )

        if dtype == "year":
            if isinstance(value, (int, float)):
                if value < 2026 or value > 2031:
                    warnings.append(
                        f"Driver '{input_id}' year {value} outside 2026-2031"
                    )

        # Bounds check
        if min_val is not None and isinstance(value, (int, float)):
            if value < min_val:
                warnings.append(
                    f"Driver '{input_id}' value {value} below min {min_val}"
                )
        if max_val is not None and isinstance(value, (int, float)):
            if value > max_val:
                warnings.append(
                    f"Driver '{input_id}' value {value} above max {max_val}"
                )

    return warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Resolve financial model assumptions from founder intake JSON.",
    )
    parser.add_argument(
        "store_name",
        help="Store name — used to locate {StoreName}_intake.json and write {StoreName}_assumptions.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for input/output files (default: current working directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args()

    # Logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    output_dir = args.output_dir if args.output_dir else Path.cwd()
    output_dir = output_dir.resolve()

    store_name: str = args.store_name
    intake_path = output_dir / f"{store_name}_intake.json"
    assumptions_path = output_dir / f"{store_name}_assumptions.json"

    # ------------------------------------------------------------------
    # Load intake
    # ------------------------------------------------------------------
    if not intake_path.exists():
        logger.error("Intake file not found: %s", intake_path)
        sys.exit(2)

    try:
        intake = load_json(intake_path)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in intake file %s: %s", intake_path, exc)
        sys.exit(2)
    except OSError as exc:
        logger.error("Cannot read intake file %s: %s", intake_path, exc)
        sys.exit(2)

    logger.info("Loaded intake from %s", intake_path)

    # ------------------------------------------------------------------
    # Resolve
    # ------------------------------------------------------------------
    result = resolve(intake, output_dir)

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------
    try:
        assumptions_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        logger.error("Cannot write assumptions file %s: %s", assumptions_path, exc)
        sys.exit(2)

    driver_count = len(result["inputs"])
    logger.info(
        "Wrote %d drivers to %s",
        driver_count,
        assumptions_path,
    )

    # Exit code 1 if validation warnings were emitted
    warnings = validate_drivers(result["inputs"])
    if warnings:
        logger.warning("%d validation warning(s) — review output", len(warnings))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
