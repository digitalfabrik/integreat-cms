from playwright.sync_api import expect, Page
from pytest_django.live_server_helper import LiveServer

# pylint: disable=unused-argument


def test_login(page: Page, live_server: LiveServer, load_test_data: None) -> None:
    """
    This test serves as a playwright showcase, verifying the basic functionality of the login page.
    """
    page.goto(live_server.url)

    page.fill("input[name='username']", "root")
    page.fill("input[type='password']", "root1234")

    page.get_by_text("Anmelden").click()

    expect(page.get_by_role("heading", name="Admin Dashboard")).to_be_visible()
