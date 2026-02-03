from __future__ import annotations

from .contact_utils import get_contact, get_contact_raw, search_contact_ajax
from .content_edit_lock import content_edit_lock_heartbeat, content_edit_lock_release
from .hix import get_hix_score
from .machine_translations import build_json_for_machine_translation
from .search_content_ajax import search_content_ajax
from .slugify_ajax import slugify_ajax
from .translation_coverage import get_translation_and_word_count
from .user import get_pages_observer_has_access_to
