from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from backend.settings import IMPRINT_SLUG, WEBAPP_URL
from ...constants import status
from ...decorators import region_permission_required
from ...forms import ImprintTranslationForm
from ...models import Region, Language, ImprintPage


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class ImprintSideBySideView(PermissionRequiredMixin, TemplateView):
    """
    View for the imprint side by side form
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_imprint"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "imprint/imprint_sbs.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {
        "current_menu_item": "imprint",
        "WEBAPP_URL": WEBAPP_URL,
        "IMPRINT_SLUG": IMPRINT_SLUG,
    }

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.imprint.imprint_translation_form.ImprintTranslationForm` on the side by side view

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.http.Http404: If no imprint exists for the region

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)

        try:
            imprint = region.imprint
        except ImprintPage.DoesNotExist as e:
            raise Http404 from e

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
                }
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
                }
            )

        imprint_translation_form = ImprintTranslationForm(
            instance=target_imprint_translation,
        )

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "imprint_translation_form": imprint_translation_form,
                "source_imprint_translation": source_imprint_translation,
                "target_language": target_language,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.imprint.imprint_translation_form.ImprintTranslationForm` and save
        :class:`~cms.models.pages.imprint_page_translation.ImprintPageTranslation` object

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.http.Http404: If no imprint exists for the region

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)

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
                }
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
                }
            )

        imprint_translation_form = ImprintTranslationForm(
            request.POST,
            instance=imprint_translation_instance,
            region=region,
            language=target_language,
        )

        if not imprint_translation_form.is_valid():
            messages.error(request, _("Errors have occurred."))
        elif not imprint_translation_form.has_changed():
            messages.info(request, _("No changes detected."))
        else:
            imprint_translation = imprint_translation_form.save(
                imprint=imprint, user=request.user
            )
            published = imprint_translation.status == status.PUBLIC
            if not imprint_translation_instance:
                if published:
                    messages.success(
                        request,
                        _("Translation was successfully created and published"),
                    )
                else:
                    messages.success(request, _("Translation was successfully created"))
            else:
                if published:
                    messages.success(
                        request, _("Translation was successfully published")
                    )
                else:
                    messages.success(request, _("Translation was successfully saved"))

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "imprint_translation_form": imprint_translation_form,
                "source_imprint_translation": source_imprint_translation,
                "target_language": target_language,
            },
        )
