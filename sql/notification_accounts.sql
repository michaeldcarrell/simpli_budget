-- Accounts whose balance a user wants in their notification summary (see NotificationAccountAPI in api/views.py),
-- read by the Airflow budget_category_summary DAG alongside notification_categories.
-- Like the rest of the schema, this is managed outside Django: run it by hand against the simplibudget database.

CREATE TABLE IF NOT EXISTS public.notification_accounts (
    notification_account_id SERIAL PRIMARY KEY,
    user_id                 INTEGER NOT NULL REFERENCES public.user_attributes (user_id) ON DELETE CASCADE,
    account_id              VARCHAR(64) NOT NULL REFERENCES plaid.accounts (account_id) ON DELETE CASCADE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, account_id)
);
