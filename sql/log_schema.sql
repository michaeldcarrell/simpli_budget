-- Audit log of every write made through the app's JSON API (see ApiEventLog in simpli_budget/middleware.py).
-- Like the rest of the schema, this is managed outside Django: run it by hand against the simplibudget database.

CREATE SCHEMA IF NOT EXISTS log;

CREATE TABLE IF NOT EXISTS log.api_event (
    api_event_id  BIGSERIAL PRIMARY KEY,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id       INTEGER REFERENCES public.auth_user (id) ON DELETE SET NULL,
    -- The group the request acted on: an explicit group_id param/field, else the user's default group.
    -- Endpoints that act on a record by id (e.g. /api/category/105) don't pass one, so check url_kwargs too.
    group_id      INTEGER,
    method        TEXT NOT NULL,
    path          TEXT NOT NULL,
    view_name     TEXT,
    url_kwargs    JSONB,
    query_params  JSONB,
    request_body  JSONB,
    status_code   SMALLINT NOT NULL,
    response_body JSONB,
    duration_ms   INTEGER
);

CREATE INDEX IF NOT EXISTS api_event_group_created_idx ON log.api_event (group_id, created_at DESC);
CREATE INDEX IF NOT EXISTS api_event_user_created_idx ON log.api_event (user_id, created_at DESC);

COMMENT ON TABLE log.api_event IS 'One row per POST/PUT/PATCH/DELETE to /api/, written by the Django ApiEventLog middleware. Token-like keys are redacted.';
