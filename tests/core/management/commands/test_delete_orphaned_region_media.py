from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from integreat_cms.cms.models import Region
from integreat_cms.cms.utils.media_utils import get_region_media_directory

from ..utils import get_command_output

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_django.fixtures import Settings

ORPHANED_REGION_ID = 999999
UNEXPECTED_DIRECTORY_NAMES = ("unexpected", f"0{ORPHANED_REGION_ID}", "²")


@pytest.fixture(name="media_directories")
def fixture_media_directories(
    load_test_data: None,
    settings: Settings,
    tmp_path: Path,
) -> tuple[Path, Path, list[Path]]:
    """
    Create media directories of an existing region, of a non-existing region and unexpected directories

    :param load_test_data: The fixture providing the test data
    :param settings: The Django settings
    :param tmp_path: A temporary directory
    :return: The existing, orphaned and unexpected directories
    """
    settings.MEDIA_ROOT = str(tmp_path)
    existing = get_region_media_directory(Region.objects.first().id)
    orphaned = get_region_media_directory(ORPHANED_REGION_ID)
    unexpected = [tmp_path / "regions" / name for name in UNEXPECTED_DIRECTORY_NAMES]
    for directory in (existing, orphaned, *unexpected):
        directory.mkdir(parents=True)
        (directory / "file.png").touch()
    return existing, orphaned, unexpected


@pytest.mark.django_db
def test_delete_orphaned_region_media(
    media_directories: tuple[Path, Path, list[Path]],
) -> None:
    """
    Ensure that only media directories of non-existing regions are deleted
    """
    existing, orphaned, unexpected = media_directories
    out, err = get_command_output("delete_orphaned_region_media")
    assert f"Deleted orphaned media directory {orphaned}" in out
    assert not orphaned.exists()
    assert existing.exists()
    for directory in unexpected:
        assert f"Skipping unexpected directory {directory}" in err
        assert directory.exists()


@pytest.mark.django_db
def test_delete_orphaned_region_media_dry_run(
    media_directories: tuple[Path, Path, list[Path]],
) -> None:
    """
    Ensure that no directories are deleted in dry run mode
    """
    existing, orphaned, unexpected = media_directories
    out, _ = get_command_output("delete_orphaned_region_media", dry_run=True)
    assert f"Found orphaned media directory {orphaned}" in out
    assert orphaned.exists()
    assert existing.exists()
    for directory in unexpected:
        assert directory.exists()


@pytest.mark.django_db
def test_delete_orphaned_region_media_without_orphans(
    load_test_data: None,
    settings: Settings,
    tmp_path: Path,
) -> None:
    """
    Ensure that the command handles the absence of orphaned directories
    """
    settings.MEDIA_ROOT = str(tmp_path)
    out, err = get_command_output("delete_orphaned_region_media")
    assert "No region media directory found" in out
    assert not err
    (tmp_path / "regions").mkdir()
    out, err = get_command_output("delete_orphaned_region_media")
    assert "No orphaned region media directories found." in out
    assert not err
