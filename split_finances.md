# Split Finances Project

Living doc for this multi-session effort — read this at the start of any session touching `split_finances`.

## Goal

Michael and Hanna are splitting their budget so each has their own "Spending" category,
while keeping shared categories (bills, utilities, car payments, debt payments, etc.) combined.
Because Michael earns significantly more, a larger share of the combined/shared expenses should
come from his income, so that **leftover discretionary spending money ends up equal** for both.

Income is identified by merchant: Michael's paycheck comes from "Redfin", Hanna's from "Sondermind".

## Requested work

1. Create new DB rows: two `category_type`s — "Michael Expenses" and "Hanna Expenses" — each containing
   one category for now, "Spending". Existing categories/category_types are untouched and keep handling
   combined/shared expenses.
2. Analyze the last several months of transactions to recommend what percentage/amount of the combined
   shared expenses each person should contribute so take-home spending money is equal.

## Environment / access notes

- DB is external GCP Postgres, `managed = False` in Django — no migrations, but plain ORM `INSERT`s work fine.
- Live app container `simpli_budget` is running via Portainer/Docker; read-only inspection was done via
  `docker exec simpli_budget python manage.py shell -c "..."`. Same approach works for future sessions.
- This is a **Pattern B** stack per `../STACK_TOPOLOGY.md` — don't assume editing the repo's compose file
  and redeploying will pick up changes; that's irrelevant here though since this task is pure data, not code.

## Schema facts gathered (2026-09-14)

- Group: `group_id=1`, name "Carrell Budget". Members: `michaeldcarrell@gmail.com` (Michael, default group),
  `hannamarie95@gmail.com` (Hanna, default group), `michael@carrell.us` (not default).
- Existing `CategoryType`s for group 1:
  | id | name | invert_amounts | sort_index | hidden |
  |----|------|-----------------|------------|--------|
  | 0 | Uncategorized | False | 0 | False |
  | -1 | Hidden | False | 0 | True |
  | 1 | Income | True | 1 | False |
  | 2 | Fixed Expenses | False | 2 | False |
  | 3 | Variable Expenses | False | 3 | False |
  | 5 | Goals | False | 4 | False |

  → New types "Michael Expenses" / "Hanna Expenses" should use `invert_amounts=False`, `hidden=False`,
  `sort_index=5` and `6` (next free slots).

- Income is **already** split at the category level, not just by merchant:
  - `category_id=1` "Michael Income" (default $8,738/mo)
  - `category_id=2` "Hanna Income" (default $7,500/mo)
  - `category_id=104` "Investment Payout" (default $0/mo) — ungrouped by person, currently small/unused.
- Combined/shared categories today live under:
  - Fixed Expenses (2): Bills and Utilities, Subscriptions
  - Variable Expenses (3): Shopping, Restaurants, Education, Pets, Travel, Cash & ATM, Gifts & Donations,
    Medical, Fees & Charges, Personal Care, Auto & Transport, Student Loans, Groceries & House Hold, Home,
    Work, Clothes, Amusement
  - Goals (5): Taxes
- There's also a `Hidden` category type (id -1) that swings wildly month to month (large + and - amounts) —
  almost certainly credit card payment transfers, not real spend. **Excluded from the analysis below** to
  avoid double-counting (the underlying purchases already land in Fixed/Variable Expenses).

## Scope clarification (2026-09-14, from Michael)

The shared expense subject to the proportional-contribution split is **only "Bills and Utilities"**
(`category_id=3`), not all of Fixed/Variable Expenses/Goals. Other combined categories (Subscriptions,
Groceries, etc.) stay as shared/combined spending but aren't part of this contribution-ratio calculation.

## Contribution analysis (last 6 complete months: 2026-03 through 2026-08)

Formula: if `M`/`H` = Michael/Hanna monthly income, `E` = Bills and Utilities spend, and `x` = Michael's
dollar contribution toward `E`, solving `M - x = H - (E - x)` for equal leftover spending money gives:

