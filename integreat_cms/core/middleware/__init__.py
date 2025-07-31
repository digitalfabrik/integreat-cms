"""
This package contains custom middlewares, see :doc:`django:topics/http/middleware` and :doc:`django:ref/middleware`.
"""

from __future__ import annotations

from .access_control_middleware import AccessControlMiddleware
from .debug_request import DebugRequestMiddleware
from .region_middleware import RegionMiddleware
from .timezone_middleware import TimezoneMiddleware
