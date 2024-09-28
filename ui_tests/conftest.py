import pytest
from django.core.management import call_command
from pytest_django.plugin import DjangoDbBlocker

# pylint: disable=unused-argument


@pytest.fixture(scope="session")
def load_test_data(django_db_setup: None, django_db_blocker: DjangoDbBlocker) -> None:
    """
    Load the test data initially for all test cases

    :param django_db_setup: The fixture providing the database availability
    :param django_db_blocker: The fixture providing the database blocker
    """
    with django_db_blocker.unblock():
        call_command("loaddata", "integreat_cms/cms/fixtures/test_data.json")
