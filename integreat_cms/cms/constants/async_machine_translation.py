"""
This module contains the content types which are machine translated asynchronously via Celery.
All other content types are still translated synchronously within the request.
See ``ADR/0005-scope-async-machine-translation-to-pages.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final


#: Only add a content type together with its progress UI
CONTENT_TYPES: Final[frozenset[str]] = frozenset({"page"})
