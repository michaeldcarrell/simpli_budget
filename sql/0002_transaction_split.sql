-- 0002_transaction_split.sql
-- Database: simplibudget (and simplibudget_dev)
-- Purpose:  BUDGET-1, split one transaction across several categories.
--           budget.transaction_split holds only the *extra* lines of a split; the
--           transaction's own category_id gets the remainder (amount - sum(lines)),
--           so the lines always add up to the transaction total.
--           budget.transaction_allocation expands every live transaction into
--           its category shares. Anything that totals money by category reads it.
--           transaction_search and carrell.vw_monthly_budget are rebuilt on top of
--           it. Existing columns are unchanged (new ones are appended), so the
--           currently deployed app keeps working.
-- Checked:  2026-11-22: budget.transaction_split / transaction_allocation absent;
--           views owned by michael (db owner); 21342 transactions, none with a
--           null amount or date; no account with deleted IS NULL (so the
--           COALESCE in the new views matches vw_monthly_budget's old NOT a.deleted).
-- Run:      ~/apps/dev_tools/run-sql simpli_budget dev  sql/0002_transaction_split.sql
--           ~/apps/dev_tools/run-sql simpli_budget prod sql/0002_transaction_split.sql   (after testing on dev, before deploying the app)
-- Undo:     restore the two old view definitions (see git history of this file's
--           header / pg_get_viewdef before running), then
--           DROP VIEW budget.transaction_allocation; DROP TABLE budget.transaction_split;
--           (DROP TABLE loses any splits users have made.)

BEGIN;

SET LOCAL ROLE :"owner";         -- run-sql passes the db owner: michael (prod) / app_dev (dev)
SET LOCAL lock_timeout = '5s';   -- fail fast instead of blocking the live app

INSERT INTO public.schema_migrations (filename) VALUES ('0002_transaction_split.sql');

DO $$
BEGIN
    IF to_regclass('budget.transaction_split') IS NOT NULL
       OR to_regclass('budget.transaction_allocation') IS NOT NULL THEN
        RAISE EXCEPTION 'preflight failed: budget.transaction_split or budget.transaction_allocation already exists';
    END IF;
END $$;

-- 1. Extra split lines -------------------------------------------------------

CREATE TABLE budget.transaction_split (
    transaction_split_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_id       varchar(64) NOT NULL
                         REFERENCES plaid.transactions (transaction_id) ON DELETE CASCADE ON UPDATE CASCADE,
    category_id          integer NOT NULL REFERENCES budget.categories (category_id),
    amount               money NOT NULL CHECK (amount <> 0::money),
    sort_index           integer NOT NULL DEFAULT 0,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT transaction_split_unique_category UNIQUE (transaction_id, category_id)
);
CREATE INDEX transaction_split_category_idx ON budget.transaction_split (category_id);
COMMENT ON TABLE budget.transaction_split IS
    'Extra category lines of a split transaction (BUDGET-1). The transaction''s own category_id '
    'gets the remainder; read budget.transaction_allocation for per-category amounts.';

-- 2. Every live transaction's category shares -------------------------------

CREATE VIEW budget.transaction_allocation AS
WITH split_totals AS (
    SELECT s.transaction_id, sum(s.amount) AS split_amount
    FROM budget.transaction_split s
    GROUP BY s.transaction_id
)
-- The remainder (or the whole amount, for an unsplit transaction) on the transaction's own category.
SELECT t.transaction_id || ':r'                       AS allocation_id,
       t.transaction_id,
       NULL::integer                                   AS transaction_split_id,
       t.category_id,
       t.amount - COALESCE(st.split_amount, 0::money)  AS amount,
       t.date,
       t.account_id,
       a.group_id,
       st.transaction_id IS NOT NULL                   AS is_split,
       true                                            AS is_remainder
FROM plaid.transactions t
JOIN plaid.accounts a ON a.account_id = t.account_id
LEFT JOIN split_totals st ON st.transaction_id = t.transaction_id
WHERE NOT COALESCE(t.deleted, false)
  AND NOT COALESCE(a.deleted, false)
  AND (st.transaction_id IS NULL OR t.amount <> st.split_amount)
UNION ALL
-- One row per extra split line.
SELECT t.transaction_id || ':' || s.transaction_split_id,
       t.transaction_id,
       s.transaction_split_id,
       s.category_id,
       s.amount,
       t.date,
       t.account_id,
       a.group_id,
       true,
       false
FROM budget.transaction_split s
JOIN plaid.transactions t ON t.transaction_id = s.transaction_id
JOIN plaid.accounts a ON a.account_id = t.account_id
WHERE NOT COALESCE(t.deleted, false)
  AND NOT COALESCE(a.deleted, false);
COMMENT ON VIEW budget.transaction_allocation IS
    'Each live transaction expanded into its category shares: one remainder row on the transaction''s '
    'category (dropped when a split leaves it at $0) plus one row per budget.transaction_split line. '
    'Sum this, not plaid.transactions, for money by category.';

-- 3. Search: still one row per transaction, plus every allocated category ---

CREATE OR REPLACE VIEW budget.transaction_search AS
WITH transaction_tags AS (
    SELECT tt_1.transaction_id,
           string_agg(t_1.name::text, ', '::text) AS tags
    FROM budget.transaction_tag tt_1
    JOIN budget.tag t_1 ON tt_1.tag_id = t_1.tag_id
    GROUP BY tt_1.transaction_id
), allocation_categories AS (
    SELECT al.transaction_id,
           array_agg(al.category_id ORDER BY al.is_remainder DESC, al.transaction_split_id) AS category_ids,
           string_agg(c_1.category_name::text, ', ' ORDER BY al.is_remainder DESC, al.transaction_split_id) AS category_names,
           count(*) FILTER (WHERE NOT al.is_remainder)::integer AS split_count
    FROM budget.transaction_allocation al
    JOIN budget.categories c_1 ON c_1.category_id = al.category_id
    GROUP BY al.transaction_id
)
SELECT t.transaction_id,
       a.group_id,
       c.category_id,
       a.account_id,
       t.date,
       t.name,
       t.amount,
       a.name AS account,
       c.category_name AS category,
       tt.tags,
       COALESCE(ac.category_ids, ARRAY[c.category_id]) AS category_ids,
       COALESCE(ac.category_names, c.category_name::text) AS category_names,
       COALESCE(ac.split_count, 0) AS split_count
FROM plaid.transactions t
JOIN plaid.accounts a ON a.account_id::text = t.account_id::text
JOIN budget.categories c ON c.category_id = t.category_id
LEFT JOIN transaction_tags tt ON tt.transaction_id::text = t.transaction_id::text
LEFT JOIN allocation_categories ac ON ac.transaction_id = t.transaction_id
WHERE NOT COALESCE(t.deleted, false) AND NOT COALESCE(a.deleted, false);

-- 4. Monthly budget (Google Sheet + summary email): sum allocations ---------

CREATE OR REPLACE VIEW carrell.vw_monthly_budget AS
WITH months AS (
    SELECT DISTINCT d.year_month,
           (d.month_name_short || '-'::text) || d.year AS month
    FROM date d
), category_months AS (
    SELECT m.year_month,
           m.month,
           c_1.category_id,
           ct_1.category_type_id,
           ct_1.invert_amounts
    FROM months m
    CROSS JOIN budget.categories c_1
    JOIN budget.category_type ct_1 ON ct_1.category_type_id = c_1.category_type_id
    WHERE ct_1.group_id = 1
), year_month_transactions AS (
    SELECT d.year_month,
           al.category_id,
           sum(
               CASE
                   WHEN ct_1.invert_amounts = false THEN al.amount
                   ELSE al.amount * '-1'::integer
               END)::numeric AS monthly_total
    FROM budget.transaction_allocation al
    JOIN budget.categories c_1 ON c_1.category_id = al.category_id
    JOIN budget.category_type ct_1 ON ct_1.category_type_id = c_1.category_type_id
    JOIN date d ON d.date = al.date
    GROUP BY al.category_id, d.year_month
), monthly_category_amounts AS (
    SELECT cm.category_id,
           cm.year_month,
           cm.month,
           COALESCE(ymt.monthly_total, 0::numeric) AS monthly_total
    FROM category_months cm
    LEFT JOIN year_month_transactions ymt ON ymt.year_month = cm.year_month AND ymt.category_id = cm.category_id
)
SELECT c.category_id,
       c.sort_index AS category_sort_index,
       ct.sort_index AS category_type_sort_index,
       ct.category_type_name,
       c.category_name,
       mca.year_month,
       mca.month,
       mca.monthly_total
FROM monthly_category_amounts mca
JOIN budget.categories c ON c.category_id = mca.category_id
JOIN budget.category_type ct ON c.category_type_id = ct.category_type_id;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'claude_ro') THEN
        GRANT SELECT ON budget.transaction_split, budget.transaction_allocation TO claude_ro;
    END IF;
END $$;

-- Verify: with no splits yet, allocations must match transactions exactly.
SELECT (SELECT count(*) FROM budget.transaction_allocation)                    AS allocation_rows,
       (SELECT count(*) FROM budget.transaction_search)                        AS search_rows,
       (SELECT sum(amount) FROM budget.transaction_allocation)                 AS allocation_total,
       (SELECT sum(amount) FROM budget.transaction_search)                     AS search_total;

COMMIT;
