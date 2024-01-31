"""
This file contains the helper function to change the translation file
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from ...constants import status
from ...models import Language

if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from django.http import HttpRequest


def change_translation_status(
    request: HttpRequest,
    selected_content: QuerySet,
    language_slug: str,
    desired_status: str,
) -> None:
    """
    Helper function to change the translation status

    :param request: The current request
    :param selected_content: The current queryset
    :param language_slug: The language slug of the current language
    :param desired_status: The desired status
    """

    status_translation = {"PUBLIC": "Published", "DRAFT": "Draft"}

    if request.user.is_superuser or request.user.is_staff:
        for content in selected_content:
            if translation := content.get_translation(language_slug):
                translation.status = desired_status
                translation.pk = None
                translation.version += 1
                if desired_status == status.DRAFT:
                    translation.all_versions.update(status=desired_status)
                translation.save()
                messages.success(
                    request,
                    _('The status of "{}" was successfully changed to "{}".').format(
                        translation, _(status_translation[desired_status])
                    ),
                )
            else:
                language = Language.objects.filter(slug=language_slug).first()
                messages.warning(
                    request,
                    _(
                        'There is no translation for "{}" in {}. No change has been made.'
                    ).format(content.best_translation, language),
                )
