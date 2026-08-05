import pandas as pd
import json
import os
import sys
from datetime import datetime

# Allow running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_tenant_db_engine
from sqlalchemy.orm import sessionmaker
import models

# ── CONFIG ───────────────────────────────────────────────────────────────────
EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "additional_metrics_dump",
    "Inbound Dashboard_Manual Metrics Data.xlsx"
)
SHEET_NAME  = "Inbound Metrics"
OUTPUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_daily_metrics.json")

# Row indices (0-based) inside the sheet
DATE_ROW_IDX   = 1
METRIC_ROW_MAP = {
    "Gross Seats":                        2,
    "Gross Tickets":                      3,
    "Intr/Journey ( Overall )":           4,
    "Defects":                            5,
    "Defects/Journey":                    6,
    "Present Agent HC":                   7,
    "Intr/Journey % ( Inbound + WH)":    8,
    "Intr/Journey %  ( Travel update )":  9,
    "No. of Service Delay":              10,
    "Delay Pax Impacted":                11,
    "No. of Service Cancel":             12,
    "Service Cancel Pax Impacted":       13,
    "No. of Service Breakdown":          14,
    "Break Down Pax Impacted":           15,
    "Impacted %":                        16,
    "Total Pax Impacted":                17,
    "Cancellations Impact %":            18,
    "Call Drop Not Done":                20,
    "Blank Call Not Done":                21,
    "Overall Call Not Done":              22,
    "Call Not Done %":                    23,
    "Agent Disconnected":                 25,
    "Agent Disconnected %":               26,
    "Call Not Disposed":                  28,
    "Call Not Disposed %":                29,
}
# ─────────────────────────────────────────────────────────────────────────────


def try_parse_date(val):
    """Return datetime if val is a recognisable date, else None.
    Handles datetime objects (older cols) and strings like '1/31/2026' (newer cols).
    Skips weekly labels like 'w1', 'W3 Feb' etc.
    """
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(val.strip(), fmt)
            except ValueError:
                continue
    return None


def clean_value(val):
    """Convert a raw cell value to a JSON-safe number, or None if missing/error."""
    import math
    if val is None:
        return None
    if isinstance(val, float):
        return None if math.isnan(val) else val
    if isinstance(val, int):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        if s in ("#REF!", "#DIV/0!", "#N/A", "#VALUE!", "-", ""):
            return None
        if s.endswith("%"):
            try:
                return float(s[:-1]) / 100
            except ValueError:
                return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def to_int(val):
    if val is None:
        return None
    try:
        return int(round(val))
    except (TypeError, ValueError):
        return None


def ingest():
    print(f"Reading: {EXCEL_PATH}")
    if not os.path.exists(EXCEL_PATH):
        print(f"ERROR: File not found at {EXCEL_PATH}")
        return

    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, header=None)
    print(f"Sheet shape: {df.shape[0]} rows x {df.shape[1]} cols")

    date_row   = df.iloc[DATE_ROW_IDX, :]
    total_cols = len(date_row)

    # ── DB setup ─────────────────────────────────────────────────────────────
    engine = get_tenant_db_engine("Inbound")
    # Ensure the new table exists
    models.TenantBase.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # ── Load existing JSON (kept in sync) ────────────────────────────────────
    existing_json = {}
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r") as f:
                existing_json = json.load(f)
            print(f"Loaded existing JSON with {len(existing_json)} entries.")
        except Exception as e:
            print(f"Warning: could not load existing JSON ({e}). Starting fresh.")

    parsed_count  = 0
    skipped_count = 0

    for col_idx in range(1, total_cols):
        dt = try_parse_date(date_row.iloc[col_idx])
        if dt is None:
            skipped_count += 1
            continue

        date_key = dt.strftime("%Y-%m-%d")

        # ── Extract all metrics for this date ─────────────────────────────
        raw = {}
        for metric_name, row_idx in METRIC_ROW_MAP.items():
            raw[metric_name] = clean_value(df.iloc[row_idx, col_idx])

        # ── Build JSON record (omit None values) ──────────────────────────
        day_json = {k: v for k, v in raw.items() if v is not None}
        existing_json[date_key] = day_json

        in_range = (datetime(2026, 1, 1) <= dt <= datetime(2026, 8, 2))

        # ── Build DB record ───────────────────────────────────────────────
        db_row = models.DailyManualMetric(
            date                    = date_key,
            gross_seats             = raw.get("Gross Seats"),
            gross_tickets           = raw.get("Gross Tickets"),
            intr_journey_overall    = raw.get("Intr/Journey ( Overall )"),
            intr_journey_inbound_wh = raw.get("Intr/Journey % ( Inbound + WH)"),
            intr_journey_travel     = raw.get("Intr/Journey %  ( Travel update )"),
            defects                 = raw.get("Defects"),
            defects_journey         = raw.get("Defects/Journey"),
            present_agent_hc        = to_int(raw.get("Present Agent HC")),
            service_delay_count     = to_int(raw.get("No. of Service Delay")),
            delay_pax_impacted      = to_int(raw.get("Delay Pax Impacted")),
            service_cancel_count    = to_int(raw.get("No. of Service Cancel")),
            cancel_pax_impacted     = to_int(raw.get("Service Cancel Pax Impacted")),
            service_breakdown_count = to_int(raw.get("No. of Service Breakdown")),
            breakdown_pax_impacted  = to_int(raw.get("Break Down Pax Impacted")),
            impacted_pct            = raw.get("Impacted %"),
            total_pax_impacted      = to_int(raw.get("Total Pax Impacted")),
            cancellations_impact_pct= raw.get("Cancellations Impact %"),
            
            call_drop_not_done       = to_int(raw.get("Call Drop Not Done")) if in_range else None,
            blank_call_not_done      = to_int(raw.get("Blank Call Not Done")) if in_range else None,
            overall_call_not_done    = to_int(raw.get("Overall Call Not Done")) if in_range else None,
            call_not_done_pct        = raw.get("Call Not Done %") if in_range else None,
            agent_disconnected       = to_int(raw.get("Agent Disconnected")) if in_range else None,
            agent_disconnected_pct   = raw.get("Agent Disconnected %") if in_range else None,
            call_not_disposed        = to_int(raw.get("Call Not Disposed")) if in_range else None,
            call_not_disposed_pct    = raw.get("Call Not Disposed %") if in_range else None,
        )

        # Upsert: delete existing row for this date then re-insert
        session.query(models.DailyManualMetric)\
               .filter(models.DailyManualMetric.date == date_key)\
               .delete()
        session.add(db_row)
        parsed_count += 1

        if parsed_count % 100 == 0:
            session.commit()
            print(f"  ... committed {parsed_count} rows so far")

    session.commit()
    session.close()
    print(f"\nDB insert complete.")

    # ── Write JSON (keeps metrics.py API working unchanged) ───────────────
    sorted_json = dict(sorted(existing_json.items()))
    with open(OUTPUT_JSON, "w") as f:
        json.dump(sorted_json, f, indent=2)

    print(f"\nSummary:")
    print(f"  Valid date columns processed : {parsed_count}")
    print(f"  Non-date columns skipped     : {skipped_count}")
    print(f"  DB rows written              : {parsed_count}  (metrics_inbound.db → daily_manual_metrics)")
    print(f"  JSON entries written         : {len(sorted_json)}  ({OUTPUT_JSON})")


if __name__ == "__main__":
    ingest()
