from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from django.db.models import signals as model_signals
from lxml.etree import LxmlError
from lxml.html import fromstring, tostring

from ..constants import status
from ..contactlist import contactlists
from ..models.contact.contact import Contact
from ..models.contact.contact_usage import ContactUsage
from .content_utils import update_contacts

if TYPE_CHECKING:
    from typing import Any, Iterator, Never

    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


def check_instance_contactusages(  # pylint: disable=too-many-locals
    sender: AbstractContentTranslation,
    instance: AbstractContentTranslation,
    **kwargs: dict[str, Any],
) -> None:
    """
    Look up whether any contacts are tracked to be used in the content translation.
    We only care about the most recent and currently public translations, so we can delete any ContactUsages regarding other translations of the same page.
    Retrieve all contacts actually used in the translation, create new ContactUsages and delete outdated ContactUsages.
    """
    # The contact list is what will manage the actual extraction of contact ids from the content
    contactlist_cls = sender._contactlist  # pylint: disable=protected-access
    content_type = contactlist_cls.content_type()

    # We need to know all ids of content translations of the same page to query for old ContactUsages
    previous_versions = instance.all_versions
    # We want to know whether there is an older translation that will stay live
    leaving_previous_public = (
        instance.status != status.PUBLIC and instance.major_public_version is not None
    )
    if (
        not leaving_previous_public
        and instance.latest_version is not instance.major_public_version
    ):
        # Recycle old objects for the new instance if they aren't still needed for the live public version
        ContactUsage.objects.filter(
            content_type=content_type, object_id=instance.latest_version.pk
        ).update(object_id=instance.pk)
    if leaving_previous_public:
        # Let objects of last major version continue to exist,
        # so contacts in public translations get updated even when there are newer (unpublished) versions
        previous_versions = previous_versions.exclude(
            id=instance.major_public_version.pk
        )

    # Now we can start actually working on this translation
    new_contacts = []
    old_contacts = ContactUsage.objects.filter(
        content_type=content_type,
        object_id__in=previous_versions.values_list("pk", flat=True),
    )

    # This does the magic of extracting contact ids from HTML content
    instance_contactlists = contactlist_cls().get_contactlist(
        extra_filter={"pk": instance.pk}
    )
    logger.warning("instance_contactlists = %r", instance_contactlists)

    if not instance_contactlists:
        # This object is no longer watched by us according to object_filter
        contacts = []
    else:
        # We queried for exactly one object (instance.pk)
        # so we don't need to bother looking past the first element
        contactlist = instance_contactlists[0]
        contacts = contactlist["contacts"]
    logger.warning("contacts = %r", contacts)

    for c in contacts:
        # structure: (field, contact id)
        contact = Contact.objects.get(pk=c[1])
        u, _created = ContactUsage.objects.get_or_create(
            contact=contact,
            field=c[0],
            content_type=content_type,
            object_id=instance.pk,
        )
        new_contacts.append(u.id)

    logger.warning("new_contacts = %r", new_contacts)
    gone_contacts = old_contacts.exclude(id__in=new_contacts)
    logger.warning("gone_contacts = %r", gone_contacts)
    gone_contacts.delete()


def delete_instance_contactusages(
    sender: AbstractContentTranslation,
    instance: AbstractContentTranslation,
    **kwargs: dict[str, Any],
) -> None:
    """
    Delete all ContactUsages belonging to a model instance when that instance is deleted
    """
    contactlist_cls = sender._contactlist  # pylint: disable=protected-access
    content_type = contactlist_cls.content_type()
    old_contactusages = ContactUsage.objects.filter(
        content_type=content_type, object_id=instance.pk
    )
    old_contactusages.delete()


def contact_post_save(
    sender: Contact,
    instance: Contact,
    raw: bool = False,
    **kwargs: dict[str, Any],  # pylint: disable=unused-argument
) -> None:
    """
    Update any content using a contact when it is changed
    """
    if not instance.pk or raw:
        # Ignore unsaved instances or raw imports
        return

    usages = ContactUsage.objects.filter(contact=instance.pk)

    for usage in usages:
        content_object = usage.content_object
        original = getattr(content_object, usage.field)
        try:
            content = fromstring(original)
        except LxmlError:
            # The content is not guaranteed to be valid html, for example it may be empty
            continue

        update_contacts(content, only_ids=(instance.pk,))

        content_str = tostring(content, encoding="unicode", with_tail=False)
        setattr(content_object, usage.field, content_str)
        content_object.save(update_timestamp=False)


def register_listeners() -> None:
    """
    Register all update listeners to the contact and content models
    """
    # 1. register listeners for the objects that use Contacts
    for contactlist_cls in contactlists.values():
        model_signals.post_save.connect(
            check_instance_contactusages, sender=contactlist_cls.model
        )
        model_signals.post_delete.connect(
            delete_instance_contactusages, sender=contactlist_cls.model
        )

    # 2. register listeners for Contacts
    model_signals.post_save.connect(contact_post_save, sender=Contact)


def unregister_listeners() -> None:
    """
    Unregister all update listeners from the contact and content models
    """
    # 1. unregister listeners for the objects that use Contacts
    for contactlist_cls in contactlists.values():
        model_signals.post_save.disconnect(
            check_instance_contactusages, sender=contactlist_cls.model
        )
        model_signals.post_delete.disconnect(
            delete_instance_contactusages, sender=contactlist_cls.model
        )

    # 2. unregister listeners for Contacts
    model_signals.post_save.disconnect(contact_post_save, sender=Contact)


@contextmanager
def enable_listeners(*args: list[Any], **kwargs: dict[str, Any]) -> Iterator:
    """
    A context manager to register all update listeners, do something, and unregister them
    """
    register_listeners()
    try:
        yield
    finally:
        unregister_listeners()


@contextmanager
def disable_listeners(*args: list[Any], **kwargs: dict[str, Any]) -> Iterator:
    """
    A context manager to unregister all update listeners, do something, and register them again
    """
    unregister_listeners()
    try:
        yield
    finally:
        register_listeners()
