"""
Helpers for reading typed settings from environment variables.
"""

from __future__ import annotations

import os


def env_int(name: str, default: int) -> int:
    """
    Read an integer setting from the environment, falling back to ``default`` if unset.
    """
    return int(os.environ.get(name, str(default)))


def env_float(name: str, default: float) -> float:
    """
    Read a float setting from the environment, falling back to ``default`` if unset.
    """
    return float(os.environ.get(name, str(default)))
