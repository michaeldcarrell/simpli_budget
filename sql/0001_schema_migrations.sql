-- 0001_schema_migrations.sql
-- Database: simplibudget (and simplibudget_dev, which is copied from it)
-- Purpose:  Record which numbered sql/ files each database has had applied, so
--           dev and prod can be compared (~/apps/dev_tools/migration-status).
--           The older unnumbered files in sql/ predate this and aren't tracked.
-- Checked:  2026-11-21: public.schema_migrations absent; schema public exists.
-- Run:      ~/apps/dev_tools/run-sql --skip-dev-check simpli_budget prod sql/0001_schema_migrations.sql
--           One-time exception to "dev first": the dev database doesn't exist
--           yet and is created from prod afterwards (dev_tools/setup.sh).
-- Undo:     DROP TABLE public.schema_migrations;

BEGIN;

SET LOCAL ROLE :"owner";          -- run-sql passes the database owner (michael / app_dev)
SET LOCAL lock_timeout = '5s';

DO $$
BEGIN
    IF to_regclass('public.schema_migrations') IS NOT NULL THEN
        RAISE EXCEPTION 'already applied: public.schema_migrations exists';
    END IF;
END $$;

CREATE TABLE public.schema_migrations (
    filename   text PRIMARY KEY CHECK (filename ~ '^[0-9]{4}_[a-z0-9_]+\.sql$'),
    applied_at timestamptz NOT NULL DEFAULT now(),
    applied_by text NOT NULL DEFAULT session_user
);
COMMENT ON TABLE public.schema_migrations IS
    'Numbered sql/ files applied to this database. Each file inserts its own row; see ~/apps/DEV_ENVIRONMENT.md';

INSERT INTO public.schema_migrations (filename) VALUES ('0001_schema_migrations.sql');

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'claude_ro') THEN
        GRANT SELECT ON public.schema_migrations TO claude_ro;
    END IF;
END $$;

SELECT filename, applied_by FROM public.schema_migrations ORDER BY 1;

COMMIT;
