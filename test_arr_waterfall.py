"""
Unit tests for arr_waterfall.py's core logic, using small hand-built
subscriber sets where the expected ARR waterfall can be verified by hand.

Run with: python3 test_arr_waterfall.py
"""

import unittest

import pandas as pd

from arr_waterfall import active_mrr_total, add_sanity_check, build_waterfall


def make_df(rows):
    df = pd.DataFrame(rows)
    for col in ("start_date", "end_date", "plan_change_date"):
        df[col] = pd.to_datetime(df[col])
    return df


class TestActiveMrrTotal(unittest.TestCase):
    def test_customer_not_yet_started_is_excluded(self):
        df = make_df(
            [
                {
                    "customer_id": 1,
                    "mrr": 100,
                    "start_date": "2025-02-01",
                    "end_date": None,
                    "plan_change_date": None,
                    "plan_change_mrr": None,
                }
            ]
        )
        self.assertEqual(active_mrr_total(df, pd.Timestamp("2025-01-31")), 0)
        self.assertEqual(active_mrr_total(df, pd.Timestamp("2025-02-01")), 100)

    def test_churn_on_asof_date_is_excluded_going_forward(self):
        df = make_df(
            [
                {
                    "customer_id": 1,
                    "mrr": 100,
                    "start_date": "2025-01-01",
                    "end_date": "2025-03-31",
                    "plan_change_date": None,
                    "plan_change_mrr": None,
                }
            ]
        )
        # active_mrr_total uses a strict '>' against end_date (see its
        # docstring), so the customer is still active the day before
        # end_date but already excluded on end_date itself.
        self.assertEqual(active_mrr_total(df, pd.Timestamp("2025-03-30")), 100)
        self.assertEqual(active_mrr_total(df, pd.Timestamp("2025-03-31")), 0)

    def test_plan_change_swaps_mrr_after_effective_date(self):
        df = make_df(
            [
                {
                    "customer_id": 1,
                    "mrr": 100,
                    "start_date": "2025-01-01",
                    "end_date": None,
                    "plan_change_date": "2025-03-15",
                    "plan_change_mrr": 150,
                }
            ]
        )
        self.assertEqual(active_mrr_total(df, pd.Timestamp("2025-03-14")), 100)
        self.assertEqual(active_mrr_total(df, pd.Timestamp("2025-03-15")), 150)


class TestWaterfallReconciles(unittest.TestCase):
    """Each scenario below is checked against hand-computed monthly ARR."""

    def test_new_expansion_churn_all_reconcile(self):
        df = make_df(
            [
                # New in Jan, expands in Mar.
                {
                    "customer_id": 1,
                    "mrr": 1000,
                    "start_date": "2025-01-01",
                    "end_date": None,
                    "plan_change_date": "2025-03-15",
                    "plan_change_mrr": 1500,
                },
                # Active from the start, churns in April.
                {
                    "customer_id": 2,
                    "mrr": 500,
                    "start_date": "2025-01-01",
                    "end_date": "2025-04-10",
                    "plan_change_date": None,
                    "plan_change_mrr": None,
                },
            ]
        )
        waterfall = build_waterfall(df, "2025-01-01", "2025-04-01")
        checked = add_sanity_check(waterfall)

        self.assertTrue(checked["reconciles"].all())

        by_month = checked.set_index("month")
        self.assertEqual(by_month.loc["2025-01", "new_arr"], 18000)  # (1000+500)*12
        self.assertEqual(by_month.loc["2025-03", "expansion_arr"], 6000)  # (1500-1000)*12
        self.assertEqual(by_month.loc["2025-04", "churned_arr"], 6000)  # 500*12
        self.assertEqual(by_month.loc["2025-04", "ending_arr"], 18000)  # customer 1 only


if __name__ == "__main__":
    unittest.main()
