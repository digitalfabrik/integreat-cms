"""
This package contains the shortcodes which reference other objects from the content of a
translation, and the conversions between those shortcodes and the html they represent.

References are stored as shortcodes so that they are only resolved when the content is
requested (see ``ADR/0001-compose-referenced-objects-into-content-dynamically-shortcodes.md``).
That happens in two flavours:

* :func:`~integreat_cms.cms.utils.shortcodes.conversion.expand_shortcodes_for_delivery` builds
  the representation which is delivered to end users
* :func:`~integreat_cms.cms.utils.shortcodes.conversion.expand_shortcodes_for_cms` builds the
  representation which is presented to users of the CMS, because editors should not have to
  care about shortcodes at all

Whatever the CMS gets back is turned into shortcodes again by
:func:`~integreat_cms.cms.utils.shortcodes.conversion.collapse_into_shortcodes`, so that
references to internal content never reach the link index kept by our ``linkcheck`` dependency.

All three are implemented by the shortcodes themselves, see
:class:`~integreat_cms.cms.utils.shortcodes.base.Shortcode` and
:class:`~integreat_cms.cms.utils.shortcodes.base.EditableShortcode`.
"""

from __future__ import annotations

from .base import EditableShortcode, Shortcode
from .conversion import (
    collapse_into_shortcodes,
    expand_shortcodes_for_cms,
    expand_shortcodes_for_delivery,
)
from .registry import editable_shortcodes, get_shortcodes, register
