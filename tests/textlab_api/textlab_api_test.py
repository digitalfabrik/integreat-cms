import pytest

from integreat_cms.cms.views.utils.hix import normalize_text
from tests.textlab_api.textlab_config import TEXTLAB_NORMALIZE_TEXT


@pytest.mark.parametrize("input,output", TEXTLAB_NORMALIZE_TEXT)
def test_normalize_text(
    input: str,
    output: str,
) -> None:
    """
    Test for the text normalization function that is applied before sending text to the TextLab API
    """
    assert output == normalize_text(input)
