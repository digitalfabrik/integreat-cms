"""
Registry of the available news source managers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .pushnews_manager import PushnewsManager
from .tunews_manager import TunewsManager

if TYPE_CHECKING:
    from typing import Final

    from .abstract_news_manager import AbstractNewsManager

PUSHNEWS: Final[PushnewsManager] = PushnewsManager()
TUNEWS: Final[TunewsManager] = TunewsManager()

CHOICES: Final[list[AbstractNewsManager]] = [PUSHNEWS, TUNEWS]
