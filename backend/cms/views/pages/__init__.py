"""
Python standard Init-File
"""
from .pages import PageTreeView
from .page import (
    PageView,
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
from .archive import ArchivedPagesView
from .sbs_page import SBSPageView
