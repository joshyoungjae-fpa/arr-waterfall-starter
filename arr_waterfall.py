"""
Monthly ARR waterfall from subscriptions.csv (Jan 2025 - Jun 2026).

Data model assumed from the columns:
  - mrr: the customer's MRR from start_date until plan_change_date (or forever
    if plan_change_date is empty).
  - plan_change_date / plan_change_mrr: a single plan change event; MRR becomes
    plan_change_mrr from plan_change_date onward.
  - end_date: last date the subscription is active (inclusive). Empty = still active.

Sign convention in the output CSV:
  - starting_arr, new_arr, expansion_arr, ending_arr: positive
  - contraction_arr, churned_arr: positive magnitudes (amount of ARR lost)
  - waterfall identity: starting_arr + new_arr + expansion_arr
                         - contraction_arr - churned_arr == ending_arr
"""

import numpy as np
import pandas as pd

INPUT_CSV = "subscriptions.csv"
OUTPUT_CSV = "monthly_waterfall.csv"
START_MONTH = "2025-01-01"
END_MONTH = "2026-06-01"


def load_subscriptions(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        parse_dates=["start_date", "end_date", "plan_change_date"],
    )
    return df


def active_mrr_total(df: pd.DataFrame, asof_date: pd.Timestamp) -> float:
    """Total run-rate MRR of customers still active *going forward* from asof_date.

    end_date is the customer's last day of service (inclusive for billing), so a
    customer whose end_date falls exactly on asof_date has already churned as far
    as the forward-looking ARR run-rate is concerned -- hence the strict '>' here.
    This keeps ending_arr(month) == starting_arr(month + 1) even when churn lands
    on the last calendar day of a month.
    """
    active = (df["start_date"] <= asof_date) & (
        df["end_date"].isna() | (df["end_date"] > asof_date)
    )
    changed = df["plan_change_date"].notna() & (df["plan_change_date"] <= asof_date)
    mrr = np.where(changed, df["plan_change_mrr"], df["mrr"])
    return float((mrr * active).sum())


def build_waterfall(df: pd.DataFrame, start_month: str, end_month: str) -> pd.DataFrame:
    months = pd.date_range(start_month, end_month, freq="MS")
    rows = []

    for period_start in months:
        period_end = period_start + pd.offsets.MonthEnd(0)
        prev_end = period_start - pd.Timedelta(days=1)

        starting_arr = active_mrr_total(df, prev_end) * 12
        ending_arr = active_mrr_total(df, period_end) * 12

        # New ARR: customers whose subscription started this month.
        new_mask = df["start_date"].between(period_start, period_end)
        new_arr = (df.loc[new_mask, "mrr"] * 12).sum()

        # Plan changes that took effect this month.
        change_mask = df["plan_change_date"].notna() & df["plan_change_date"].between(
            period_start, period_end
        )
        delta = df.loc[change_mask, "plan_change_mrr"] - df.loc[change_mask, "mrr"]
        expansion_arr = (delta[delta > 0] * 12).sum()
        contraction_arr = (-delta[delta < 0] * 12).sum()

        # Churn: customers whose end_date falls this month.
        churn_mask = df["end_date"].notna() & df["end_date"].between(period_start, period_end)
        churned = df.loc[churn_mask]
        churned_had_change = churned["plan_change_date"].notna() & (
            churned["plan_change_date"] <= churned["end_date"]
        )
        churn_mrr = np.where(churned_had_change, churned["plan_change_mrr"], churned["mrr"])
        churned_arr = float((churn_mrr).sum()) * 12

        rows.append(
            {
                "month": period_start.strftime("%Y-%m"),
                "starting_arr": starting_arr,
                "new_arr": new_arr,
                "expansion_arr": expansion_arr,
                "contraction_arr": contraction_arr,
                "churned_arr": churned_arr,
                "ending_arr": ending_arr,
            }
        )

    waterfall = pd.DataFrame(rows)
    for col in waterfall.columns[1:]:
        waterfall[col] = waterfall[col].round(2)
    return waterfall


def add_sanity_check(waterfall: pd.DataFrame) -> pd.DataFrame:
    waterfall = waterfall.copy()
    waterfall["computed_ending_arr"] = (
        waterfall["starting_arr"]
        + waterfall["new_arr"]
        + waterfall["expansion_arr"]
        - waterfall["contraction_arr"]
        - waterfall["churned_arr"]
    ).round(2)
    waterfall["reconciles"] = np.isclose(
        waterfall["computed_ending_arr"], waterfall["ending_arr"], atol=0.01
    )
    return waterfall


def main():
    df = load_subscriptions(INPUT_CSV)
    waterfall = build_waterfall(df, START_MONTH, END_MONTH)
    checked = add_sanity_check(waterfall)

    checked.drop(columns=["computed_ending_arr", "reconciles"]).to_csv(
        OUTPUT_CSV, index=False
    )

    with pd.option_context("display.float_format", lambda x: f"{x:,.2f}", "display.width", 160):
        print(checked.drop(columns=["computed_ending_arr", "reconciles"]).to_string(index=False))

    print("\nSanity check: starting_arr + new_arr + expansion_arr - contraction_arr - churned_arr == ending_arr")
    if checked["reconciles"].all():
        print("PASS - all months reconcile.")
    else:
        bad = checked.loc[~checked["reconciles"], ["month", "computed_ending_arr", "ending_arr"]]
        print("FAIL - mismatches found:")
        print(bad.to_string(index=False))

    print(f"\nWrote {OUTPUT_CSV} ({len(checked)} months).")


if __name__ == "__main__":
    main()
