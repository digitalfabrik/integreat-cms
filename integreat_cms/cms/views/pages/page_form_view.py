import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.db import transaction

from ...constants import status, text_directions
from ...decorators import permission_required
from ...forms import PageForm, PageTranslationForm
from ...models import PageTranslation
from .page_context_mixin import PageContextMixin
from ..media.media_context_mixin import MediaContextMixin
from ..mixins import ContentEditLockMixin

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageFormView(
    TemplateView, PageContextMixin, MediaContextMixin, ContentEditLockMixin
):
    """
    View for the page form and page translation form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pages/page_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {
        "current_menu_item": "new_page",
    }
    #: The url name of the view to show if the user decides to go back (see :class:`~integreat_cms.cms.views.mixins.ContentEditLockMixin`)
    back_url_name = "pages"

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        r"""
        Render :class:`~integreat_cms.cms.forms.pages.page_form.PageForm` and :class:`~integreat_cms.cms.forms.pages.page_translation_form.PageTranslationForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )

        # get page and translation objects if they exist
        page = (
            region.pages.filter(id=kwargs.get("page_id"))
            .prefetch_translations()
            .prefetch_public_translations()
            .first()
        )
        page_translation = page.get_translation(language.slug) if page else None

        disabled = False
        if page:
            # Make form disabled if page is archived
            if page.explicitly_archived:
                disabled = True
                messages.warning(
                    request, _("You cannot edit this page because it is archived.")
                )
            elif page.implicitly_archived:
                disabled = True
                messages.warning(
                    request,
                    _(
                        "You cannot edit this page, because one of its parent pages is archived and therefore, this page is archived as well."
                    ),
                )
            # Show information if latest changes are only saved as draft
            public_translation = page.get_public_translation(language.slug)
            if public_translation and page_translation != public_translation:
                messages.info(
                    request,
                    _(
                        "The latest changes have only been saved as a draft. Currently, <a href='%(revision_url)s' class='underline hover:no-underline'>version %(revision)s</a> of this page is displayed in the app."
                    )
                    % {
                        "revision_url": reverse(
                            "page_revisions",
                            kwargs={
                                "region_slug": region.slug,
                                "language_slug": language.slug,
                                "page_id": page.id,
                                "selected_revision": public_translation.version,
                            },
                        ),
                        "revision": public_translation.version,
                    },
                )

        # Make form disabled if user has no permission to edit the page
        if not request.user.has_perm("cms.change_page_object", page):
            disabled = True
            messages.warning(
                request,
                _("You don't have the permission to edit this page."),
            )
        # Show warning if user has no permission to publish the page
        if not request.user.has_perm("cms.publish_page_object", page):
            messages.warning(
                request,
                _(
                    "You don't have the permission to publish this page, but you can propose changes and submit them for review instead."
                ),
            )

        page_form = PageForm(
            instance=page,
            disabled=disabled,
            additional_instance_attributes={
                "region": region,
            },
        )
        # Pass language to mirrored page widget to render the preview urls
        page_form.fields["mirrored_page"].widget.language_slug = language.slug

        if not request.user.expert_mode:
            del page_form.fields["api_token"]

        page_translation_form = PageTranslationForm(
            instance=page_translation, disabled=disabled
        )

        # Pass side by side language options
        side_by_side_language_options = self.get_side_by_side_language_options(
            region, language, page
        )

        # Pass siblings to template to enable rendering of page order table
        if page:
            siblings = (
                page.region_siblings.prefetch_translations()
                .prefetch_public_translations()
                .filter(explicitly_archived=page.explicitly_archived)
            )
        else:
            siblings = (
                region.get_root_pages()
                .prefetch_translations()
                .prefetch_public_translations()
                .filter(explicitly_archived=False)
            )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "page_form": page_form,
                "page_translation_form": page_translation_form,
                "page": page,
                "siblings": siblings,
                "language": language,
                # Languages for tab view
                "languages": region.active_languages if page else [language],
                "side_by_side_language_options": side_by_side_language_options,
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
                "translation_states": page.translation_states if page else [],
            },
        )

    @transaction.atomic
    # pylint: disable=too-many-branches,unused-argument
    def post(self, request, *args, **kwargs):
        r"""
        Submit :class:`~integreat_cms.cms.forms.pages.page_form.PageForm` and
        :class:`~integreat_cms.cms.forms.pages.page_translation_form.PageTranslationForm` and save :class:`~integreat_cms.cms.models.pages.page.Page`
        and :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` objects.
        Forms containing images/files need to be additionally instantiated with the FILES attribute of request objects,
        see :doc:`django:topics/http/file-uploads`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region
        language = region.get_language_or_404(
            kwargs.get("language_slug"), only_active=True
        )

        page_instance = region.pages.filter(id=kwargs.get("page_id")).first()

        if not request.user.has_perm("cms.change_page_object", page_instance):
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to edit {page_instance!r}"
            )

        page_translation_instance = PageTranslation.objects.filter(
            page=page_instance,
            language=language,
        ).first()

        page_form = PageForm(
            data=request.POST,
            files=request.FILES,
            instance=page_instance,
            additional_instance_attributes={
                "region": region,
            },
        )
        # Pass language to mirrored page widget to render the preview urls
        page_form.fields["mirrored_page"].widget.language_slug = language.slug

        if not request.user.expert_mode:
            del page_form.fields["api_token"]

        page_translation_form = PageTranslationForm(
            data=request.POST,
            instance=page_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "page": page_form.instance,
            },
            changed_by_user=request.user,
        )

        if not page_form.is_valid() or not page_translation_form.is_valid():
            # Add error messages
            page_form.add_error_messages(request)
            page_translation_form.add_error_messages(request)
        elif (
            not request.user.has_perm("cms.publish_page_object", page_form.instance)
            and page_translation_form.cleaned_data.get("status") == status.PUBLIC
        ):
            # Raise PermissionDenied if user wants to publish page but doesn't have the permission
            raise PermissionDenied(
                f"{request.user!r} does not have the permission to publish {page_form.instance!r}"
            )
        elif (
            page_translation_form.instance.status == status.AUTO_SAVE
            and not page_form.has_changed()
            and not page_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))

        else:
            # Only save page form if page does not yet exist or if translation is no auto save
            if (
                not page_instance
                or page_translation_form.instance.status != status.AUTO_SAVE
            ):
                page_translation_form.instance.page = page_form.save()
            # Save page translation form
            page_translation_form.save()
            # If any source translation changes to draft, set all depending translations/versions to draft
            if page_translation_form.instance.status == status.DRAFT:
                language_tree_node = region.language_node_by_slug.get(language.slug)
                languages = [language] + [
                    node.language for node in language_tree_node.get_descendants()
                ]
                page_translation_form.instance.page.translations.filter(
                    language__in=languages
                ).update(status=status.DRAFT)
            # Add the success message and redirect to the edit page
            if not page_instance:
                messages.success(
                    request,
                    _('Page "{}" was successfully created').format(
                        page_translation_form.instance.title
                    ),
                )
            elif (
                not page_form.has_changed() and not page_translation_form.has_changed()
            ):
                messages.info(request, _("No changes detected, but date refreshed"))
            else:
                # Add the success message
                page_translation_form.add_success_message(request)
            return redirect(
                "edit_page",
                **{
                    "page_id": page_form.instance.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                },
            )

        # Pass siblings to template to enable rendering of page order table
        if page_translation_form.instance.id:
            siblings = page_translation_form.instance.page.region_siblings
        elif page_form.instance.id:
            siblings = page_form.instance.region_siblings
        else:
            siblings = region.get_root_pages()
        siblings = siblings.filter(
            explicitly_archived=page_form.instance.explicitly_archived
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "page_form": page_form,
                "page_translation_form": page_translation_form,
                "page": page_instance,
                "siblings": siblings,
                "language": language,
                # Languages for tab view
                "languages": region.active_languages if page_instance else [language],
                "side_by_side_language_options": self.get_side_by_side_language_options(
                    region, language, page_instance
                ),
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
                "translation_states": page_instance.translation_states
                if page_instance
                else [],
            },
        )

    @staticmethod
    def get_side_by_side_language_options(region, language, page):
        """
        This is a helper function to generate the side-by-side language options for both the get and post requests.

        :param region: The current region
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param language: The current language
        :type language: ~integreat_cms.cms.models.languages.language.Language

        :param page: The current page
        :type page: ~integreat_cms.cms.models.pages.page.Page

        :return: The list of language options, each represented by a dict
        :rtype: list
        """

        side_by_side_language_options = []
        for language_node in filter(lambda n: n.active, region.language_tree):
            if not language_node.is_root():
                source_language = region.language_node_by_id.get(
                    language_node.parent_id
                ).language
                side_by_side_language_options.append(
                    {
                        "value": language_node.slug,
                        "label": _("{source_language} to {target_language}").format(
                            source_language=source_language.translated_name,
                            target_language=language_node.translated_name,
                        ),
                        "selected": language_node.language == language,
                        "disabled": not page or source_language not in page.languages,
                    }
                )
        return side_by_side_language_options
