from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from ...decorators import permission_required
from ...models import Contact

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponseRedirect


@permission_required("cms.archive_contact")
def archive_contact(
    request: HttpRequest,
    contact_id: int,
    region_slug: str,
) -> HttpResponseRedirect:
    """
    Method that archives a given contact

    :param request: The current request
    :param contact_id: Id of the existing contact that is supposed to be archived
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.contacts.contact_list_view.ContactListView`
    """
    to_be_archived_contact = get_object_or_404(
        Contact,
        id=contact_id,
        location__region=request.region,
    )
    if not to_be_archived_contact.referring_objects:
        to_be_archived_contact.archive()
        messages.success(
            request,
            _("Contact {0} was successfully archived").format(to_be_archived_contact),
        )
        return redirect(
            "contacts",
            **{
                "region_slug": region_slug,
            },
        )
    messages.error(
        request,
        _('Cannot archive contact "{0}" while content objects refer to it.').format(
            to_be_archived_contact,
        ),
    )
    return redirect("edit_contact", region_slug=region_slug, contact_id=contact_id)


@permission_required("cms.delete_contact")
def delete_contact(
    request: HttpRequest,
    contact_id: int,
    region_slug: str,
) -> HttpResponseRedirect:
    """
    Delete given contact

    :param request: The current request
    :param contact_id: The id of the contact which should be deleted
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.contacts.contact_list_view.ContactListView`
    """
    to_be_deleted_contact = get_object_or_404(
        Contact,
        id=contact_id,
        location__region=request.region,
    )
    if not to_be_deleted_contact.referring_objects:
        to_be_deleted_contact.delete()
        messages.success(
            request,
            _("Contact {0} was successfully deleted").format(to_be_deleted_contact),
        )
        return redirect(
            "contacts",
            **{
                "region_slug": region_slug,
            },
        )
    messages.error(
        request,
        _('Cannot delete contact "{0}" while content objects refer to it.').format(
            to_be_deleted_contact,
        ),
    )
    return redirect("edit_contact", region_slug=region_slug, contact_id=contact_id)


@permission_required("cms.archive_contact")
def restore_contact(
    request: HttpRequest,
    contact_id: int,
    region_slug: str,
) -> HttpResponseRedirect:
    """
    Restore given contact

    :param request: The current request
    :param contact_id: The id of the contact which should be restored
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.contacts.contact_list_view.ContactListView`
    """
    to_be_restored_contact = get_object_or_404(
        Contact,
        id=contact_id,
        location__region=request.region,
    )
    to_be_restored_contact.restore()

    messages.success(
        request,
        _("Contact {0} was successfully restored").format(to_be_restored_contact),
    )

    return redirect(
        "archived_contacts",
        **{
            "region_slug": region_slug,
        },
    )


@permission_required("cms.change_contact")
def copy_contact(
    request: HttpRequest,
    contact_id: int,
    region_slug: str,
) -> HttpResponseRedirect:
    """
    Method that copies an existing contact

    :param request: The current request
    :param contact_id: Id of the existing contact that is supposed to be copied
    :param region_slug: The slug of the current region
    :return: A redirection to the :class:`~integreat_cms.cms.views.contacts.contact_list_view.ContactListView`
    """
    to_be_copied_contact = get_object_or_404(
        Contact,
        id=contact_id,
        location__region=request.region,
    )
    to_be_copied_contact.copy()

    messages.success(
        request,
        _("Contact {0} was successfully copied").format(to_be_copied_contact),
    )
    return redirect(
        "contacts",
        **{
            "region_slug": region_slug,
        },
    )
