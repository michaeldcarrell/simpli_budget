import json
import logging
import time
from types import SimpleNamespace

from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpResponseForbidden, JsonResponse

from simpli_budget.models import ApiEvent, UserAttributes, get_user_group, is_demo_user

logger = logging.getLogger(__name__)


class SetUserAttributeDefaults:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not UserAttributes.objects.filter(
                user=request.user
            ).exists():
                UserAttributes.objects.create(
                    user=request.user,
                    show_hidden=False
                )
        return self.get_response(request)


DEMO_READ_ONLY_MESSAGE = "This is a read-only demo, so changes aren't saved. Sign in with Google to use your own budget."


class DemoReadOnly:
    """
    Rejects every write from the demo user, so new endpoints are read-only for it by default.
    The exceptions are requests that only look like writes: the transaction search is a POST, and the
    theme/onboarding endpoints keep the demo user's choices in its session rather than the database.
    """
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
    ALLOWED_WRITES = (
        ('POST', '/api/transactions'),
        ('PUT', '/api/settings'),
        ('POST', '/api/onboarding/complete'),
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method not in self.SAFE_METHODS
            and (request.method, request.path) not in self.ALLOWED_WRITES
            and is_demo_user(request.user)
        ):
            if request.path.startswith('/api/'):
                return JsonResponse({'message': DEMO_READ_ONLY_MESSAGE}, status=403)
            return HttpResponseForbidden(DEMO_READ_ONLY_MESSAGE)
        return self.get_response(request)


class ApiEventLog:
    """
    Records every write made through the JSON API in log.api_event, so there's a history of who changed what.
    POSTs that only read (the transaction search and chat) are skipped, as are the demo user and anonymous
    requests. Logging never fails the request: errors are logged and swallowed.
    """
    WRITE_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')
    READ_ONLY_POSTS = ('/api/transactions', '/api/chat')
    REDACTED_KEYS = ('token', 'secret', 'password')
    MAX_BODY_CHARS = 16_000

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_log(request):
            return self.get_response(request)

        # Read the body before the view does: Django caches it, whereas a multipart stream can only be read once.
        request_body = self._request_body(request)
        started = time.monotonic()
        response = self.get_response(request)
        try:
            self._record(request, request_body, response, round((time.monotonic() - started) * 1000))
        except Exception:
            logger.exception('Failed to record API event for %s %s', request.method, request.path)
        return response

    def _should_log(self, request) -> bool:
        return (
            request.method in self.WRITE_METHODS
            and request.path.startswith('/api/')
            and request.path not in self.READ_ONLY_POSTS
            and request.user.is_authenticated
            and not is_demo_user(request.user)
        )

    def _request_body(self, request):
        if request.content_type != 'application/json' or not request.body:
            return None
        try:
            return json.loads(request.body)
        except ValueError:
            return None

    def _record(self, request, request_body, response, duration_ms: int):
        match = request.resolver_match
        ApiEvent.objects.create(
            user=request.user,
            group_id=self._group_id(request, request_body),
            method=request.method,
            path=request.path,
            view_name=match.view_name if match else None,
            url_kwargs=self._clean(match.kwargs) if match and match.kwargs else None,
            query_params=self._clean(request.GET.dict()) or None,
            request_body=self._clean(request_body),
            status_code=response.status_code,
            response_body=self._clean(getattr(response, 'data', None)),
            duration_ms=duration_ms,
        )

    def _group_id(self, request, request_body):
        shim = SimpleNamespace(GET=request.GET, data=request_body if isinstance(request_body, dict) else None)
        try:
            return get_user_group(request.user, shim).group_id
        except Http404:
            return None

    def _clean(self, value):
        """JSON-safe copy of value with token-like keys redacted, or a stub if it's too large to be worth keeping."""
        if value is None:
            return None
        cleaned = json.loads(json.dumps(self._redact(value), cls=DjangoJSONEncoder))
        size = len(json.dumps(cleaned))
        if size > self.MAX_BODY_CHARS:
            return {'truncated': True, 'size': size}
        return cleaned

    def _redact(self, value):
        if isinstance(value, dict):
            return {
                key: '[redacted]' if any(word in str(key).lower() for word in self.REDACTED_KEYS) else self._redact(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self._redact(item) for item in value]
        return value
