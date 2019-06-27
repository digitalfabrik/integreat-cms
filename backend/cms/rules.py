from rules import add_rule, add_perm, predicate


# Predicates

@predicate
def is_page_editor(user, page):
    if not page:
        return False
    return user in page.editors.all()

@predicate
def is_page_publisher(user, page):
    if not page:
        return False
    return user in page.publishers.all()

@predicate
def can_edit_all_pages(user, page):
    return user.has_perm('edit_pages')

@predicate
def can_publish_all_pages(user, page):
    return user.has_perm('publish_pages')


# Permissions

add_perm('cms.edit_page', can_edit_all_pages | is_page_editor | can_publish_all_pages | is_page_publisher)
add_perm('cms.publish_page', can_publish_all_pages | is_page_publisher)
