from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import permission_required
from ...forms import PageTranslationForm
from ...models import Language
from ..media.media_context_mixin import MediaContextMixin
from ..mixins import ContentEditLockMixin
from .page_context_mixin import PageContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

    from integreat_cms.cms.models.pages.page import Page

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageSideBySideView(
    TemplateView, PageContextMixin, MediaContextMixin, ContentEditLockMixin
):
    """
    View for the page side by side form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pages/page_sbs.html"
    #: The url name of the view to show if the user decides to go back (see :class:`~integreat_cms.cms.views.mixins.ContentEditLockMixin`)
    back_url_name: str | None = "pages"

    def get(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse | HttpResponseRedirect:
        r"""
        Render :class:`~integreat_cms.cms.forms.pages.page_translation_form.PageTranslationForm` on the side by side view

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region
        page = region.pages.get(id=kwargs.get("page_id"))

        target_language = Language.objects.get(slug=kwargs.get("language_slug"))
        if source_language_node := region.language_tree_nodes.get(
            language=target_language
        ).parent:
            source_language = source_language_node.language
        else:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view for the region's default language (in this case {default_language})."
                ).format(default_language=target_language.translated_name),
            )
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        source_page_translation = page.get_translation(source_language.slug)
        target_page_translation = page.get_translation(target_language.slug)

        if not source_page_translation:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view if the source translation (in this case {source_language}) does not exist."
                ).format(source_language=source_language.translated_name),
            )
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        disabled = False
        # Make form disabled if user has no permission to edit the page
        if not request.user.has_perm("cms.change_page_object", page):
            disabled = True
            messages.warning(
                request,
                _("You don't have the permission to edit this page."),
            )

        page_translation_form = PageTranslationForm(
            instance=target_page_translation,
            disabled=disabled,
        )

        old_translation_content = get_old_source_content(
            page, source_language, target_language
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "page_translation_form": page_translation_form,
                "source_page_translation": source_page_translation,
                "target_language": target_language,
                "old_translation_content": old_translation_content,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Submit :class:`~integreat_cms.cms.forms.pages.page_translation_form.PageTranslationForm` and save
        :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` object

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit pages

        :return: The rendered template response
        """

        region = request.region
        page = region.pages.get(id=kwargs.get("page_id"))

        if not request.user.has_perm("cms.change_page_object", page):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to edit {page!r}"
            )

        target_language = Language.objects.get(slug=kwargs.get("language_slug"))
        source_language_node = region.language_tree_nodes.get(
            language=target_language
        ).parent

        if source_language_node:
            source_page_translation = page.get_translation(
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
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        page_translation_instance = page.get_translation(target_language.slug)

        if not source_page_translation:
            messages.error(
                request,
                _(
                    "You cannot use the side-by-side-view if the source translation (in this case {source_language}) does not exist."
                ).format(source_language=source_language_node.language.translated_name),
            )
            return redirect(
                "edit_page",
                **{
                    "page_id": page.id,
                    "region_slug": region.slug,
                    "language_slug": target_language.slug,
                },
            )

        page_translation_form = PageTranslationForm(
            data=request.POST,
            instance=page_translation_instance,
            additional_instance_attributes={
                "page": page,
                "creator": request.user,
                "language": target_language,
            },
            changed_by_user=request.user,
        )

        if not page_translation_form.is_valid():
            # Add error messages
            page_translation_form.add_error_messages(request)
        elif not page_translation_form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        elif not request.user.has_perm("cms.publish_page_object", page) and (
            page_translation_form.cleaned_data.get("status")
            in [status.DRAFT, status.PUBLIC]
        ):
            # Raise PermissionDenied if user wants to publish page but doesn't have the permission
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to publish {page!r}"
            )
        else:
            # Save form
            page_translation_form.save()
            # Add the success message
            page_translation_form.add_success_message(request)

        old_translation_content = get_old_source_content(
            page, source_language_node.language, target_language
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "page_translation_form": page_translation_form,
                "source_page_translation": source_page_translation,
                "target_language": target_language,
                "old_translation_content": old_translation_content,
            },
        )


def get_old_source_content(
    page: Page, source_language: Language, target_language: Language
) -> str:
    """
    This function returns the content of the source language translation that was up to date when the latest (no minor edit)
    target language translation was created.

    :param page: The page
    :param source_language: The source language of the page
    :param target_language: The target language of the page
    :return: The content of the translation
    """
    if major_target_page_translation := page.translations.filter(
        language__slug=target_language.slug, minor_edit=False
    ).first():
        if source_previous_translation := (
            page.translations.filter(
                language=source_language,
                last_updated__lte=major_target_page_translation.last_updated,
            )
            .order_by("-last_updated")
            .first()
        ):
            return source_previous_translation.content
    return ""
