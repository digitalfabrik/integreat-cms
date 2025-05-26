from __future__ import annotations

import pytest
from django.db import IntegrityError

from integreat_cms.cms.models import Language, LanguageTreeNode, Region


@pytest.mark.django_db
def test_inactive_requires_invisible() -> None:
    """
    Test whether the constraint that does not allow ltn with both active=False and visible=True
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    new_language = Language.objects.create(
        slug="op-test",
        bcp47_tag="oper",
        native_name="Old Persian",
        english_name="Altpersisch",
        text_direction="ltr",
        primary_country_code="OPER",
        table_of_contents="frakaara",
    )
    region = Region.objects.create(name="Testregion")
    with pytest.raises(
        IntegrityError, match="language_tree_node_inactive_requires_invisible"
    ):
        LanguageTreeNode.add_root(
            region=region, language=new_language, visible=True, active=False
        )
