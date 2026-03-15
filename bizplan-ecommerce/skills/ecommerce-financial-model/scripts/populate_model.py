#!/usr/bin/env python3
"""
Populate an eCommerce Excel financial model template with resolved assumptions.

Writes driver values via direct XML editing (preserving charts and formatting),
evaluates formulas with xlcalculator, runs equity optimization when requested,
and extracts model outputs to JSON.

Usage:
    python populate_model.py {StoreName} [--output-dir DIR] [--verbose]

Reads:  {StoreName}_assumptions.json  (from CWD or --output-dir)
Writes: {StoreName}_Financial_Model.xlsx
        {StoreName}_model_outputs.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Paths relative to this script
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_MAP_PATH = SCRIPT_DIR / "../references/input_map.jsonc"
OUTPUT_MAP_PATH = SCRIPT_DIR / "../references/output_map.jsonc"
TEMPLATE_PATH = SCRIPT_DIR / "../templates/eCommerce Model v1.xlsx"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXCLUDED_IDS: set[str] = {"loan_start_year"}
MAX_EQUITY_ITERATIONS = 5
CASH_BUFFER = 1000
EQUITY_MULTIPLIER = 1.15
BALANCE_TOLERANCE = 0.01

YEAR_KEYS = ["year_1", "year_2", "year_3", "year_4", "year_5", "year_6"]
YEAR_NUMBERS = [2026, 2027, 2028, 2029, 2030, 2031]

# Output map sections that contain per-year metric cells
OUTPUT_SECTIONS = [
    "orders",
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "operating_metrics",
    "expenses",
]

logger = logging.getLogger("populate_model")


# ============================================================================
# Dependency check
# ============================================================================
try:
    import openpyxl  # noqa: F401 — needed transitively by xlcalculator
except ImportError:
    print(
        "ERROR: openpyxl is required but not installed.\n"
        "       pip install 'openpyxl>=3.1.2'",
        file=sys.stderr,
    )
    sys.exit(2)

try:
    from xlcalculator import Evaluator, ModelCompiler
except ImportError:
    print(
        "ERROR: xlcalculator is required but not installed.\n"
        "       pip install 'xlcalculator>=0.5.0'",
        file=sys.stderr,
    )
    sys.exit(2)


# ============================================================================
# JSONC Parser
# ============================================================================
def parse_jsonc(text: str) -> Any:
    """Parse JSON with ``//`` and ``/* */`` comments.

    Uses a character-by-character scanner that respects string boundaries
    (including escaped quotes) so that ``//`` inside URLs is preserved.
    After stripping comments, trailing commas before ``}`` or ``]`` are removed.
    """
    result: list[str] = []
    i = 0
    length = len(text)
    in_string = False

    while i < length:
        ch = text[i]

        if in_string:
            result.append(ch)
            if ch == "\\" and i + 1 < length:
                # Escaped character — consume next char unconditionally
                i += 1
                result.append(text[i])
            elif ch == '"':
                in_string = False
            i += 1
            continue

        # Outside a string
        if ch == '"':
            in_string = True
            result.append(ch)
            i += 1
            continue

        if ch == "/" and i + 1 < length:
            next_ch = text[i + 1]
            if next_ch == "/":
                # Single-line comment — skip to end of line
                i += 2
                while i < length and text[i] != "\n":
                    i += 1
                continue
            elif next_ch == "*":
                # Block comment — skip to closing */
                i += 2
                while i < length - 1:
                    if text[i] == "*" and text[i + 1] == "/":
                        i += 2
                        break
                    i += 1
                else:
                    i = length  # unterminated block comment
                continue

        result.append(ch)
        i += 1

    stripped = "".join(result)
    # Remove trailing commas before } or ]
    stripped = re.sub(r",\s*([}\]])", r"\1", stripped)
    return json.loads(stripped)


def load_jsonc(path: Path) -> Any:
    """Read and parse a JSONC file."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("File not found: %s", path)
        sys.exit(2)
    except OSError as exc:
        logger.error("Cannot read %s: %s", path, exc)
        sys.exit(2)
    return parse_jsonc(text)


