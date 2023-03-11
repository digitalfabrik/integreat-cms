import pytest
from django.core.management.base import CommandError

from integreat_cms.cms.models import Page

from ..utils import get_command_output


def test_find_missing_versions_missing_model():
    """
    Ensure that missing model cause an error
    """
    with pytest.raises(CommandError) as exc_info:
        out, err = get_command_output("find_missing_versions")
        assert out == err == ""
    assert str(exc_info.value) == "Error: the following arguments are required: model"


def test_find_missing_versions_invalid_model():
    """
    Ensure that an invalid model throws an error
    """
    with pytest.raises(CommandError) as exc_info:
        out, err = get_command_output("find_missing_versions", "invalid")
        assert out == err == ""
    assert (
        str(exc_info.value)
        == "Error: argument model: Invalid model (must be either page, event or poi)"
    )


# pylint: disable=unused-argument
@pytest.mark.django_db
@pytest.mark.parametrize("model", ["page", "event", "poi"])
def test_find_missing_versions_success(load_test_data, model):
    """
    Ensure no errors are found in default test data
    """
    out, err = get_command_output("find_missing_versions", model)
    assert "✔ All versions are consistent." in out
    assert err == ""


# pylint: disable=unused-argument
@pytest.mark.django_db
def test_find_missing_versions_failure(load_test_data):
    """
    Ensure that inconsistencies are listed
    """
    # Create version inconsistency
    page_translation = Page.objects.get(id=1).get_translation("de")
    page_translation.version += 1
    page_translation.save()
    out, err = get_command_output("find_missing_versions", "page")
    assert "Checking the model PageTranslation for version inconsistencies..." in out
    assert err == (
        "The latest version of <Page (id: 1, region: augsburg, slug: willkommen)>"
        " in <Language (id: 1, slug: de, name: German)>"
        " is 3, but there are only 2 translation objects!\n"
    )
