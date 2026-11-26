"""
Test that the PDF export cannot be abused to read local files or to access internal services
"""

from __future__ import annotations

import io
import socket
from typing import TYPE_CHECKING

import pytest
from weasyprint import HTML

from integreat_cms.cms.templatetags.pdf_filters import pdf_strip_attachments
from integreat_cms.cms.utils.pdf_utils import (
    PdfUrlFetcher,
    resolve_pdf_uri,
    validate_remote_pdf_url,
)

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from pytest_django.fixtures import SettingsWrapper

#: These tests need neither the database nor the network
pytestmark = pytest.mark.unit

CANARY = "TOP-SECRET-CANARY"

#: The marker of a file which is embedded into a PDF
EMBEDDED_FILE = b"EmbeddedFile"


@pytest.fixture
def media_root(tmp_path: Path, settings: SettingsWrapper) -> Path:
    """
    Provide a media directory with one file inside and one secret file outside of it

    :param tmp_path: The fixture providing a temporary directory
    :param settings: The fixture providing the django settings
    :return: The temporary directory which contains the ``media`` directory
    """
    media = tmp_path / "media"
    media.mkdir()
    (media / "image.png").write_bytes(b"image")
    (tmp_path / "secret.txt").write_text(CANARY)
    (media / "link.txt").symlink_to(tmp_path / "secret.txt")
    settings.MEDIA_ROOT = str(media)
    return tmp_path


def test_resolve_pdf_uri_media_file(media_root: Path) -> None:
    """
    Files inside the media directory can still be resolved

    :param media_root: The fixture providing the media directory
    """
    assert resolve_pdf_uri("/media/image.png") == str(media_root / "media/image.png")
    assert resolve_pdf_uri("http://localhost:8000/media/image.png") == str(
        media_root / "media/image.png"
    )


@pytest.mark.parametrize(
    "uri",
    [
        "/media/../secret.txt",
        "/media/%2e%2e/secret.txt",
        "/media/%2E%2E%2Fsecret.txt",
        "/media/%252e%252e/secret.txt",
        "/media/link.txt",
        "http://localhost:8000/media/%2e%2e/secret.txt",
        "/static/../secret.txt",
        "/static/%2e%2e/secret.txt",
        "../../secret.txt",
    ],
)
def test_resolve_pdf_uri_path_traversal(media_root: Path, uri: str) -> None:
    """
    Paths which leave the media or static directories are not resolved

    :param media_root: The fixture providing the media directory
    :param uri: The malicious URI
    """
    assert resolve_pdf_uri(uri) is None
    assert resolve_pdf_uri(uri.replace("secret.txt", "/etc/passwd")) is None


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "FILE:///etc/passwd",
        "ftp://example.com/file",
        "http://127.0.0.1:1/",
        "http://localhost:1/",
        "http://[::1]:1/",
        "http://[::ffff:127.0.0.1]:1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://0.0.0.0/",
        "http:///no-host",
    ],
)
def test_pdf_url_fetcher_refuses_url(url: str) -> None:
    """
    Local files, unknown protocols and hosts in internal networks are refused

    :param url: The malicious URL
    """
    with pytest.raises(ValueError):
        PdfUrlFetcher().fetch(url)


def test_validate_remote_pdf_url_resolves_hostname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Hostnames are judged by the addresses they resolve to

    :param monkeypatch: The fixture providing the monkeypatch
    """

    def fake_getaddrinfo(host: str, *args: Any, **kwargs: Any) -> list[tuple]:
        address = "10.1.2.3" if host == "internal.example.com" else "93.184.215.14"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 80))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    validate_remote_pdf_url("https://public.example.com/image.png")
    with pytest.raises(ValueError, match="non-public"):
        validate_remote_pdf_url("https://internal.example.com/image.png")


def test_pdf_strip_attachments() -> None:
    """
    The ``rel`` attribute is removed and escaped markup stays escaped
    """
    content = (
        '<div><a REL="nofollow Attachment" href="https://example.com">link</a>'
        '&lt;a rel="attachment" href="file:///etc/passwd"&gt;x&lt;/a&gt;</div>'
    )
    result = pdf_strip_attachments(content)
    assert " rel=" not in result.lower().replace("&lt;a rel=", "")
    assert '<a href="https://example.com">link</a>' in result
    assert "&lt;a rel=" in result


@pytest.mark.parametrize(
    "href",
    [
        "/media/%2e%2e/secret.txt",
        "file://{root}/secret.txt",
    ],
)
def test_pdf_does_not_embed_local_files(media_root: Path, href: str) -> None:
    """
    Even if an attachment link reaches WeasyPrint, the file is not embedded

    :param media_root: The fixture providing the media directory
    :param href: The malicious link target
    """
    html = f'<a rel="attachment" href="{href.format(root=media_root)}">x</a>'
    pdf = io.BytesIO()
    HTML(
        string=html,
        base_url="http://localhost:8000",
        url_fetcher=PdfUrlFetcher(),
    ).write_pdf(target=pdf, pdf_forms=False, uncompressed_pdf=True)
    assert CANARY.encode() not in pdf.getvalue()
    assert EMBEDDED_FILE not in pdf.getvalue()
