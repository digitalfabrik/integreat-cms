from __future__ import annotations

import pytest
from django.core.management.base import CommandError

from ..utils import get_command_output


def test_find_large_files_invalid_limit() -> None:
    """
    Ensure that a negative limit throws an error
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("find_large_files", limit=-10))
    assert str(exc_info.value) == "The limit cannot be negative."


def test_find_large_files_exceeding_limit() -> None:
    """
    Ensure that a too high limit throws an error
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("find_large_files", limit=999))
    assert str(exc_info.value) == "Please select a limit smaller than 100."


def test_find_large_files_invalid_threshold() -> None:
    """
    Ensure that a negative threshold throws an error
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("find_large_files", threshold=-10))
    assert str(exc_info.value) == "The threshold cannot be negative."


@pytest.mark.django_db
def test_find_large_files_valid_limit() -> None:
    """
    Ensure that changing the limit works
    """
    out, err = get_command_output("find_large_files", limit=5)
    assert "Searching the largest 5 media with more than 3MiB..." in out
    assert not err


@pytest.mark.django_db
def test_find_large_files_valid_threshold() -> None:
    """
    Ensure that increasing the threshold works
    """
    out, err = get_command_output("find_large_files", threshold=5)
    assert "Searching the largest 10 media with more than 5MiB..." in out
    assert not err


@pytest.mark.django_db
def test_find_large_files() -> None:
    """
    Ensure that finding large files works
    """
    out, err = get_command_output("find_large_files")
    assert "No files found with these filters." in out
    assert not err
