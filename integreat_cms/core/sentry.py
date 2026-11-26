"""
Sentry error reporting and performance tracing

Sentry is initialized separately in each entry point (WSGI, ASGI, Celery worker, Celery beat), so every event carries
a ``component`` tag which tells which kind of process it came from.
"""

from __future__ import annotations

import sentry_sdk
from django.conf import settings
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from integreat_cms import __version__

#: The environments in which errors are reported to Sentry
_SENTRY_ENVIRONMENTS: tuple[str, ...] = ("production", "staging")


def init_sentry(component: str) -> None:
    """
    Initialize Sentry once per process and tag all events with the given component.

    This function is idempotent, so it is safe to call it on every request.

    :param component: The kind of process, e.g. ``"django"`` or ``"celery-worker"``
    """
    if (
        settings.ENVIRONMENT in _SENTRY_ENVIRONMENTS
    ) and not sentry_sdk.get_client().is_active():
        sentry_sdk.init(
            dsn=settings.SENTRY_CMS_DSN,
            environment=settings.ENVIRONMENT,
            release=f"integreat-cms@{__version__}",
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=False,
            integrations=[DjangoIntegration(), CeleryIntegration()],
        )

    # Use the global scope instead of the isolation scope (``sentry_sdk.set_tag()``), because the isolation scope is
    # not shared with new threads or forked per request, while the global scope applies to all events of this process
    # and is inherited by the forked Celery pool processes.
    sentry_sdk.get_global_scope().set_tag("component", component)
