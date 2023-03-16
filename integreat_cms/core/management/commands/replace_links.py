import logging

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError

from ....cms.models import Region
from ....cms.utils.linkcheck_utils import replace_links
from ..log_command import LogCommand

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to replace links in the whole content
    """

    help = "Search & replace links in the content"

    def add_arguments(self, parser):
        """
        Define the arguments of this command

        :param parser: The argument parser
        :type parser: ~django.core.management.base.CommandParser
        """
        parser.add_argument("search", help="The (partial) URL to search")
        parser.add_argument("replace", help="The (partial) URL to replace")
        parser.add_argument(
            "--region-slug", help="Only replace links in the region with this slug"
        )
        parser.add_argument("--username", help="The username of the creator")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Whether changes should be written to the database",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args, search, replace, region_slug, username, commit, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param search: The (partial) URL to search
        :type search: str

        :param replace: The (partial) URL to replace
        :type replace: str

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
        if region_slug:
            try:
                region = Region.objects.get(slug=region_slug)
            except Region.DoesNotExist as e:
                raise CommandError(
                    f'Region with slug "{region_slug}" does not exist.'
                ) from e
        else:
            region = None
        if username:
            try:
                user = get_user_model().objects.get(username=username)
            except get_user_model().DoesNotExist as e:
                raise CommandError(
                    f'User with username "{username}" does not exist.'
                ) from e
        else:
            user = None

        replace_links(search, replace, region, user, commit)

        if commit:
            self.print_success(
                f'✔ Successfully replaced "{search}" with "{replace}" in content links.'
            )
        else:
            self.print_info(
                f'✔ Finished dry-run of replacing "{search}" with "{replace}" in content links.'
            )
