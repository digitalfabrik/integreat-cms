"""
This modules contains the config for the sitemap tests
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

#: The sitemaps
SITEMAPS: Final[list[tuple[str, str, int]]] = [
    (
        "/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-index.xml",
        38,
    ),
    (
        "/augsburg/de/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-augsburg-de.xml",
        147,
    ),
    (
        "/augsburg/en/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-augsburg-en.xml",
        133,
    ),
    (
        "/augsburg/ar/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-augsburg-ar.xml",
        111,
    ),
    (
        "/augsburg/fa/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-augsburg-fa.xml",
        83,
    ),
    (
        "/nurnberg/de/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-nurnberg-de.xml",
        73,
    ),
    (
        "/nurnberg/en/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-nurnberg-en.xml",
        52,
    ),
    (
        "/nurnberg/ar/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-nurnberg-ar.xml",
        31,
    ),
    (
        "/nurnberg/fa/sitemap.xml",
        "tests/sitemap/expected-sitemaps/sitemap-nurnberg-fa.xml",
        24,
    ),
]
