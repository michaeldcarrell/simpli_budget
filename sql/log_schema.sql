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

-- Budget assistant conversations (see ChatAPI in api/views.py). Every message is kept here; only a recent
-- window of an active session is sent back to the model (helpers/chat.py: context_messages).
CREATE TABLE IF NOT EXISTS log.chat_session (
    chat_session_id BIGSERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES public.auth_user (id) ON DELETE CASCADE,
    group_id        INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Set by "New chat"; a session idle longer than CHAT_SESSION_IDLE is also treated as over.
    ended_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS chat_session_user_group_idx ON log.chat_session (user_id, group_id, last_message_at DESC);

CREATE TABLE IF NOT EXISTS log.chat_message (
    chat_message_id BIGSERIAL PRIMARY KEY,
    chat_session_id BIGINT NOT NULL REFERENCES log.chat_session (chat_session_id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    -- The page the user was on when asking (user messages only).
    page            JSONB,
    -- Tool names the assistant called for this answer (assistant messages only).
    tools_used      JSONB,
    -- Set when the answer failed or was cut off; such turns are shown but never sent back to the model.
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chat_message_session_idx ON log.chat_message (chat_session_id, chat_message_id);
