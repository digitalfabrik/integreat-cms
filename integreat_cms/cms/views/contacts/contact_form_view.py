from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import ContactForm
from ...models import Contact
from ...utils.translation_utils import gettext_many_lazy as __
from .contact_context_mixin import ContactContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse


@method_decorator(permission_required("cms.view_contact"), name="dispatch")
@method_decorator(permission_required("cms.change_contact"), name="post")
class ContactFormView(TemplateView, ContactContextMixin):
    """
    Class for rendering the contact form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "contacts/contact_form.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render contact form for HTTP GET requests

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region
        contact_instance = Contact.objects.filter(
            id=kwargs.get("contact_id"), location__region=region
        ).first()

        if contact_instance and contact_instance.archived:
            disabled = True
            messages.warning(
                request, _("You cannot edit this contact because it is archived.")
            )
        elif not request.user.has_perm("cms.change_contact"):
            disabled = True
            messages.warning(
                request, _("You don't have the permission to edit contacts.")
            )
        else:
            disabled = False

        contact_form = ContactForm(
            instance=contact_instance,
            disabled=disabled,
            additional_instance_attributes={"region": region},
        )

        help_text = (
            _("This location is used for the contact.")
            if contact_instance
            else _(
                "Select a location to use for your contact or create a new location. Only published locations can be set."
            )
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "contact_form": contact_form,
                "poi": contact_instance.location if contact_instance else None,
                "referring_pages": None,  # to implement later, how do we collect such pages?
                "referring_locations": None,  # to implement later, how do we collect such POIs?
                "referring_events": None,  # to implement later, how do we collect such Events?
                "help_text": help_text,
            },
        )

    def post(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        r"""
        Save contact and ender contact form for HTTP POST requests

        :param request: Object representing the user call
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to change contact

        :return: The rendered template response
        """
        region = request.region

        contact_instance = Contact.objects.filter(
            id=kwargs.get("contact_id"), location__region=region
        ).first()
        contact_form = ContactForm(
            data=request.POST,
            instance=contact_instance,
            additional_instance_attributes={"region": region},
        )

        if not contact_form.is_valid():
            contact_form.add_error_messages(request)
        else:
            contact_form.save()
            if not contact_instance:
                messages.success(
                    request,
                    _('Contact for "{}" was successfully created').format(
                        contact_form.instance
                    ),
                )
            elif not contact_form.has_changed():
                messages.info(request, _("No changes detected, but date refreshed"))
            else:
                messages.success(
                    request,
                    _('Contact for "{}" was successfully saved').format(
                        contact_form.instance
                    ),
                )
            return redirect(
                "edit_contact",
                **{
                    "contact_id": contact_form.instance.id,
                    "region_slug": region.slug,
                },
            )

        help_text = (
            _("This location is used for the contact.")
            if contact_instance
            else _(
                "Select a location to use for your contact or create a new location. Only published locations can be set."
            )
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "contact_form": contact_form,
                "poi": contact_instance.location if contact_instance else None,
                "referring_pages": None,
                "referring_locations": None,
                "referring_events": None,
                "help_text": help_text,
            },
        )
