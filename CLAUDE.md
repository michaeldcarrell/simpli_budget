# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Simpli Budget is a personal, multi-user budgeting app: Django server-rendered templates + vanilla JS on the frontend, a small DRF JSON API for AJAX calls, and Postgres (hosted on GCP, not local) for storage. Plaid is used to pull bank account/transaction data.

## Commands

Setup:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # NOTE: this file is UTF-16 encoded; a plain `pip install -r requirements.txt` works fine, but tools that assume UTF-8 (e.g. some editors/linters) may choke on it
```

Required env vars (loaded via `python-decouple`, typically from a `.env` file — see `simpli_budget/settings.py`):
- `SECRET_KEY`
- `CBA_LAMBDA_KEY`
- `PLAID_SECRET`
- `CBA_POSTGRES_DB_PASS`
- `DEBUG` (optional, defaults to `True`)

Run the dev server:
```bash
python manage.py runserver
```

Run tests (Django's test runner; `api/tests.py` is currently an empty stub, no real test suite exists yet):
```bash
python manage.py test
python manage.py test api.tests.SomeTestCase.test_something   # single test
```

There is no configured linter/formatter and no JS build step (static JS is hand-written, served as-is).

Production runs via gunicorn (`Procfile`): `gunicorn simpli_budget.wsgi`.

## Architecture

### Two Django apps
- `simpli_budget/` — the main app: models, page views (`simpli_budget/views/`), templates, auth glue. `simpli_budget/urls.py` is the root URLconf, mounting page routes plus `accounts/` (allauth) and `api/` (see below).
- `api/` — a thin DRF app. `api/views.py` holds all `APIView` JSON endpoints consumed by page-specific JS in `static/<feature>/js/`; `api/urls.py` is mounted at `/api/`. `api/models.py` is unused (empty stub) — all real models live in `simpli_budget/models.py`.

### The database is external and unmanaged
Every model in `simpli_budget/models.py` sets `Meta.managed = False` and points at tables that already exist in a shared Postgres instance, split across schemas: `budget` (groups, categories, category_types, category_month, tag), `plaid` (accounts, access_tokens, transactions), and `rule` (rule sets, rules, match types). **There are no Django migrations for this schema** — changes to these tables happen outside Django (they're managed elsewhere), so adding a field means it must already exist in the DB before the model can use it.

Money columns are stored as `TEXT` in Postgres (e.g. `_amount`, `_balance`, `default_monthly_amount`) and Django models expose them through `@property` accessors (`amount`, `balance`, `default_monthly_amount`) that run them through `money_as_float`/`money_display` helpers at the top of `models.py`. Don't read the underscored raw fields directly in new code — use the property.

`TransactionSearch` (`simpli_budget/models.py`) maps to a Postgres view (`budget.transaction_search`) that pre-joins transaction/account/category/tag data for the paginated search API (`api/views.py: TransactionsAPI`) — it's read-only and denormalized specifically to make that filtering/ordering fast.

### Multi-tenancy via Group
Every user belongs to one or more `Group`s through `GroupUser` (one row has `user_default_group=True` to mark the user's default). Nearly every domain model (`Categories`, `Accounts`, `Transactions`, `Tag`, `RuleSet`, `Rule`, `AccessTokens`, etc.) implements `user_has_access(user)`, which checks `GroupUser` membership on that record's group (directly or via a parent FK chain). **Every view/API endpoint that fetches a record by ID must call `user_has_access` before returning/mutating it** — this is the app's only authorization mechanism, there's no per-object Django permission system. Follow the existing pattern in `api/views.py` (fetch by id → check `user_has_access` → 404 with a generic "not found" message if it fails, to avoid leaking existence of other groups' records) when adding new endpoints.

`get_user_group(user, request)` in `models.py` resolves "the current group" for a request: it starts from the user's default group, then lets a `group_id` query param or POST body field override it (used for multi-group support in views).

### Auth
Google-only social login via django-allauth: `SOCIALACCOUNT_ONLY = True` and `CustomAccountAdapter.is_open_for_signup` returns `False` (`simpli_budget/adapter.py`), so there's no username/password signup path. `CustomSocialAccountAdapter.pre_social_login` links a Google login to an existing `User` by email instead of creating a duplicate. Page views use `LoginRequiredMixin`; API views use DRF `SessionAuthentication` + `IsAuthenticated`.

`SetUserAttributeDefaults` middleware (`simpli_budget/middleware.py`) lazily creates a `UserAttributes` row (currently just a `show_hidden` category-visibility preference) the first time an authenticated user is seen.

### Budget aggregation helpers
`Month`, `CategoryTypeMonth`, and `BudgetMonth` in `models.py` are plain Python classes (not Django models) that assemble the month-overview page: `year_month` is an integer in `YYYYMM` form; `Month` looks up calendar metadata from the `Date` model (a pre-populated date-dimension table); `BudgetMonth` walks `CategoryType` → `CategoryMonth` → `Transactions` to compute per-category and net income/expense totals for a given month, applying `invert_amounts` per category type (income categories are stored/inverted differently from expenses).

### Plaid integration
`helpers/plaid.py` wraps two Plaid production endpoints (`/link/token/create`, `/item/public_token/exchange`) — hardcoded to `https://production.plaid.com`, not the sandbox. Used by `api/views.py` (`PlaidLinkTokenAPI`, `PlaidPublicTokenExchangeAPI`) and the accounts page views to support linking/relinking bank accounts.

### Frontend
No JS framework or bundler — each feature has a plain JS file under `static/<feature>/js/` that calls the `api/` endpoints directly (fetch/XHR) and manipulates the DOM. Templates live under `templates/<feature>/` and extend `templates/_layout.html`.

### Surrounding infrastructure (outside this repo)
This app is one piece of a larger personal-infra setup, which matters when reasoning about where data comes from or where a job should live:
- **Heroku** hosts only this Django app (`Procfile` → gunicorn), chosen purely for uptime/networking convenience — it is not where the rest of the system runs.
- **Google Cloud** hosts the Postgres database this app reads/writes, as a managed database service — not on the home server (see "The database is external and unmanaged" above for why it's external and unmigrated from here). A future migration of the database to the home server is possible but hasn't happened yet.
- **A home server** runs the other services in this ecosystem, including Airflow.
- **Airflow on the home server** runs the scheduled jobs that keep data current — e.g. pulling new Plaid transactions into the DB. Those jobs are custom Python scripts living outside this repo, not Django management commands. This repo has no Celery/cron/task-queue infrastructure of its own and isn't expected to grow one; new recurring/background work belongs in an Airflow DAG on the home server, not in this codebase.
