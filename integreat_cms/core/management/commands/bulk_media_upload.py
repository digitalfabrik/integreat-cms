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
    Management command to upload files to the media library in bulk and produce a CSV of the upload locations.
    """

    help = "Bulk upload files to the media library and produce a CSV of the upload locations."

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
            help="The path to the directory to upload media from",
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
            help="The region slug whose media library to upload the files to",
        )
        group_output.add_argument(
            "--global",
            action="store_true",
            help="Upload the files to the global library",
        )
        parser.add_argument(
            "csv",
            help="Path to which to write the CSV information of successfully uploaded files, along with their new location on disk",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        # INPUT VALIDATION & PREPARATION
        if not (options["zip"] or options["dir"]):
            # We need at least one of the options, else we cannot do anything
            raise CommandError("Specify --zip or --directory")
        if not (options["region"] or options["global"]):
            raise CommandError("Specify --global or a --region")
        if options["region"] is not None:
            # Find the region belonging to the slug
            # This simultaneously validates the slug, since this will throw an exception if no matching region is found
            options["region"] = Region.objects.get(slug=options["region"])
            # If no region is given, the global library is meant (represented by None in our model, so no need to do anything special and can just use options["region"])
        # Determine the directory object representing the given destination path
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
                        # Build the string to report which library it is
                        realm = (
                            f"region {options['region'].slug}"
                            if options["region"]
                            else "global"
                        )
                        raise CommandError(
                            f"Directory not found ({realm}): {options['dest']} (use --parents to automatically create missing directories)",
                        ) from e
        # Make an object to pass into functions for reporting
        stats: dict[str, set] = {
            "successful": set(),
            "failed": set(),
        }

        # DO THE UPLOADING
        with (
            open(options["csv"], "w") as out
        ):  # TODO(PeterNerlich): Fail if file exists (and add --force option?)  # noqa: TD003, FIX002
            # Write out the CSV header
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
            # Keep track of recursion levels
            root = str(path)
        # Ensure sane and usable stats, even if not or only partially given
        stats = {
            "successful": set(),
            "failed": set(),
        } | (stats if stats is not None else {})
        # The region is always that of the parent directory, we don't mix regions
        # (In the media library, the user always sees the items from the global library in addition to their own, even if the names coincide)
        region = destination.region if destination is not None else options["region"]

        # Gather files and directories before processing them
        files = set()
        dirs = set()
        for item in path.iterdir():
            if item.is_file():
                files.add(item)
            elif item.is_dir() and options.get("recursive", False):
                dirs.add(item)
        if files:
            # For each file, create and submit an instance of the upload form and mimic how files would be passed to it from the webserver normally
            # The query data is the same for all files in a directory
            query = QueryDict("", mutable=True)
            query["parent_directory"] = destination

            for file_path in files:
                relative_path = (
                    str(file_path).removeprefix(str(root))
                    if isinstance(file_path, ZipPath)
                    else file_path.relative_to(root)
                )
                with file_path.open("rb") as data:
                    # Find out the uncompressed size by moving to the end of the data stream
                    data.seek(0, 2)
                    uncompressed_size = data.tell()
                    # Seek back to the start, so when the form is submitted it doesn't complain that it is invalid
                    data.seek(0)
                    # Find out the mime type
                    mimetype = mimetypes.guess_type(str(file_path))[0]
                    # Mimic the way a file uploaded by a user is normally passed to the form
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
                    # Initialize the mediafile object with None already, so we can later check whether we were successful or not
                    mediafile: MediaFile | None = None
                    form = UploadMediaFileForm(data=query, files=file_data)
                    # We need to set the region manually (normally done directly by upload_file_ajax() in media_actions.py)
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
                            continue
                    except (UnicodeDecodeError, IntegrityError):
                        logger.exception("File could not be read")
                    if mediafile:
                        stats["successful"].add(relative_path)
                        if created is not None:
                            created.write(f"{relative_path},{mediafile.file}" + "\n")
                    else:
                        # I'm not quite sure whether there's actually a case where form.save() would not return a valid object
                        # while form.is_valid() was True – I'm hoping for a confident reviewer to know and clearify this… *puppy eyes*
                        # If not, then this would move up into the exception handler and the branch above into a finally: clause
                        stats["failed"].add(relative_path)
                        logger.error("Upload failed: %s", relative_path)

        if dirs:
            # Make one or two single queries now instead of one for each individual subdir or file
            library_dirs = {
                directory.name: directory
                for directory in Directory.objects.filter(
                    parent=destination, region=region
                )
            }
            library_files = MediaFile.objects.filter(
                parent_directory=destination, region=region
            ).values_list("name")

            for item in dirs:
                relative_path = (
                    str(item).removeprefix(str(root))
                    if isinstance(item, ZipPath)
                    else item.relative_to(root)
                )
                if item.name not in library_dirs:
                    # Build the string to report which library it is
                    realm = f"region {region.slug}" if region else "global"
                    # If we never encounter a directory that does not already exist in the library, django doesn't even send the query for library_files to the database! :tada:
                    if item.name in library_files:
                        logger.error(
                            "Not a directory (%s): %s",
                            realm,
                            relative_path,
                        )
                        continue
                    if "parents" in options:
                        library_dir = Directory.objects.create(
                            name=item.name,
                            region=region,
                            parent=destination,
                        )
                    else:
                        logger.error(
                            "Directory not found (%s): %s (use --parents to automatically create missing directories)",
                            realm,
                            relative_path,
                        )
                        continue
                else:
                    library_dir = library_dirs[item.name]
                self.upload_directory(
                    item,
                    destination=library_dir,
                    root=root,
                    created=created,
                    stats=stats,
                    **options,
                )