```
x = (M - H + E) / 2
Michael's share of E = x / E
Hanna's share of E   = 1 - x / E
```

| Month | Michael income | Hanna income | Bills and Utilities | Michael's share (that month) |
|-------|----------------|--------------|----------------------|-------------------------------|
| 2026-03 | $8,738.56 | $6,117.00 | $7,039.66 | 68.6% |
| 2026-04 | $13,163.96 | $7,489.00 | $8,766.69 | 82.4% |
| 2026-05 | $12,887.80 | $6,577.00 | $8,193.09 | 88.5% |
| 2026-06 | $8,794.73 | $5,526.00 | $6,888.65 | 73.7% |
| 2026-07 | $8,794.71 | $8,741.00 | $8,670.21 | 50.3% |
| 2026-08 | $12,348.55 | $4,847.00 | $8,747.26 | 92.9% |
| **Avg** | **$10,788.05** | **$6,549.50** | **$8,050.93** | — |

Using the averages: `x = (10788.05 - 6549.50 + 8050.93) / 2 ≈ $6,144.74`

→ **Recommended split: Michael ≈ 76.3%, Hanna ≈ 23.7% of the monthly Bills and Utilities amount.**

This leaves each of them ≈ $4,643/mo in leftover income after Bills and Utilities (income minus their
share of that category) — verified equal both ways (`M - x = H - (E - x)`).

Monthly share varies a fair amount (50–93% Michael) because Michael's income is lumpier month to month
than Hanna's, not because the bill itself varies much (~$6.9k–$8.8k).

**Decision (2026-09-14): fixed 75% Michael / 25% Hanna split on Bills and Utilities**, going forward — not
recomputed monthly. At the ~$8,050.93/mo average, that's roughly **$6,038 Michael / $2,013 Hanna**.

## Status / next steps

- [x] Capture requirements
- [x] Inspect schema, group, existing category types/categories (read-only)
- [x] Pull last several months of transactions, draft contribution formula and preliminary split
- [x] Scope narrowed to Bills and Utilities only; recomputed split (76.3% / 23.7%) — resolves earlier
      income/expense gap since Bills and Utilities alone fits comfortably within combined income
- [x] Decided: fixed 75% Michael / 25% Hanna split on Bills and Utilities, no periodic recompute
- [x] Created `CategoryType` rows "Michael Expenses" (id=16, sort=5) and "Hanna Expenses" (id=17, sort=6),
      each with one `Categories` row "Spending" (id=117 and 118). Default monthly amounts left blank —
      Michael to populate in-app.
- [ ] Decide how/where Michael tracks actual contributions against the split (not necessarily in-app — may
      just be a manual monthly transfer)

## Session log

- 2026-09-14: Initial ask captured. Reviewed `simpli_budget/models.py` schema. Pulled group/category/user
  data and 19 months of transaction aggregates read-only via the running container. Drafted split formula
  and flagged the income/expense gap for follow-up.
- 2026-09-14: Michael clarified scope — split applies only to "Bills and Utilities", not all combined
  categories. Recomputed with that category alone: ≈76.3%/23.7% Michael/Hanna, gap issue resolved.
- 2026-09-14: Created "Michael Expenses" (CategoryType id 16) and "Hanna Expenses" (CategoryType id 17),
  each with a "Spending" category (ids 117, 118). Default monthly amounts intentionally left blank for
  Michael to populate in-app.
- 2026-09-14: Finalized the contribution split at a fixed 75/25 (Michael/Hanna) on Bills and Utilities,
  rather than recomputing periodically.
- 2026-09-14: Reordered `sort_index` so the list reads Income, Fixed Expenses, Michael Expenses,
  Hanna Expenses, Variable Expenses, Goals (was sorting to the bottom). New sort values: Income=1,
  Fixed Expenses=2, Michael Expenses=3, Hanna Expenses=4, Variable Expenses=5, Goals=6.
