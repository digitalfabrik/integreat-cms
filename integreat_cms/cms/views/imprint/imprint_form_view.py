from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...constants import status, translation_status
from ...decorators import permission_required
from ...forms import ImprintTranslationForm
from ...models import ImprintPage, ImprintPageTranslation
from ...utils.content_edit_lock import get_locking_user
from ...utils.translation_utils import gettext_many_lazy as __
from ...utils.translation_utils import translate_link
from ..media.media_context_mixin import MediaContextMixin
from .imprint_context_mixin import ImprintContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

    from ...models import Language, Region

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_imprintpage"), name="dispatch")
@method_decorator(permission_required("cms.change_imprintpage"), name="post")
class ImprintFormView(TemplateView, ImprintContextMixin, MediaContextMixin):
    """
    View for the imprint page form and imprint page translation form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "imprint/imprint_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {
        "translation_status": translation_status,
    }

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render :class:`~integreat_cms.cms.forms.imprint.imprint_translation_form.ImprintTranslationForm`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        # current region
        region = request.region

        # current language
        if language_slug := kwargs.get("language_slug"):
            language = region.get_language_or_404(language_slug, only_active=True)
        elif region.default_language:
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                },
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating pages."),
            )
            return redirect(
                "languagetreenodes",
                **{
                    "region_slug": region.slug,
                },
            )

        # get imprint and translation objects if they exist
        try:
            imprint = region.imprint
        except ImprintPage.DoesNotExist:
            imprint = None

        imprint_translation = ImprintPageTranslation.objects.filter(
            page=imprint,
            language=language,
        ).first()

        disabled = False
        if imprint:
            # Show information if latest changes are only saved as draft, but there is an earlier public version of this translation
            public_translation = imprint.get_public_translation(language.slug)
            if (
                public_translation
                and imprint_translation != public_translation
                and public_translation.id  # checking that public translation is not a fallback translation
            ):
                public_translation_url = reverse(
                    "imprint_versions",
                    kwargs={
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                        "selected_version": public_translation.version,
                    },
                )
                message = __(
                    _(
                        "This is not the most recent public revision of this translation."
                    ),
                    _(
                        "Instead, <a>revision {}</a> is shown in the apps.",
                    ).format(public_translation.version),
                )
                messages.info(
                    request,
                    translate_link(
                        message,
                        attributes={
                            "href": public_translation_url,
                            "class": "underline hover:no-underline",
                        },
                    ),
                )

        # Make form disabled if user has no permission to manage the imprint
        if not request.user.has_perm("cms.change_imprintpage"):
            disabled = True
            messages.warning(
                request, _("You don't have the permission to edit the imprint.")
            )

        imprint_translation_form = ImprintTranslationForm(
            instance=imprint_translation, disabled=disabled
        )

        # If the imprint does not exist yet, create the key manually
        edit_lock_key = (
            imprint.edit_lock_key if imprint else (region.slug, ImprintPage.__name__)
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "back_url": reverse("dashboard", kwargs={"region_slug": region.slug}),
                "imprint_translation_form": imprint_translation_form,
                "imprint": imprint,
                "language": language,
                # Languages for tab view
                "languages": region.active_languages if imprint else [language],
                "side_by_side_language_options": self.get_side_by_side_language_options(
                    region, language, imprint
                ),
                "translation_states": imprint.translation_states if imprint else [],
                "lock_key": edit_lock_key,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Binds the user input data to the imprint form and validates the input.
        Forms containing images/files need to be additionally instantiated with the FILES attribute of request objects,
        see :doc:`django:topics/http/file-uploads`

        :param request: Request submitted for saving imprint form
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: Redirection to the populated imprint form
        """

        region = request.region
        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )

        try:
            imprint_instance = region.imprint
        except ImprintPage.DoesNotExist:
            imprint_instance = None

        imprint_translation_instance = ImprintPageTranslation.objects.filter(
            page=imprint_instance,
            language=language,
        ).first()

        # Since imprints have a special rule for the lock key, compute it here and just pass it to the form
        lock_key = (
            imprint_instance.edit_lock_key
            if imprint_instance
            else (region.slug, ImprintPage.__name__)
        )
        locked_by_user = get_locking_user(*lock_key)

        imprint_translation_form = ImprintTranslationForm(
            data=request.POST,
            instance=imprint_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
            },
            changed_by_user=request.user,
            locked_by_user=locked_by_user,
        )

        if not imprint_translation_form.is_valid():
            # Add error messages
            imprint_translation_form.add_error_messages(request)
        elif (
            imprint_translation_form.instance.status == status.AUTO_SAVE
            and not imprint_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
        else:
            # Create imprint instance if not exists
            imprint_translation_form.instance.page = (
                imprint_instance or ImprintPage.objects.create(region=region)
            )
            # Save form
            imprint_translation_form.save()
            # Add the success message and redirect to the edit page
            if not imprint_instance:
                messages.success(request, _("Imprint was successfully created"))
            else:
                # Add the success message
                imprint_translation_form.add_success_message(request)
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "back_url": reverse("dashboard", kwargs={"region_slug": region.slug}),
                "imprint_translation_form": imprint_translation_form,
                "imprint": imprint_instance,
                "language": language,
                # Languages for tab view
                "languages": (
                    region.active_languages if imprint_instance else [language]
                ),
                "side_by_side_language_options": self.get_side_by_side_language_options(
                    region, language, imprint_instance
                ),
                "translation_states": (
                    imprint_instance.translation_states if imprint_instance else []
                ),
                "lock_key": lock_key,
            },
        )

    @staticmethod
    def get_side_by_side_language_options(
        region: Region, language: Language, imprint: ImprintPage | None
    ) -> list[dict[str, Any]]:
        """
        This is a helper function to generate the side-by-side language options for both the get and post requests.

        :param region: The current region
        :param language: The current language
        :param imprint: The current imprint
        :return: The list of language options, each represented by a dict
        """
        side_by_side_language_options = []
        for language_node in region.language_tree_nodes.filter(active=True):
            if language_node.parent:
                source_translation = ImprintPageTranslation.objects.filter(
                    page=imprint,
                    language=language_node.parent.language,
                )
                side_by_side_language_options.append(
                    {
                        "value": language_node.language.slug,
                        "label": _("{source_language} to {target_language}").format(
                            source_language=language_node.parent.language.translated_name,
                            target_language=language_node.language.translated_name,
                        ),
                        "selected": language_node.language == language,
                        "disabled": not source_translation.exists(),
                    }
                )
        return side_by_side_language_options
