"""
Python standard Init-File
"""
from .page_tree_view import PageTreeView
from .page_view import PageView
from .page_actions import (
    archive_page,
    restore_page,
    view_page,
    delete_page,
    copy_link,
    redirect_to_view,
    download_xliff,
    upload_xliff,
    confirm_xliff_import,
    move_page,
    grant_page_permission_ajax,
    revoke_page_permission_ajax,
    get_page_order_table_ajax,
    get_new_page_order_table_ajax,
    get_pages_list_ajax,
    save_mirrored_page,
)
from .page_sbs_view import PageSideBySideView
from .page_revision_view import PageRevisionView
