from datetime import datetime

import pytest

from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import (
    Feedback,
    RegionFeedback,
    PageFeedback,
    POIFeedback,
    EventFeedback,
    EventListFeedback,
    ImprintPageFeedback,
    MapFeedback,
    SearchResultFeedback,
    OfferListFeedback,
    OfferFeedback,
)

from .api_config import API_FEEDBACK_VIEWS, API_FEEDBACK_ERRORS


feedback_type_dict = {
    "api:region_feedback": RegionFeedback,
    "api:page_feedback": PageFeedback,
    "api:poi_feedback": POIFeedback,
    "api:event_feedback": EventFeedback,
    "api:event_list_feedback": EventListFeedback,
    "api:imprint_page_feedbacks": ImprintPageFeedback,
    "api:map_feedback": MapFeedback,
    "api:search_result_feedback": SearchResultFeedback,
    "api:offer_list_feedback": OfferListFeedback,
    "api:offer_feedback": OfferFeedback,
}


# pylint: disable=unused-argument
@pytest.mark.django_db
@pytest.mark.parametrize("view_name,post_data", API_FEEDBACK_VIEWS)
def test_api_feedback_success(load_test_data, view_name, post_data):
    """
    Check successful feedback submission for different feedback types

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: NoneType

    :param view_name: The identifier of the view
    :type view_name: str

    :param post_data: The post data for this view
    :type post_data: dict
    """
    client = Client()
    url = reverse(view_name, kwargs={"region_slug": "augsburg", "language_slug": "de"})
    response = client.post(url, data=post_data)
    assert response.status_code == 201
    assert response.json() == {"success": "Feedback successfully submitted"}

    # database checks
    assert Feedback.objects.count() == 1
    feedback = Feedback.objects.first()

    if view_name != "api:legacy_feedback_endpoint":
        assert isinstance(feedback, feedback_type_dict[view_name])

    if "rating" in post_data:
        rating = post_data["rating"] == "up"
        assert feedback.rating == rating
    else:
        assert feedback.rating is None

    if "comment" in post_data:
        assert feedback.comment == post_data["comment"]
    else:
        assert feedback.comment == ""

    is_technical = post_data["category"] == "Technisches Feedback"
    assert feedback.is_technical == is_technical
    assert feedback.created_date.date() == datetime.today().date()
    assert feedback.language_id == 1
    assert feedback.read_by_id is None
    assert feedback.region_id == 1


# pylint: disable=unused-argument
@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_name,kwargs,post_data,response_data", API_FEEDBACK_ERRORS
)
def test_api_feedback_errors(
    load_test_data, view_name, kwargs, post_data, response_data
):
    """
    Check different errors during feedback processing

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: NoneType

    :param view_name: The identifier of the view
    :type view_name: str

    :param kwargs: The keyword argument passed to the view
    :type kwargs: dict

    :param post_data: The post data for this view
    :type post_data: dict

    :param response_data: The expected response data
    :type response_data: dict
    """
    client = Client()
    url = reverse(view_name, kwargs=kwargs)
    response = client.post(url, data=post_data)
    assert response.status_code == response_data["code"]
    assert response.json() == {"error": f"{response_data['error']}"}

    # database checks
    assert not Feedback.objects.exists()


# pylint: disable=unused-argument
@pytest.mark.django_db
def test_api_feedback_invalid_method(load_test_data):
    """
    Check error when request method is not POST

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: NoneType
    """
    client = Client()
    url = reverse(
        "api:region_feedback", kwargs={"region_slug": "augsburg", "language_slug": "de"}
    )
    response = client.get(url)
    assert response.status_code == 405
    assert response.json() == {"error": "Invalid request."}

    # database checks
    assert not Feedback.objects.exists()
