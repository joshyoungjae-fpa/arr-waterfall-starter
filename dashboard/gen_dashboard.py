"""
Builds the JSON payload for the interactive ARR waterfall dashboard:
one object per month with the aggregate waterfall figures (cross-checked
against monthly_waterfall.csv, produced by arr_waterfall.py) plus the
actual customer rows behind each of the four flows, for drill-down.

Same active/churn-boundary rules as arr_waterfall.py: end_date is
exclusive for "still active going forward" (a customer whose end_date is
literally the last day of the month has already dropped out of that
month's ending ARR), so this file mirrors that logic rather than
re-deriving something subtly different.
"""
import json
from pathlib import Path

import pandas as pd
import numpy as np

# anchored to this file's location (not the caller's cwd) since this script
# now lives one level below the CSVs it reads
BASE = Path(__file__).resolve().parent
ROOT = BASE.parent

SUBS_CSV = ROOT / "subscriptions.csv"
WATERFALL_CSV = ROOT / "monthly_waterfall.csv"
OUT_JSON = BASE / "waterfall_data.json"

df = pd.read_csv(SUBS_CSV, parse_dates=["start_date", "end_date", "plan_change_date"])
agg = pd.read_csv(WATERFALL_CSV)

months = pd.date_range("2025-01-01", "2026-06-01", freq="MS")

MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]


def r2(x):
    return round(float(x), 2)


payload = []
for period_start in months:
    period_end = period_start + pd.offsets.MonthEnd(0)
    key = period_start.strftime("%Y-%m")
    agg_row = agg.loc[agg["month"] == key].iloc[0]

    new_mask = df["start_date"].between(period_start, period_end)
    new_rows = df.loc[new_mask].sort_values("mrr", ascending=False)
    new_customers = [
        {"id": int(r.customer_id), "plan": r.plan, "mrr": r2(r.mrr),
         "date": r.start_date.strftime("%Y-%m-%d")}
        for r in new_rows.itertuples()
    ]

    change_mask = df["plan_change_date"].notna() & df["plan_change_date"].between(period_start, period_end)
    changed = df.loc[change_mask].copy()
    changed["delta"] = changed["plan_change_mrr"] - changed["mrr"]

    exp_rows = changed.loc[changed["delta"] > 0].sort_values("delta", ascending=False)
    expansion_customers = [
        {"id": int(r.customer_id), "plan": r.plan, "fromMrr": r2(r.mrr),
         "toMrr": r2(r.plan_change_mrr), "delta": r2(r.delta),
         "date": r.plan_change_date.strftime("%Y-%m-%d")}
        for r in exp_rows.itertuples()
    ]

    con_rows = changed.loc[changed["delta"] < 0].sort_values("delta")
    contraction_customers = [
        {"id": int(r.customer_id), "plan": r.plan, "fromMrr": r2(r.mrr),
         "toMrr": r2(r.plan_change_mrr), "delta": r2(-r.delta),
         "date": r.plan_change_date.strftime("%Y-%m-%d")}
        for r in con_rows.itertuples()
    ]

    churn_mask = df["end_date"].notna() & df["end_date"].between(period_start, period_end)
    churned = df.loc[churn_mask].copy()
    had_change = churned["plan_change_date"].notna() & (churned["plan_change_date"] <= churned["end_date"])
    churned["mrr_at_churn"] = np.where(had_change, churned["plan_change_mrr"], churned["mrr"])
    churned_rows = churned.sort_values("mrr_at_churn", ascending=False)
    churned_customers = [
        {"id": int(r.customer_id), "plan": r.plan, "mrr": r2(r.mrr_at_churn),
         "date": r.end_date.strftime("%Y-%m-%d")}
        for r in churned_rows.itertuples()
    ]

    # cross-check: drill-down sums must equal the published aggregate
    assert abs(sum(c["mrr"] for c in new_customers) * 12 - agg_row["new_arr"]) < 0.02, key
    assert abs(sum(c["delta"] for c in expansion_customers) * 12 - agg_row["expansion_arr"]) < 0.02, key
    assert abs(sum(c["delta"] for c in contraction_customers) * 12 - agg_row["contraction_arr"]) < 0.02, key
    assert abs(sum(c["mrr"] for c in churned_customers) * 12 - agg_row["churned_arr"]) < 0.02, key

    dt = period_start
    payload.append({
        "month": key,
        "label": f"{MONTH_NAMES[dt.month-1]} {dt.year}",
        "short": MONTH_NAMES[dt.month-1][:3],
        "year": dt.year,
        "starting": r2(agg_row["starting_arr"]),
        "new": r2(agg_row["new_arr"]),
        "expansion": r2(agg_row["expansion_arr"]),
        "contraction": r2(agg_row["contraction_arr"]),
        "churned": r2(agg_row["churned_arr"]),
        "ending": r2(agg_row["ending_arr"]),
        "nrr": None if pd.isna(agg_row["nrr_pct"]) else r2(agg_row["nrr_pct"]),
        "newCustomers": new_customers,
        "expansionCustomers": expansion_customers,
        "contractionCustomers": contraction_customers,
        "churnedCustomers": churned_customers,
    })

Path(OUT_JSON).write_text(json.dumps(payload))
print("months:", len(payload))
print("max new customers in a month:", max(len(m["newCustomers"]) for m in payload))
print("max churn customers in a month:", max(len(m["churnedCustomers"]) for m in payload))
print("all cross-checks passed")
