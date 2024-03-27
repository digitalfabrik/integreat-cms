"""
This package contains all views related to pages
"""

from __future__ import annotations

from .page_actions import (
    archive_page,
    cancel_translation_process_ajax,
    delete_page,
    expand_page_translation_id,
    get_page_content_ajax,
    get_page_order_table_ajax,
    move_page,
    preview_page_ajax,
    refresh_date,
    render_mirrored_page_field,
    restore_page,
    upload_xliff,
)
from .page_bulk_actions import (
    ExportMultiLanguageXliffView,
    ExportXliffView,
    GeneratePdfView,
)
from .page_form_view import PageFormView
from .page_permission_actions import (
    grant_page_permission_ajax,
    revoke_page_permission_ajax,
)
from .page_sbs_view import PageSideBySideView
from .page_tree_view import PageTreeView
from .page_version_view import PageVersionView
from .page_xliff_import_view import PageXliffImportView
from .partial_page_tree_view import render_partial_page_tree_views
