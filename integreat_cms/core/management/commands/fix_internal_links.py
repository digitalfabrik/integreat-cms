import logging
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.utils.text import slugify
from django.utils.translation import gettext as _
from linkcheck.models import Url

from integreat_cms.cms.utils.linkcheck_utils import replace_links

from ....cms.models import Event, Page, POI, Region
from ....cms.utils.linkcheck_utils import replace_links
from ..log_command import LogCommand

logger = logging.getLogger(__name__)


def get_region(region_slug):
    """
    Get a region object by slug or raise an error if not found

    :param region_slug: Region slug
    :type region_slug: str

    :return: Region
    :rtype: ~integreat_cms.cms.models.regions.region.Region
    """
    try:
        return Region.objects.get(slug=region_slug)
    except Region.DoesNotExist as e:
        raise CommandError(f'Region with slug "{region_slug}" does not exist.') from e


def get_user(username):
    """
    Get a user by username or raise an error if not found

    :param username: Username
    :type username: str

    :return: User
    :rtype: ~integreat_cms.cms.models.users.user.User
    """
    try:
        return get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist as e:
        raise CommandError(f'User with username "{username}" does not exist.') from e


def parse_internal_url(url):
    """
    Parse internal url

    :param url: The URL
    :type url: linkcheck.models.Url

    :return: Region slug, language slug, content type, translation slug
    :rtype: str, str, str, str
    """
    prepared_url = unquote(url.internal_url).strip("/")
    region_slug, language_and_path = prepared_url.split("/", maxsplit=1)
    language_slug, path = language_and_path.split("/", maxsplit=1)
    path_components = path.split("/")
    content_type = path_components[0]
    translation_slug = path_components[-1]

    return region_slug, language_slug, content_type, translation_slug


def get_content_model(content_type):
    """
    Get content model by content type

    :param content_type: Content type extracted from internal url path
    :type content_type: str

    :return: Data model (Page, Event or POI)
    :rtype: ~django.db.models.Model
    """
    if content_type == "events":
        return Event
    if content_type == "locations":
        return POI
    return Page


class Command(LogCommand):
    """
    Management command to automatically fix broken internal links in the whole content
    Links will be fixed in two cases:
    1. A parent page has been moved, so the slug is identical but the path is not correct anymore
    2. The slug of a page has been changed, so a link might reference an older version of a page
    """

    help = "Search & fix broken internal links in the content"

    def add_arguments(self, parser):
        """
        Define the arguments of this command

        :param parser: The argument parser
        :type parser: ~django.core.management.base.CommandParser
        """
        parser.add_argument(
            "--region-slug", help="Only fix links in the region with this slug"
        )
        parser.add_argument("--username", help="The username of the creator")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Whether changes should be written to the database",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args, region_slug, username, commit, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param region_slug: The slug of the given region
        :type region_slug: str

        :param username: The username of the creator
        :type username: str

        :param commit: Whether changes should be written to the database
        :type commit: bool

        :param \**options: The supplied keyword options
        :type \**options: dict

        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        region = get_region(region_slug) if region_slug else None
        user = get_user(username) if username else None

        # Get all broken internal urls
        broken_internal_urls = [
            url
            for url in Url.objects.all()
            if url.type == "internal" and not url.status
        ]

        for url in broken_internal_urls:
            (
                region_slug,
                language_slug,
                content_type,
                translation_slug,
            ) = parse_internal_url(url)

            if content_type in [settings.IMPRINT_SLUG, "news", "offers"]:
                # Only links to pages, events or locations can be fixed automatically
                continue

            # Find a content object by translation url
            objects = (
                get_content_model(content_type)
                .objects.filter(
                    translations__slug=slugify(translation_slug, allow_unicode=True),
                    translations__language__slug=language_slug,
                    region__slug=region_slug,
                )
                .distinct()
            )

            if len(objects) == 1:
                # Get an actual public translation of the content object
                public_translation = objects[0].get_public_translation(language_slug)
                if public_translation and public_translation.get_absolute_url().strip(
                    "/"
                ) != unquote(url.internal_url).strip("/"):
                    # If the last public url of the translation is different, perform a replacement
                    replace_links(
                        url.internal_url,
                        public_translation.get_absolute_url(),
                        region,
                        user,
                        commit,
                    )

        if commit:
            self.print_success("✔ Successfully finished fixing broken internal links.")
        else:
            self.print_info("✔ Finished dry-run of fixing broken internal links.")
