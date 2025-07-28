import csv
import logging
import select
import sys
from typing import Any

from django.core.management.base import CommandParser
from django.db import connection

from integreat_cms.cms.models.media.media_file import Directory, MediaFile
from integreat_cms.cms.models.pages.page import Page

from ..log_command import LogCommand

logger = logging.getLogger(__name__)


def get_mixed_tree_paths() -> dict[str, Any]:
    """
    Recursively builds paths for both Directory and MediaFile objects.
    The CTE will first build paths for directories and then attach MediaFile objects.
    """
    # Get the table names dynamically
    directory_table = Directory._meta.db_table
    mediafile_table = MediaFile._meta.db_table

    # ruff: noqa: S608
    with connection.cursor() as cursor:
        cursor.execute(f"""
            WITH RECURSIVE directory_tree(id, name, parent_id, full_path, is_directory) AS (
                -- Base case: Select root directories (parent_id IS NULL)
                SELECT id, name, parent_id, name::TEXT AS full_path, TRUE
                FROM {directory_table}
                WHERE parent_id IS NULL

                UNION ALL

                -- Recursive case: Join directories and their subdirectories (children)
                SELECT d.id, d.name, d.parent_id, (dt.full_path || '/' || d.name)::TEXT, TRUE
                FROM {directory_table} d
                JOIN directory_tree dt ON d.parent_id = dt.id
            ),
            mediafile_tree AS (
                -- MediaFile case: Attach MediaFile objects to the full path of the parent directory
                SELECT mf.id, mf.name, mf.parent_directory_id AS parent_id, (dt.full_path || '/' || mf.name)::TEXT AS full_path, FALSE AS is_directory
                FROM {mediafile_table} mf
                JOIN directory_tree dt ON mf.parent_directory_id = dt.id
            )

            -- Combine the results from both directories and media files
            SELECT id, full_path, is_directory FROM directory_tree
            UNION ALL
            SELECT id, full_path, is_directory FROM mediafile_tree;
        """)

        rows = cursor.fetchall()
        return {row[1]: {"id": row[0], "is_directory": row[2]} for row in rows}


class Command(LogCommand):
    """
    Management command to change references of media files from a source path to a target path.
    This command reads a CSV file and then changes the reference from the first column (source path) to the second column (target path).
    """

    help = "Replace references of media files from source paths with target paths based on a CSV file."

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "path",
            nargs="?",
            default=None,
            help="The path to the csv file we want to import from",
        )

    def should_stdin_be_used(self, options: dict) -> bool:
        return bool(
            sys.platform != "win32"
            and not sys.stdin.isatty()
            and select.select([sys.stdin], [], [], 0)[0]
            and not options["path"]
        )

    def handle(self, *args: Any, **options: Any) -> None:
        successful = 0
        failed = 0

        with (
            open(options["path"], newline="")
            if not self.should_stdin_be_used(options)
            else sys.stdin as csvfile
        ):
            reader = csv.reader(csvfile, delimiter=",", quotechar="|")
            next(reader, None)
            full_path_lookup = get_mixed_tree_paths()

            for row in reader:
                path = {
                    "old": (
                        row[0]
                        .removeprefix("https://")
                        .removeprefix("admin.integreat-app.de/media/")
                        .removeprefix("cms.integreat-app.de/media/")
                    ),
                    "new": (
                        row[1]
                        .removeprefix("https://")
                        .removeprefix("admin.integreat-app.de/media/")
                        .removeprefix("cms.integreat-app.de/media/")
                    ),
                }
                file = {"old": None, "new": None}

                for which, p in path.items():
                    try:
                        file[which] = MediaFile.objects.get(
                            file=p,
                        )
                    except MediaFile.DoesNotExist:
                        logger.info(
                            "%r path is not valid. Old path was %r and new path was %r",
                            which,
                            path["old"],
                            path["new"],
                        )

                if file["old"] and file["new"]:
                    pages = Page.objects.filter(
                        explicitly_archived=False, icon=file["old"]
                    )
                    for page in pages:
                        logger.info("page %r found", page)
                        page.icon = file["new"]
                        page.save()

                    successful += 1
                else:
                    failed += 1

        logger.info("DONE  Replaced %r files (%r failed)", successful, failed)
