from django import template

register = template.Library()


@register.simple_tag
def get_last_root_page(pages):
    return pages.filter(parent=None).last()


@register.filter
def get_descendants(page):
    return [descendant.id for descendant in page.get_descendants(include_self=True)]
