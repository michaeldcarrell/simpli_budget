-- Alerts when a bank login needs re-authenticating in Plaid (ITEM_LOGIN_REQUIRED). The Airflow plaid_nightly_refresh
-- DAG stamps login_required_at the first time a login fails that way, alerts the group's members, and clears it on
-- the next successful sync; relinking in the app clears it too (PlaidPublicTokenExchangeAPI in api/views.py).
-- Like the rest of the schema, this is managed outside Django: run it by hand against the simplibudget database.

ALTER TABLE plaid.access_tokens ADD COLUMN IF NOT EXISTS login_required_at TIMESTAMPTZ;

ALTER TABLE public.user_attributes ADD COLUMN IF NOT EXISTS bank_login_alerts_enabled BOOLEAN NOT NULL DEFAULT true;
