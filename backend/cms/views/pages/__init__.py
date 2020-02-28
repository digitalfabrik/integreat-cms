"""
Python standard Init-File
"""
from .page_tree_view import PageTreeView
from .page_view import PageView
from .page_actions import (
    archive_page,
    restore_page,
    view_page, delete_page,
    download_page_xliff,
    upload_page,
    move_page,
    grant_page_permission_ajax,
    revoke_page_permission_ajax,
    get_pages_list_ajax,
    save_mirrored_page
)
from .page_sbs_view import PageSideBySideView
