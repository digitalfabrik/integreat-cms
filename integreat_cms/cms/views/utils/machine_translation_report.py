"""
This module contains the AJAX call for reading the machine translation
report(s) queued for the current user, region, and content type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.utils.translation import gettext as _

from ....cms.models import MachineTranslationReport

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest


def _object_report_has_failure(object_report: dict[str, Any]) -> bool:
    """
    A per-object entry in the translation report takes one of two shapes:
    ``{"exception": "..."}``, when something raised all the way up through
    the per-object ``try``/``except`` in the Celery task (e.g. an unknown
    provider) - or the shape :func:`~...machine_translation_celery_task._get_language_report`
    returns, when ``translate_queryset()`` returned normally but still
    recorded a failure *internally* (e.g. the API client caught its own
    provider exception via ``mark_unsuccessful()``/``mark_too_long()`` and
    never raised at all). Both must count as a failure here, not just the
    first - otherwise a batch that entirely failed via the second shape
    (e.g. every object hit a DeepL API error) reads as a full success.

    :param object_report: One object's entry in the per-language report
    :return: Whether this object/language actually failed
    """
    if "exception" in object_report:
        return True
    return any(object_report.get("failed", {}).values())


def _get_report_outcome(results: dict[str, dict[str, dict[str, Any]]]) -> str:
    """
    :param results: The per-language, per-object translation report
    :return: "FULL_SUCCESS" if every object/language succeeded, "PARTIAL_SUCCESS"
        if at least one - but not all - failed
    """
    has_failure = any(
        _object_report_has_failure(object_report)
        for language_report in results.values()
        for object_report in language_report.values()
    )
    return "PARTIAL_SUCCESS" if has_failure else "FULL_SUCCESS"


def _get_report_message(outcome: str) -> str:
    """
    :param outcome: The outcome as computed by :func:`_get_report_outcome`
    :return: The full, translated banner text for that outcome. Evaluated
        per-request (not at import time), so this reflects the language
        active for the current request, not whatever was active on import.
    """
    if outcome == "PARTIAL_SUCCESS":
        return _(
            "Machine translation of multiple pages has finished. "
            "Not all pages could be translated."
        )
    return _(
        "Machine translation of multiple pages has finished. "
        "All pages were translated successfully."
    )


def get_machine_translation_report(
    request: HttpRequest,
    region_slug: str,
    language_slug: str,
    model_type: str,
) -> JsonResponse:
    """
    Report the machine translation report(s) queued for the current user,
    region, and content type, if any - a destructive read, so each report is
    only ever returned once, to whoever triggered the translation.

    :param request: The current request
    :param region_slug: The slug of the current region
    :param language_slug: The slug of the current language (unused, kept for
        URL consistency with the other machine translation AJAX endpoints)
    :param model_type: The content type the reports concern (e.g. "page")
    :return: A JSON object containing the queued reports, if any
    """
    if not request.user.has_perm(f"cms.view_{model_type}"):
        raise PermissionDenied

    with transaction.atomic():
        reports_qs = MachineTranslationReport.objects.select_for_update().filter(
            user_id=request.user.id,
            region_id=request.region.id,
            content_type=model_type,
        )
        reports = list(reports_qs)
        reports_qs.delete()

    return JsonResponse(
        {
            "reports": [
                {
                    "language_slugs": report.language_slugs,
                    "results": report.results,
                    "outcome": (outcome := _get_report_outcome(report.results)),
                    "message": _get_report_message(outcome),
                }
                for report in reports
            ]
        }
    )
