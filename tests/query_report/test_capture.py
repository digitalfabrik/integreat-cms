from __future__ import annotations

import pytest
from django.db import connection
from django.test.client import Client

from integreat_cms.cms.models import Region

from .capture import record_queries


@pytest.mark.django_db
def test_records_orm_queries() -> None:
    """
    Every executed ORM query is recorded with the test as its call site.
    """
    with record_queries() as records:
        Region.objects.count()
        Region.objects.count()
    assert len(records) == 2
    call_sites = [record.call_site for record in records]
    assert all("test_capture.py" in call_site for call_site in call_sites), call_sites
    assert all(record.route is None for record in records)


@pytest.mark.django_db
def test_records_route_for_client_request(load_test_data: None) -> None:
    """
    Queries executed while handling a test client request are attributed to the resolved URL route.
    """
    client = Client()
    with record_queries() as records:
        response = client.get("/api/v3/regions/")
    assert response.status_code == 200
    assert records
    assert {record.route for record in records} == {"api/v3/regions/"}
    assert len({record.request_id for record in records}) == 1
    assert all(record.call_site.startswith("integreat_cms/") for record in records)


@pytest.mark.django_db
def test_no_wrapper_after_exit() -> None:
    """
    The recorder is removed from the connection once the context is left.
    """
    before = list(connection.execute_wrappers)
    with record_queries():
        assert len(connection.execute_wrappers) == len(before) + 1
    assert connection.execute_wrappers == before