# ============================================================================
# Sheet path resolution
# ============================================================================
def resolve_sheet_path(files: dict[str, bytes], sheet_name: str) -> str:
    """Resolve the XML path for *sheet_name* inside the xlsx ZIP.

    Parses ``xl/workbook.xml`` to map sheet name to ``rId``, then
    ``xl/_rels/workbook.xml.rels`` to map ``rId`` to a file path.

    Returns:
        A path like ``xl/worksheets/sheet2.xml``.
    """
    # Parse workbook.xml for sheet name -> rId
    wb_xml = files["xl/workbook.xml"].decode("utf-8")
    # Use regex to avoid namespace headaches
    sheet_pattern = re.compile(
        r'<sheet[^>]*\sname="' + re.escape(sheet_name) + r'"[^>]*?r:id="([^"]+)"',
        re.DOTALL,
    )
    m = sheet_pattern.search(wb_xml)
    if not m:
        raise ValueError(
            f"Sheet '{sheet_name}' not found in xl/workbook.xml"
        )
    r_id = m.group(1)
    logger.debug("Sheet '%s' has rId=%s", sheet_name, r_id)

    # Parse workbook.xml.rels for rId -> Target
    # Attributes can appear in any order, so match the full element then extract Target
    rels_xml = files["xl/_rels/workbook.xml.rels"].decode("utf-8")
    # First find any <Relationship> that contains Id="rIdN"
    rel_pattern = re.compile(
        r'<Relationship\s[^>]*Id="' + re.escape(r_id) + r'"[^>]*/?>',
        re.DOTALL,
    )
    rel_match = rel_pattern.search(rels_xml)
    if not rel_match:
        raise ValueError(
            f"Relationship {r_id} not found in xl/_rels/workbook.xml.rels"
        )
    # Then extract Target from the matched element
    target_match = re.search(r'Target="([^"]+)"', rel_match.group(0))
    if not target_match:
        raise ValueError(
            f"Relationship {r_id} has no Target attribute"
        )
    target = target_match.group(1)

    # Target is relative to xl/, e.g. "worksheets/sheet2.xml"
    xml_path = f"xl/{target}" if not target.startswith("xl/") else target
    logger.debug("Resolved sheet '%s' -> %s", sheet_name, xml_path)
    return xml_path


