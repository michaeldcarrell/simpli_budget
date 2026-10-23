-- Whether a user's notification summary includes the PTO fund (helpers/pto.py) of each group they belong to that has
-- one; read by the Airflow budget_category_summary DAG (classes/budget/pto.py).
-- Like the rest of the schema, this is managed outside Django: run it by hand against the simplibudget database.

ALTER TABLE public.user_attributes ADD COLUMN IF NOT EXISTS pto_notifications_enabled BOOLEAN NOT NULL DEFAULT false;
