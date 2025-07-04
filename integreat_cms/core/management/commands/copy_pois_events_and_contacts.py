from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from integreat_cms.cms.models import Event, POI, Region

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser
    from django.db.models import FileField

    from integreat_cms.cms.models import EventTranslation, POITranslation

    from .users.user import User


logger = logging.getLogger(__name__)


def make_hardlink(file_field: FileField, region_id: int) -> FileField:
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
    if obj.icon and obj.icon.region is not None:
        # Theoretically, there might be orphaned media files
        obj.icon.pk = None
        obj.icon.region = region
        try:
            obj.icon.file = make_hardlink(obj.icon.file, region.pk)
        except FileNotFoundError:
            logger.info("Could not copy icon for %r: FileNotFound", obj)
        obj.icon.save()


def copy_translations(
    region: Region,
    translations: list[POITranslation] | list[EventTranslation],
    obj: POI | Event,
    related_name: str,
) -> None:
    for tr in translations:
        if tr.language in region.languages:
            # Ensure partial attempts don't make everything more difficult
            try:
                dup = obj.translations.get(language=tr.language, version=tr.version)
            except obj.translations.model.DoesNotExist:
                pass
            else:
                logger.info(
                    "Not saving translation, already exists in %r: %r",
                    tr.language,
                    dup,
                )
                continue
            tr.pk = None
            setattr(tr, related_name, obj)
            # Don't update the timestamp
            tr.save(update_timestamp=False)
            logger.info(
                "Saved translation to target region in %r: %r",
                tr.language,
                tr,
            )
        else:
            logger.info(
                "Not saving translation in language not in target region (%r): %r",
                tr.language,
                tr,
            )


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
    help = "Duplicate POIs and contacts into one or many target regions"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "template_slug", type=str, help=_("The slug of the template region")
        )
        parser.add_argument(
            "target_slugs",
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

    def handle(
        self,
        *args: Any,
        template_slug: str,
        target_slugs: list[str],
        username: str,
        contacts: bool,
        events: bool,
        **options: Any,
    ) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param template_slug: The slug of template region
        :param target_slugs: The slugs of target regions
        :param contact: Whether contacts should be copied too
        :param \**options: The supplied keyword options

        """
        user = get_user(username) if username else None
        template_region = Region.objects.get(slug=template_slug)
        target_regions = [Region.objects.get(slug=slug) for slug in target_slugs]

        with transaction.atomic():
            for poi in POI.objects.filter(region=template_region):
                source_events = list(poi.events.all())
                source_contacts = list(poi.contacts.all())
                for target_region in target_regions:
                    copy_icon(target_region, poi)

                    # need to grab query set before poi points to a different object in db
                    translations = list(poi.translations.all())
                    poi.pk = None
                    poi.region = target_region
                    poi.save()

                    copy_translations(target_region, translations, poi, "poi")

                    if contacts:
                        for source_contact in source_contacts:
                            source_contact.pk = None
                            source_contact.location = poi
                            source_contact.save()

                    if events:
                        for source_event in source_events:
                            new_event = source_event.copy(user)
                            new_event.location = poi
                            new_event.region = target_region
                            new_event.save()

            if events:
                events_without_poi = Event.objects.filter(
                    location_id=None, region=template_region
                )
                for event in events_without_poi:
                    for target_region in target_regions:
                        new_event = event.copy(user)
                        new_event.region = target_region
                        new_event.save()
