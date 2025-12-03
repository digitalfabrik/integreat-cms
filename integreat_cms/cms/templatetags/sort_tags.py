from django import template
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def sort_link(context, label, field):
    """
    Usage:
        {% sort_link "Name" "name" %}
    """

    request = context["request"]
    current = request.GET.getlist("sort")
    current = [c.strip() for c in current]

    if field in current:
        new_field = f"-{field}"
        arrow = " ▲"
        new_sort = [new_field] + [c for c in current if c != field]
    elif f"-{field}" in current:
        new_field = field
        arrow = " ▼"
        new_sort = [new_field] + [c for c in current if c != f"-{field}"]
    else:
        new_field = field
        arrow = ""
        new_sort = [new_field, *current]

    params = request.GET.copy()
    params.pop("sort", None)
    params.setlist("sort", new_sort)

    url = f"?{urlencode(params, doseq=True)}"

    return mark_safe(f'<a href="{url}" class="hover:underline">{label}{arrow}</a>')


@register.inclusion_tag("_sortable_table_header.html", takes_context=True)
def render_table_header(context, table_fields):
    return {
        "request": context["request"],
        "table_fields": table_fields,
    }
