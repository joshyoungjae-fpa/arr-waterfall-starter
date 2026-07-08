# ARR Waterfall — Claude Code Starter Project

This is a mock SaaS subscription dataset so you can practice building an
ARR waterfall using Claude Code, hands-on.

## What's in this folder
- `subscriptions.csv` — 156 mock customers, Jan 2025–Jun 2026, three plans
  (Starter/Growth/Enterprise), with realistic churn, expansion, and
  contraction events mixed in.

## Columns
| column | meaning |
|---|---|
| customer_id | unique customer id |
| plan | Starter / Growth / Enterprise |
| mrr | monthly recurring revenue at signup |
| start_date | subscription start date |
| end_date | churn date (blank if still active) |
| plan_change_date | date of an upgrade/downgrade (blank if none) |
| plan_change_mrr | new MRR after the plan change (blank if none) |

Note: a customer could churn *and* have had a plan change earlier —
that's realistic and worth handling deliberately, not ignoring.

## How to run this session

1. Open a terminal, `cd` into this folder.
2. Run `claude` to start a session.
3. Paste this as your first prompt:

```
I have a CSV called subscriptions.csv with columns: customer_id, plan,
mrr, start_date, end_date, plan_change_date, plan_change_mrr.

Write a Python script using pandas that builds a monthly ARR waterfall
from Jan 2025 to Jun 2026:
- Starting ARR
- New ARR (new customers who started that month)
- Expansion ARR (plan_change_mrr increases)
- Contraction ARR (plan_change_mrr decreases)
- Churned ARR (customers whose end_date falls in that month)
- Ending ARR

Output a clean CSV (monthly_waterfall.csv) and print a summary table
to the terminal. Also print a sanity check: does starting ARR + new +
expansion - contraction - churn actually equal ending ARR each month?
```

4. Let it read the file, write the script, and **run it**. Watch what
   it does when the sanity check fails on the first try (it likely will
   — waterfall logic has edge cases) and see how it debugs itself.

## Good follow-up prompts once it works
- "Break the waterfall out by plan tier instead of totals."
- "Now calculate net revenue retention (NRR) by month from this data."
- "Chart ARR by month with a stacked bar for new/expansion vs a line
  for churn, save as a PNG."
- "Write a CLAUDE.md for this project so next month I can just drop in
  a new subscriptions.csv and ask you to rerun it."

## What to watch for as you learn
- Does it ask before overwriting files, or just do it?
- When the numbers don't tie out, does it explain *why* before fixing,
  or just patch until the check passes? (Push it to explain — that's
  the muscle you want it to build with you.)
- Try `/clear` after this session finishes, then reopen and ask "what
  does this project do?" — see how much it picks up from CLAUDE.md
  alone.
