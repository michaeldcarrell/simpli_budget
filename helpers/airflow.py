"""
Manual transaction refresh: triggers the Plaid sync DAG on the home server's Airflow through its REST API
(Airflow 3, /api/v2). The DAG refreshes every linked bank login, not just the requesting group's.
"""
import time

import requests
from django.conf import settings

from simpli_budget.models import is_demo_user

TIMEOUT_SECONDS = 10
# Airflow's API tokens last a day by default; fetch a new one well before that.
TOKEN_MAX_AGE_SECONDS = 15 * 60
ACTIVE_STATES = ('queued', 'running')

_token = {'value': None, 'fetched_at': 0.0}


class AirflowError(Exception):
    pass


def refresh_allowed(user, group) -> bool:
    """The refresh button is only offered to members of the groups listed in settings.REFRESH_GROUP_IDS."""
    return (
        group is not None
        and not is_demo_user(user)
        and bool(settings.AIRFLOW_API_URL)
        and group.group_id in settings.REFRESH_GROUP_IDS
        and group.user_has_access(user)
    )


def _headers() -> dict:
    if _token['value'] is None or time.monotonic() - _token['fetched_at'] > TOKEN_MAX_AGE_SECONDS:
        response = _request('POST', '/auth/token', auth=False, json={
            'username': settings.AIRFLOW_API_USERNAME,
            'password': settings.AIRFLOW_API_PASSWORD,
        })
        _token['value'] = response.json()['access_token']
        _token['fetched_at'] = time.monotonic()
    return {'Authorization': f"Bearer {_token['value']}"}


def _request(method: str, path: str, auth: bool = True, **kwargs) -> requests.Response:
    try:
        response = requests.request(
            method,
            f'{settings.AIRFLOW_API_URL.rstrip("/")}{path}',
            headers=_headers() if auth else None,
            timeout=TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as e:
        raise AirflowError(f'Airflow is unreachable: {e}') from e
    if response.status_code == 401 and auth:
        _token['value'] = None  # expired or revoked; the next call logs in again
    if not response.ok:
        raise AirflowError(f'Airflow returned {response.status_code} for {method} {path}')
    return response


def _run_status(run: dict | None) -> dict:
    if run is None:
        return {'state': None, 'manual': False, 'started_at': None, 'finished_at': None, 'active': False}
    return {
        'state': run['state'],
        'manual': run['run_type'] == 'manual',
        'started_at': run.get('start_date') or run.get('queued_at'),
        'finished_at': run.get('end_date'),
        'active': run['state'] in ACTIVE_STATES,
    }


def latest_refresh() -> dict:
    """The most recent run of the refresh DAG, scheduled or manual."""
    runs = _request(
        'GET',
        f'/api/v2/dags/{settings.AIRFLOW_REFRESH_DAG_ID}/dagRuns',
        params={'order_by': '-run_after', 'limit': 1},
    ).json()['dag_runs']
    return _run_status(runs[0] if runs else None)


def trigger_refresh(user) -> dict:
    run = _request('POST', f'/api/v2/dags/{settings.AIRFLOW_REFRESH_DAG_ID}/dagRuns', json={
        'logical_date': None,
        'note': f'Triggered from Simpli Budget by {user.email or user.username}',
    }).json()
    return _run_status(run)