# ============================================================================
# XML cell writing
# ============================================================================
def write_cells_via_xml(
    template_path: Path,
    output_path: Path,
    cell_updates: dict[str, float | int],
) -> int:
    """Write cell values into *output_path* by editing XML inside the xlsx ZIP.

    1. Copies template to output.
    2. Replaces ``<v>`` tag values for each cell on the Assumptions sheet.
    3. Strips cached ``<v>`` from ALL formula cells on ALL sheets.
    4. Deletes ``xl/calcChain.xml`` and its Content_Types reference.
    5. Sets ``fullCalcOnLoad="1"`` on ``<calcPr>`` in workbook.xml.

    Returns:
        Number of cells successfully written.
    """
    shutil.copy2(template_path, output_path)

    # Read entire ZIP into memory
    with zipfile.ZipFile(str(output_path), "r") as zf:
        files: dict[str, bytes] = {name: zf.read(name) for name in zf.namelist()}

    # Resolve the Assumptions sheet XML path
    sheet_xml_path = resolve_sheet_path(files, "Assumptions")
    xml = files[sheet_xml_path].decode("utf-8")

    written = 0
    for cell_ref, value in cell_updates.items():
        # Match the cell element and replace its <v> content
        pattern = re.compile(
            rf'(<c[^>]*\sr="{re.escape(cell_ref)}"[^>]*>)(.*?)(</c>)',
            re.DOTALL,
        )
        m = pattern.search(xml)
        if not m:
            logger.warning("Cell %s not found in template XML — skipped", cell_ref)
            continue

        c_open = m.group(1)
        c_inner = m.group(2)
        c_close = m.group(3)

        # Remove t="s" (shared string type) if present — we are writing a raw number
        c_open_clean = re.sub(r'\s+t="s"', "", c_open)

        # Replace existing <v>...</v> or insert one
        if re.search(r"<v>[^<]*</v>", c_inner):
            new_inner = re.sub(r"<v>[^<]*</v>", f"<v>{value}</v>", c_inner)
        else:
            # No <v> tag — append before closing </c>
            new_inner = c_inner + f"<v>{value}</v>"

        new_cell = c_open_clean + new_inner + c_close
        xml = xml[: m.start()] + new_cell + xml[m.end() :]
        written += 1
        logger.debug("Wrote %s = %s", cell_ref, value)

    if written < len(cell_updates):
        logger.warning(
            "Wrote %d of %d cells — %d missed",
            written,
            len(cell_updates),
            len(cell_updates) - written,
        )

    files[sheet_xml_path] = xml.encode("utf-8")

    # ------------------------------------------------------------------
    # Strip cached <v> from ALL formula cells on ALL worksheet XMLs
    # ------------------------------------------------------------------
    for name in list(files.keys()):
        if name.startswith("xl/worksheets/") and name.endswith(".xml"):
            sheet_xml = files[name].decode("utf-8")
            # Cells with <f>...</f> formula followed by <v>...</v>
            sheet_xml = re.sub(
                r"(<c[^>]*>(?:<is>.*?</is>)?<f[^/]*>.*?</f>)<v>[^<]*</v>",
                r"\1",
                sheet_xml,
                flags=re.DOTALL,
            )
            # Cells with self-closing <f/> followed by <v>...</v>
            sheet_xml = re.sub(
                r"(<c[^>]*><f/>)<v>[^<]*</v>",
                r"\1",
                sheet_xml,
                flags=re.DOTALL,
            )
            files[name] = sheet_xml.encode("utf-8")

    # ------------------------------------------------------------------
    # Delete calcChain.xml
    # ------------------------------------------------------------------
    files.pop("xl/calcChain.xml", None)

    # Remove calcChain reference from [Content_Types].xml
    if "[Content_Types].xml" in files:
        ct = files["[Content_Types].xml"].decode("utf-8")
        ct = re.sub(r"<Override[^>]*calcChain[^>]*/>", "", ct)
        files["[Content_Types].xml"] = ct.encode("utf-8")

    # ------------------------------------------------------------------
    # Set fullCalcOnLoad="1" on <calcPr>
    # ------------------------------------------------------------------
    if "xl/workbook.xml" in files:
        wb_xml = files["xl/workbook.xml"].decode("utf-8")
        # Remove any existing attribute to avoid duplication
        wb_xml = re.sub(r'\s*fullCalcOnLoad="[^"]*"', "", wb_xml)
        wb_xml = re.sub(r"<calcPr\b", '<calcPr fullCalcOnLoad="1"', wb_xml)
        files["xl/workbook.xml"] = wb_xml.encode("utf-8")

    # ------------------------------------------------------------------
    # Write all files back to ZIP
    # ------------------------------------------------------------------
    with zipfile.ZipFile(str(output_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)

    logger.info("Wrote %d / %d input cells to %s", written, len(cell_updates), output_path.name)
    return written


# ============================================================================
# xlcalculator helpers
# ============================================================================
def set_xlcalc_input(
    evaluator: Evaluator, sheet_name: str, cell_address: str, value: Any
) -> None:
    """Set *value* in the evaluator for all reference-style variants of a cell."""
    m = re.match(r"([A-Z]+)(\d+)", cell_address)
    if not m:
        return
    col, row = m.groups()
    for variant in [
        f"{sheet_name}!{col}{row}",
        f"{sheet_name}!${col}${row}",
        f"{sheet_name}!${col}{row}",
        f"{sheet_name}!{col}${row}",
    ]:
        try:
            evaluator.set_cell_value(variant, value)
        except Exception:
            pass


def _create_evaluator(
    output_path: Path,
    cell_updates: dict[str, float | int],
) -> Evaluator:
    """Build an xlcalculator Evaluator from *output_path* with inputs set."""
    compiler = ModelCompiler()
    model = compiler.read_and_parse_archive(str(output_path))

    # Create reference-style aliases for every cell in the model
    for key in list(model.cells.keys()):
        if "!" not in key:
            continue
        sheet_part, cell_ref = key.split("!", 1)
        m = re.match(r"\$?([A-Z]+)\$?(\d+)", cell_ref)
        if not m:
            continue
        col, row = m.groups()
        base = f"{sheet_part}!{col}{row}"
        variants = [
            f"{sheet_part}!${col}${row}",
            f"{sheet_part}!${col}{row}",
            f"{sheet_part}!{col}${row}",
            base,
        ]
        for v in variants:
            if v not in model.cells:
                model.cells[v] = model.cells[key]

    evaluator = Evaluator(model)

    # Set all input values with all reference variants
    for cell_ref, value in cell_updates.items():
        set_xlcalc_input(evaluator, "Assumptions", cell_ref, value)

    return evaluator


# ============================================================================
# Output extraction
# ============================================================================
def extract_outputs(
    output_path: Path,
    cell_updates: dict[str, float | int],
    output_map: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate formulas via xlcalculator and read output metrics.

    Returns a dict mirroring the output_map sections, with numeric values
    for each metric/year cell.
    """
    evaluator = _create_evaluator(output_path, cell_updates)
    default_sheet = output_map.get("default_sheet", "Model")

    outputs: dict[str, Any] = {}

    for section_name in OUTPUT_SECTIONS:
        section = output_map.get(section_name)
        if not section:
            continue
        section_out: dict[str, dict[str, Any]] = {}
        for metric_name, metric_def in section.items():
            if not isinstance(metric_def, dict) or "cells" not in metric_def:
                continue
            year_values: dict[str, Any] = {}
            for year_key, cell_addr in metric_def["cells"].items():
                ref = f"{default_sheet}!{cell_addr}"
                try:
                    val = evaluator.evaluate(ref)
                    if isinstance(val, float):
                        val = round(val, 2)
                except Exception:
                    val = None
                year_values[year_key] = val
            section_out[metric_name] = year_values
        outputs[section_name] = section_out

    return outputs


# ============================================================================
# Derived metrics
# ============================================================================
def compute_derived(outputs: dict[str, Any]) -> dict[str, Any]:
    """Compute derived metrics from raw model outputs.

    - ``revenue_cagr``: compound annual growth of net revenue, years 1-6.
    - ``break_even_year``: first calendar year with positive net income (or None).
    - ``runway_months``: if year-1 burn rate is negative, months of cash runway.
    """
    derived: dict[str, Any] = {
        "revenue_cagr": None,
        "break_even_year": None,
        "runway_months": None,
    }

    # Revenue CAGR
    try:
        net_rev = outputs.get("income_statement", {}).get("net_revenue", {})
        nr_y1 = net_rev.get("year_1")
        nr_y6 = net_rev.get("year_6")
        if nr_y1 and nr_y6 and nr_y1 > 0:
            derived["revenue_cagr"] = round(((nr_y6 / nr_y1) ** 0.2) - 1, 4)
    except Exception:
        pass

    # Break-even year
    try:
        net_inc = outputs.get("income_statement", {}).get("net_income", {})
        for idx, yk in enumerate(YEAR_KEYS):
            val = net_inc.get(yk)
            if val is not None and val > 0:
                derived["break_even_year"] = YEAR_NUMBERS[idx]
                break
    except Exception:
        pass

    # Runway months
    try:
        burn_y1 = (
            outputs.get("operating_metrics", {}).get("burn_rate", {}).get("year_1")
        )
        cash_y1 = (
            outputs.get("cash_flow", {}).get("closing_cash_balance", {}).get("year_1")
        )
        if burn_y1 is not None and burn_y1 < 0 and cash_y1 is not None:
            monthly_burn = abs(burn_y1) / 12
            if monthly_burn > 0:
                derived["runway_months"] = round(cash_y1 / monthly_burn, 1)
    except Exception:
        pass

    return derived


# ============================================================================
# Balance-sheet validation
# ============================================================================
def validate_balance_sheet(outputs: dict[str, Any]) -> bool:
    """Check that balance_check (E194:J194) is within +/-0.01 of zero for all years."""
    bc = outputs.get("balance_sheet", {}).get("balance_check", {})
    for yk in YEAR_KEYS:
        val = bc.get(yk)
        if val is None:
            logger.warning("balance_check %s is None — cannot verify", yk)
            return False
        if abs(val) > BALANCE_TOLERANCE:
            logger.warning("balance_check %s = %.4f (exceeds tolerance)", yk, val)
            return False
    return True


# ============================================================================
# Equity optimization
# ============================================================================
def equity_optimization(
    assumptions: dict[str, Any],
    cell_updates: dict[str, float | int],
    id_to_cell: dict[str, str],
    template_path: Path,
    output_path: Path,
    output_map: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run equity optimization loop if equity_mode is 'suggest'.

    Returns:
        (final_outputs, equity_audit_dict)
    """
    internal = assumptions.get("__internal_targets", {})
    equity_mode = internal.get("equity_mode", "explicit")
    initial_equity = cell_updates.get(id_to_cell.get("initial_equity_injection", "B76"), 0)

    equity_audit: dict[str, Any] = {
        "mode": equity_mode,
        "initial_estimate": initial_equity,
        "iterations": [],
        "final_equity": initial_equity,
        "converged": None,
        "total_iterations": 0,
        "final_min_cash": None,
        "final_min_cash_year": None,
    }

    # --- First run: write + extract ---
    written = write_cells_via_xml(template_path, output_path, cell_updates)
    outputs = extract_outputs(output_path, cell_updates, output_map)

    # Determine min closing cash
    def _min_cash(outs: dict) -> tuple[Optional[float], Optional[int]]:
        ccb = outs.get("cash_flow", {}).get("closing_cash_balance", {})
        min_val: Optional[float] = None
        min_year: Optional[int] = None
        for idx, yk in enumerate(YEAR_KEYS):
            v = ccb.get(yk)
            if v is not None and (min_val is None or v < min_val):
                min_val = v
                min_year = YEAR_NUMBERS[idx]
        return min_val, min_year

    min_cash, min_year = _min_cash(outputs)
    equity_audit["final_min_cash"] = min_cash
    equity_audit["final_min_cash_year"] = min_year

    if equity_mode != "suggest":
        # Explicit mode — no iteration
        equity_audit["converged"] = None
        equity_audit["total_iterations"] = 0
        return outputs, equity_audit

    # --- Suggest mode: iterate ---
    current_equity = initial_equity
    equity_cell = id_to_cell.get("initial_equity_injection", "B76")

    for iteration in range(1, MAX_EQUITY_ITERATIONS + 1):
        iter_entry: dict[str, Any] = {
            "iteration": iteration,
            "equity_tested": current_equity,
            "min_cash": min_cash,
            "min_cash_year": min_year,
            "result": "deficit" if (min_cash is not None and min_cash < CASH_BUFFER) else "converged",
        }
        equity_audit["iterations"].append(iter_entry)

        if min_cash is not None and min_cash >= CASH_BUFFER:
            # Converged
            iter_entry["result"] = "converged"
            equity_audit["converged"] = True
            equity_audit["final_equity"] = current_equity
            equity_audit["total_iterations"] = iteration
            equity_audit["final_min_cash"] = min_cash
            equity_audit["final_min_cash_year"] = min_year
            return outputs, equity_audit

        # Calculate new equity
        deficit = abs(min_cash) if min_cash is not None else 0
        new_equity = (current_equity + deficit + CASH_BUFFER) * EQUITY_MULTIPLIER
        new_equity = round(new_equity / 1000) * 1000  # round to nearest $1,000
        logger.info(
            "Equity iteration %d: min_cash=%.0f in %s -> new equity=$%.0f",
            iteration, min_cash or 0, min_year, new_equity,
        )

        current_equity = new_equity
        cell_updates[equity_cell] = current_equity

        # Re-run full write + extract cycle
        written = write_cells_via_xml(template_path, output_path, cell_updates)
        outputs = extract_outputs(output_path, cell_updates, output_map)
        min_cash, min_year = _min_cash(outputs)

    # Exhausted iterations
    final_entry: dict[str, Any] = {
        "iteration": MAX_EQUITY_ITERATIONS + 1,
        "equity_tested": current_equity,
        "min_cash": min_cash,
        "min_cash_year": min_year,
        "result": "converged" if (min_cash is not None and min_cash >= CASH_BUFFER) else "max_iterations",
    }
    equity_audit["iterations"].append(final_entry)
    equity_audit["converged"] = min_cash is not None and min_cash >= CASH_BUFFER
    equity_audit["final_equity"] = current_equity
    equity_audit["total_iterations"] = MAX_EQUITY_ITERATIONS
    equity_audit["final_min_cash"] = min_cash
    equity_audit["final_min_cash_year"] = min_year

    if not equity_audit["converged"]:
        logger.warning(
            "Equity optimization did not converge after %d iterations "
            "(final min cash: $%.0f). Proceeding with equity=$%.0f.",
            MAX_EQUITY_ITERATIONS,
            min_cash or 0,
            current_equity,
        )

    return outputs, equity_audit


# ============================================================================
# Build cell updates from assumptions
# ============================================================================
def build_cell_updates(
    assumptions: dict[str, Any],
    input_map: dict[str, Any],
) -> tuple[dict[str, float | int], dict[str, str]]:
    """Map resolved assumptions to cell addresses.

    Returns:
        (cell_updates, id_to_cell) — cell_updates is ``{cell_address: value}``,
        id_to_cell maps ``input_id`` to ``cell_address``.
    """
    cell_updates: dict[str, float | int] = {}
    id_to_cell: dict[str, str] = {}

    inputs_list = input_map.get("inputs", [])
    for entry in inputs_list:
        input_id: str = entry["input_id"]
        cell_address: str = entry["cell_address"]
        value_type: str = entry.get("type", "float")

        if input_id in EXCLUDED_IDS:
            logger.debug("Skipping excluded input: %s", input_id)
            continue

        id_to_cell[input_id] = cell_address

        # Look up value in assumptions (flat top-level keys)
        if input_id not in assumptions:
            logger.warning("Assumption '%s' not found in assumptions JSON — skipping", input_id)
            continue

        raw_value = assumptions[input_id]
        if raw_value is None:
            logger.warning("Assumption '%s' is null — skipping", input_id)
            continue

        # Type coercion
        if value_type in ("int", "year"):
            value: int | float = int(raw_value)
        elif value_type in ("float", "float_pct", "currency"):
            value = float(raw_value)
        else:
            value = float(raw_value)

        cell_updates[cell_address] = value

    logger.info(
        "Built %d cell updates from %d input map entries (%d excluded)",
        len(cell_updates),
        len(inputs_list),
        len(EXCLUDED_IDS),
    )
    return cell_updates, id_to_cell


# ============================================================================
# Main
# ============================================================================
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate eCommerce financial model template with resolved assumptions.",
    )
    parser.add_argument(
        "store_name",
        help="Store name (used to locate assumptions JSON and name output files)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for input/output files (default: current working directory)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG logging",
    )
    args = parser.parse_args()

    # Logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    store_name: str = args.store_name
    output_dir: Path = args.output_dir or Path.cwd()
    output_dir = output_dir.resolve()

    assumptions_path = output_dir / f"{store_name}_assumptions.json"
    model_output_path = output_dir / f"{store_name}_Financial_Model.xlsx"
    json_output_path = output_dir / f"{store_name}_model_outputs.json"

    # ------------------------------------------------------------------
    # Validate paths
    # ------------------------------------------------------------------
    if not TEMPLATE_PATH.exists():
        logger.error("Template not found: %s", TEMPLATE_PATH)
        sys.exit(2)
    if not INPUT_MAP_PATH.exists():
        logger.error("Input map not found: %s", INPUT_MAP_PATH)
        sys.exit(2)
    if not OUTPUT_MAP_PATH.exists():
        logger.error("Output map not found: %s", OUTPUT_MAP_PATH)
        sys.exit(2)
    if not assumptions_path.exists():
        logger.error("Assumptions file not found: %s", assumptions_path)
        sys.exit(2)

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    logger.info("Loading assumptions from %s", assumptions_path)
    try:
        raw_assumptions = json.loads(assumptions_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read assumptions: %s", exc)
        sys.exit(2)

    # Convert {"inputs": [{input_id, value, ...}, ...]} to flat {input_id: value}
    if "inputs" in raw_assumptions and isinstance(raw_assumptions["inputs"], list):
        assumptions = {
            entry["input_id"]: entry["value"]
            for entry in raw_assumptions["inputs"]
            if "input_id" in entry and "value" in entry
        }
        internal_targets = raw_assumptions.get("__internal_targets", {})
    else:
        # Already flat dict (legacy format)
        assumptions = raw_assumptions
        internal_targets = {}

    input_map = load_jsonc(INPUT_MAP_PATH)
    output_map = load_jsonc(OUTPUT_MAP_PATH)

    # ------------------------------------------------------------------
    # Build cell updates
    # ------------------------------------------------------------------
    cell_updates, id_to_cell = build_cell_updates(assumptions, input_map)
    if not cell_updates:
        logger.error("No cell updates produced — check assumptions JSON keys")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Equity optimization (or single-pass)
    # ------------------------------------------------------------------
    logger.info("Running financial model population...")
    # Re-attach __internal_targets for equity_optimization to read equity_mode
    assumptions_with_targets = dict(assumptions)
    assumptions_with_targets["__internal_targets"] = internal_targets
    outputs, equity_audit = equity_optimization(
        assumptions=assumptions_with_targets,
        cell_updates=cell_updates,
        id_to_cell=id_to_cell,
        template_path=TEMPLATE_PATH,
        output_path=model_output_path,
        output_map=output_map,
    )

    # ------------------------------------------------------------------
    # Derived metrics
    # ------------------------------------------------------------------
    derived = compute_derived(outputs)
    outputs["derived"] = derived

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    balance_ok = validate_balance_sheet(outputs)
    inputs_written = equity_audit.get("total_iterations", 0)
    # Count from last write cycle
    final_written = sum(
        1 for entry in input_map.get("inputs", [])
        if entry["input_id"] not in EXCLUDED_IDS
        and entry["input_id"] in assumptions
        and assumptions[entry["input_id"]] is not None
    )
    outputs["validation"] = {
        "balance_check_passed": balance_ok,
        "inputs_written": final_written,
    }

    # ------------------------------------------------------------------
    # Equity audit
    # ------------------------------------------------------------------
    outputs["equity_audit"] = equity_audit

    # ------------------------------------------------------------------
    # Write JSON outputs
    # ------------------------------------------------------------------
    try:
        json_output_path.write_text(
            json.dumps(outputs, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Model outputs written to %s", json_output_path)
    except OSError as exc:
        logger.error("Failed to write model outputs: %s", exc)
        sys.exit(2)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Excel model:    %s", model_output_path)
    logger.info("Model outputs:  %s", json_output_path)
    logger.info("Inputs written: %d", final_written)
    logger.info("Balance check:  %s", "PASSED" if balance_ok else "FAILED")
    logger.info(
        "Equity mode:    %s (final=$%s, iterations=%d)",
        equity_audit["mode"],
        f"{float(equity_audit['final_equity']):,.0f}" if equity_audit["final_equity"] else "N/A",
        equity_audit["total_iterations"],
    )
    if derived["revenue_cagr"] is not None:
        logger.info("Revenue CAGR:   %.1f%%", derived["revenue_cagr"] * 100)
    if derived["break_even_year"]:
        logger.info("Break-even:     %d", derived["break_even_year"])
    if derived["runway_months"] is not None:
        logger.info("Runway:         %.1f months", derived["runway_months"])

    # Exit code
    if not balance_ok:
        logger.warning("Exiting with code 1 — balance sheet validation failed")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
