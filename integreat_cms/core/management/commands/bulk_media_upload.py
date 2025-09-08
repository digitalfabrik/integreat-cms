import io
import logging
import mimetypes
from pathlib import Path
from typing import Any
from zipfile import Path as ZipPath
from zipfile import ZipFile

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import CommandError, CommandParser
from django.db.utils import IntegrityError
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict

from integreat_cms.cms.forms.media.upload_media_file_form import UploadMediaFileForm
from integreat_cms.cms.models.media.media_file import Directory, MediaFile
from integreat_cms.cms.models.regions.region import Region

from ..log_command import LogCommand

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to change references of media files from a source path to a target path.
    This command reads a CSV file and then changes the reference from the first column (source path) to the second column (target path).
    """

    help = "Bulk upload files to the media library and print a CSV of the upload locations to stdout."

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        group_input = parser.add_argument_group("Input")
        group_input.add_argument(
            "--zip",
            help="The path to the zip archive to upload media from",
        )
        group_input.add_argument(
            "--dir",
            "--directory",
            help="The path to the directory file to upload media from",
        )
        group_input.add_argument(
            "-r",
            "--recursive",
            action="store_true",
            help="Recursively descend into sub directories and upload their contents as well",
        )

        group_output = parser.add_argument_group("Output")
        group_output.add_argument(
            "--dest",
            "--destination",
            help='The "path" to the directory inside the media library to which the media should be uploaded to',
        )
        group_output.add_argument(
            "-p",
            "--parents",
            action="store_true",
            help="Make parent directories as needed",
        )
        group_output.add_argument(
            "--region",
            default=None,
            help="The region slug whose media library to upload the files to (upload to global library if not given)",
        )
        parser.add_argument(
            "csv",
            help="Path to which to write the CSV information of successfully uploaded files, along with their new location on disk",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if not options["zip"] or options["dir"]:
            raise CommandError("Specify --zip or --directory")
        if options["region"]:
            options["region"] = Region.objects.get(slug=options["region"])
        destination: Directory | None = None
        if options["dest"]:
            for part in Path(options["dest"]).parts:
                if options["parents"]:
                    destination = Directory.objects.get_or_create(
                        name=part,
                        region=options["region"],
                        parent=destination,
                    )[0]
                else:
                    try:
                        destination = Directory.objects.get(
                            name=part,
                            region=options["region"],
                            parent=getattr(destination, "id", None),
                        )
                    except Directory.DoesNotExist as e:
                        realm = (
                            f"region {options['region'].slug}"
                            if options["region"]
                            else "global"
                        )
                        raise CommandError(
                            f"Directory not found ({realm}): {options['dest']} (use --parents to automatically create missing directories)",
                        ) from e
        stats: dict[str, set] = {
            "successful": set(),
            "failed": set(),
        }
        with open(options["csv"], "w") as out:
            out.write("name,upload_path\n")
            if options["zip"]:
                with ZipFile(options["zip"]) as zipfile:
                    self.upload_directory(
                        path=ZipPath(zipfile),
                        destination=destination,
                        created=out,
                        stats=stats,
                        **options,
                    )
            if options["dir"]:
                self.upload_directory(
                    path=Path(options["dir"]),
                    destination=destination,
                    created=out,
                    stats=stats,
                    **options,
                )

        logger.info(
            "DONE  Uploaded %r files (%r failed)",
            len(stats["successful"]),
            len(stats["failed"]),
        )

    def upload_directory(
        self,
        path: Path | ZipPath,
        destination: Directory | None,
        root: str | None = None,
        created: io.TextIOBase | None = None,
        stats: dict[str, set] | None = None,
        **options: dict[str, Any],
    ) -> None:
        """
        Upload all files in a directory to the destination directory in the media library
        """
        if root is None:
            root = str(path)
        # Make a sane default for stats
        stats = {
            "successful": set(),
            "failed": set(),
        } | (stats if stats is not None else {})
        # The region is always that of the parent directory, we don't mix regions
        region = destination.region if destination is not None else options["region"]

        files = set()
        dirs = set()
        for item in path.iterdir():
            if item.is_file():
                files.add(item)
            elif item.is_dir() and options.get("recursive", False):
                dirs.add(item)
        if files:
            query = QueryDict("", mutable=True)
            query["parent_directory"] = destination
            for file_path in files:
                relative_path = (
                    str(file_path).removeprefix(str(root))
                    if isinstance(file_path, ZipPath)
                    else file_path.relative_to(root)
                )
                with file_path.open() as data:
                    # Find out the uncompressed size
                    data.seek(0, 2)
                    uncompressed_size = data.tell()
                    # Seek back to the start
                    data.seek(0)
                    mimetype = mimetypes.guess_type(str(file_path))[0]
                    file_data = MultiValueDict(
                        {
                            "file": [
                                InMemoryUploadedFile(
                                    file=data,
                                    field_name="file",
                                    name=file_path.name,
                                    content_type=mimetype,
                                    size=uncompressed_size,
                                    charset=None,
                                    content_type_extra=None,
                                )
                            ]
                        }
                    )
                    mediafile = None
                    form = UploadMediaFileForm(data=query, files=file_data)
                    form.instance.region = region
                    try:
                        if form.is_valid():
                            mediafile = form.save()
                        else:
                            stats["failed"].add(relative_path)
                            logger.error(
                                "Cannot upload %s:  %r",
                                relative_path,
                                form.get_error_messages(),
                            )
                    except (UnicodeDecodeError, IntegrityError):
                        pass
                    if mediafile:
                        stats["successful"].add(relative_path)
                        if created is not None:
                            created.write(f"{relative_path},{mediafile.file}" + "\n")
                    else:
                        stats["failed"].add(relative_path)
                        logger.error("Upload failed: %s", relative_path)
        if dirs:
            # Make one single query now instead of one for each individual subdir or file
            child_dirs = {
                directory.name: directory
                for directory in Directory.objects.filter(
                    parent=destination, region=region
                )
            }
            child_files = MediaFile.objects.filter(
                parent_directory=destination, region=region
            ).values_list("name")

            for item in dirs:
                relative_path = (
                    str(item).removeprefix(str(root))
                    if isinstance(item, ZipPath)
                    else item.relative_to(root)
                )
                if item.name not in child_dirs:
                    realm = f"region {region.slug}" if region else "global"
                    if item.name in child_files:
                        logger.error(
                            "Not a directory (%s): %s",
                            realm,
                            relative_path,
                        )
                        continue
                    if "parents" not in options:
                        logger.error(
                            "Directory not found (%s): %s (use --parents to automatically create missing directories)",
                            realm,
                            relative_path,
                        )
                        continue
                    child_dir = Directory.objects.create(
                        name=item.name,
                        region=region,
                        parent=destination,
                    )
                else:
                    child_dir = child_dirs[item.name]
                self.upload_directory(
                    item, child_dir, root=root, created=created, stats=stats, **options
                )
