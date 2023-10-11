from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import ImprintTranslationForm
from ...models import ImprintPage, Language
from ..media.media_context_mixin import MediaContextMixin
from .imprint_context_mixin import ImprintContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_imprintpage"), name="dispatch")
@method_decorator(permission_required("cms.change_imprintpage"), name="post")
class ImprintSideBySideView(TemplateView, ImprintContextMixin, MediaContextMixin):
    """
    View for the imprint side by side form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "imprint/imprint_sbs.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "back_url": reverse(
                    "dashboard",
                    kwargs={
                        "region_slug": kwargs["region_slug"],
                    },
                )
            }
        )
        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render :class:`~integreat_cms.cms.forms.imprint.imprint_translation_form.ImprintTranslationForm` on the side by side view

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.http.Http404: If no imprint exists for the region

        :return: The rendered template response
        """

        region = request.region

        try:
            imprint = region.imprint
        except ImprintPage.DoesNotExist as e:
            raise Http404 from e

        disabled = False
        # Make form disabled if user has no permission to manage the imprint
        if not request.user.has_perm("cms.change_imprintpage"):
            disabled = True
            messages.warning(
                request, _("You don't have the permission to edit the imprint.")
            )

        target_language = Language.objects.get(slug=kwargs.get("language_slug"))
        source_language_node = region.language_tree_nodes.get(
            language=target_language
        ).parent

        if source_language_node:
            source_language = source_language_node.language
        else:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view for the region's default language (in this case {default_language})."
                ).format(default_language=target_language.translated_name),
            )
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        source_imprint_translation = imprint.get_translation(source_language.slug)
        target_imprint_translation = imprint.get_translation(target_language.slug)

        if not source_imprint_translation:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view if the source translation (in this case {source_language}) does not exist."
                ).format(source_language=source_language.translated_name),
            )
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        imprint_translation_form = ImprintTranslationForm(
            instance=target_imprint_translation, disabled=disabled
        )

        old_translation_content = get_old_source_content(
            imprint, source_language_node.language, target_language
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "imprint_translation_form": imprint_translation_form,
                "source_imprint_translation": source_imprint_translation,
                "target_language": target_language,
                "old_translation_content": old_translation_content,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Submit :class:`~integreat_cms.cms.forms.imprint.imprint_translation_form.ImprintTranslationForm` and save
        :class:`~integreat_cms.cms.models.pages.imprint_page_translation.ImprintPageTranslation` object

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.http.Http404: If no imprint exists for the region

        :return: The rendered template response
        """

        region = request.region

        try:
            imprint = region.imprint
        except ImprintPage.DoesNotExist as e:
            raise Http404 from e

        target_language = Language.objects.get(slug=kwargs.get("language_slug"))
        source_language_node = region.language_tree_nodes.get(
            language=target_language
        ).parent

        if source_language_node:
            source_imprint_translation = imprint.get_translation(
                source_language_node.language.slug
            )
        else:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view for the region's default language (in this case {default_language})."
                ).format(default_language=target_language.translated_name),
            )
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        imprint_translation_instance = imprint.get_translation(target_language.slug)

        if not source_imprint_translation:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view if the source translation (in this case {source_language}) does not exist."
                ).format(source_language=source_language_node.language.translated_name),
            )
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        imprint_translation_form = ImprintTranslationForm(
            data=request.POST,
            instance=imprint_translation_instance,
            additional_instance_attributes={
                "page": imprint,
                "creator": request.user,
                "language": target_language,
            },
        )

        if not imprint_translation_form.is_valid():
            # Add error messages
            imprint_translation_form.add_error_messages(request)
        elif not imprint_translation_form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save form
            imprint_translation_form.save()
            # Add the success message
            imprint_translation_form.add_success_message(request)
            return redirect(
                "sbs_edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        old_translation_content = get_old_source_content(
            imprint, source_language_node.language, target_language
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "imprint_translation_form": imprint_translation_form,
                "source_imprint_translation": source_imprint_translation,
                "target_language": target_language,
                "old_translation_content": old_translation_content,
            },
        )


def get_old_source_content(
    imprint: ImprintPage, source_language: Language, target_language: Language
) -> str:
    """
    This function returns the content of the source language translation that was up to date when the latest (no minor edit)
    target language translation was created.

    :param imprint: The imprint
    :param source_language: The source language of the imprint
    :param target_language: The target language of the imprint
    :return: The content of the translation
    """
    # For the text diff, use the latest source translation that was created before the latest no minor edit target translation

    if major_target_imprint_translation := imprint.translations.filter(
        language__slug=target_language.slug, minor_edit=False
    ).first():
        if source_previous_translation := (
            imprint.translations.filter(
                language=source_language,
                last_updated__lte=major_target_imprint_translation.last_updated,
            )
            .order_by("-last_updated")
            .first()
        ):
            return source_previous_translation.content
    return ""
