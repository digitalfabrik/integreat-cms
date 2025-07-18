from __future__ import annotations

import logging
import os
import re
from copy import deepcopy
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from integreat_cms.cms.models import Event, POI, Region, User

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser
    from django.db.models import FileField


logger = logging.getLogger(__name__)


def make_hardlink(file_field: FileField, region_id: int) -> FileField:
    """
    Create a hardlink to the original file in the media path for the target region
    """
    base = file_field.storage.base_location
    orig_path = file_field.name
    new_path = re.sub(r"^regions/[0-9]+/", f"regions/{region_id}/", orig_path)
    # make the directory
    os.makedirs(os.path.dirname(os.path.join(base, new_path)), exist_ok=True)
    # create the hard link
    try:
        os.link(os.path.join(base, orig_path), os.path.join(base, new_path))
    except FileExistsError as e:
        if (
            os.stat(os.path.join(base, orig_path)).st_ino
            == os.stat(os.path.join(base, new_path)).st_ino
        ):
            logger.info(
                "Hard link already exists between %r and %r",
                new_path,
                orig_path,
            )
        else:
            raise FileExistsError("Failed to create hard link") from e
    # modify the file information
    file_field.name = new_path
    return file_field


def copy_icon(region: Region, obj: POI | Event) -> None:
    """
    Ensure the icon of an object is accessible from the target region as well
    """
    if obj.icon and obj.icon.region is not None:
        # Theoretically, there might be orphaned media files
        obj.icon.pk = None
        obj.icon.region = region
        try:
            obj.icon.file = make_hardlink(obj.icon.file, region.pk)
        except FileNotFoundError:
            logger.info("Could not copy icon for %r: FileNotFound", obj)
        obj.icon.save()


def get_user(username: str) -> User:
    """
    Get a user by username or raise an error if not found

    :param username: Username
    :return: User
    """
    try:
        return get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist as e:
        raise CommandError(f'User with username "{username}" does not exist.') from e


class Command(BaseCommand):
    help = "Duplicate POIs into target regions"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "template-slug", type=str, help=_("The slug of the template region")
        )
        parser.add_argument(
            "target-slug",
            type=str,
            nargs="+",
            help=_("The slugs of the target regions"),
        )
        parser.add_argument("--username", help="The username of the creator")
        parser.add_argument(
            "--contacts",
            action="store_true",
            help="Whether contacts should be copied too",
        )
        parser.add_argument(
            "--events",
            action="store_true",
            help="Whether events should be copied too",
        )
        parser.add_argument(
            "--add-suffix",
            action="store_true",
            help="Whether the suffix ' (Copy)' should be appended",
        )

    def handle(
        self,
        *args: Any,
        username: str,
        contacts: bool,
        events: bool,
        add_suffix: bool,
        **options: Any,
    ) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param contact: Whether contacts should be copied too
        :param \**options: The supplied keyword options

        """
        template_slug = options["template-slug"]
        target_slug = options["target-slug"]
        user = get_user(username) if username else None
        template_region = Region.objects.get(slug=template_slug)
        target_regions = [Region.objects.get(slug=slug) for slug in target_slug]

        with transaction.atomic():
            for source_poi in POI.objects.filter(region=template_region):
                source_events = list(source_poi.events.all())
                source_contacts = list(source_poi.contacts.all())

                for target_region in target_regions:
                    # Create a deep copy per region so we don't somehow mess up the template object for the next target region
                    poi = deepcopy(source_poi)

                    copy_icon(target_region, poi)

                    poi.region = target_region
                    poi.copy(user=user, add_suffix=add_suffix)

                    if contacts:
                        for source_contact in source_contacts:
                            contact = deepcopy(source_contact)

                            contact.location = poi
                            contact.copy(add_suffix=add_suffix)

                    if events:
                        for source_event in source_events:
                            event = deepcopy(source_event)

                            event.location = poi
                            event.region = target_region
                            event.copy(user=user, add_suffix=add_suffix)

            if events:
                events_without_poi = Event.objects.filter(
                    location_id=None, region=template_region
                )
                for source_event in events_without_poi:
                    for target_region in target_regions:
                        event = deepcopy(source_event)

                        event.region = target_region
                        event.copy(user=user, add_suffix=add_suffix)
