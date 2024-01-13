"""
This file contains the helper function to change the publication status of translations
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from ...constants import status
from ...models import Language
from ...utils.stringify_list import iter_to_string

if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from django.http import HttpRequest


def change_publication_status(
    request: HttpRequest,
    selected_content: QuerySet,
    language_slug: str,
    desired_status: str,
) -> None:
    """
    Helper function to change the publication status

    :param request: The current request
    :param selected_content: The current queryset
    :param language_slug: The language slug of the current language
    :param desired_status: The desired status
    """

    successful = []
    unchanged = []
    failed = []

    if request.user.is_superuser or request.user.is_staff:
        for content in selected_content:
            if translation := content.get_translation(language_slug):
                if translation.status == desired_status:
                    unchanged.append(translation.title)
                else:
                    translation.links.all().delete()
                    translation.status = desired_status
                    translation.pk = None
                    translation.version += 1
                    if desired_status == status.DRAFT:
                        translation.all_versions.filter(status=status.PUBLIC).update(
                            status=status.DRAFT
                        )
                    translation.save()
                    successful.append(translation.title)
            else:
                failed.append(content.best_translation.title)

    if selected_content:
        meta = type(selected_content[0])._meta
        model_name = meta.verbose_name.title()
        model_name_plural = meta.verbose_name_plural.title()
    else:
        model_name = model_name_plural = ""

    changed_status = dict(status.CHOICES).get(desired_status)

    if successful:
        messages.success(
            request,
            ngettext_lazy(
                'The publication status of {model_name} {object_names} was successfully changed to "{changed_status}".',
                'The publication status of the following {model_name_plural} was successfully changed to "{changed_status}": {object_names}',
                len(successful),
            ).format(
                model_name=model_name,
                model_name_plural=model_name_plural,
                changed_status=changed_status,
                object_names=iter_to_string(successful),
            ),
        )

    if unchanged:
        messages.info(
            request,
            ngettext_lazy(
                'The publication status of {model_name} {object_names} is already "{changed_status}".',
                'The publication status of the following {model_name_plural} is already "{changed_status}": {object_names}',
                len(unchanged),
            ).format(
                model_name=model_name,
                model_name_plural=model_name_plural,
                changed_status=changed_status,
                object_names=iter_to_string(unchanged),
            ),
        )

    if failed:
        messages.warning(
            request,
            ngettext_lazy(
                'The publication status of {model_name} {object_names} could not be changed to "{changed_status}", because it has no translation in {language}.',
                'The publication status of the following {model_name_plural} could not be changed to "{changed_status}", because they don\'t have a translation in {language}: {object_names}',
                len(failed),
            ).format(
                model_name=model_name,
                model_name_plural=model_name_plural,
                changed_status=changed_status,
                language=Language.objects.filter(slug=language_slug).first(),
                object_names=iter_to_string(failed),
            ),
        )
