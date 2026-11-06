"""
Shared type aliases for machine translation task tracking, kept separate from
:mod:`~integreat_cms.core.utils.machine_translation_celery_task` so that
``cms.models``/``cms.templatetags`` modules can use them without importing a
module that pulls in ``User``/``Region`` (and, transitively, the content
models themselves) at module level.
"""

from __future__ import annotations

type ObjectIdAndLanguageSlug = tuple[int, str]
