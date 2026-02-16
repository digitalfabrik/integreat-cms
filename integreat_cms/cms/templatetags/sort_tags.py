from django import template
from django.template.context import RequestContext
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def sort_link(context: RequestContext, label: str, field: str) -> str:
    """
    Sets the correct href for sortable table headers

    Usage in template:
        {% sort_link "Name" "name" %}
    """

    request = context["request"]
    params = request.GET.copy()
    current = params.get("sort")

    if field == current:
        params["sort"] = f"-{field}"
        arrow = " ▼"
    elif f"-{field}" == current:
        params.pop("sort", None)
        arrow = " ▲"
    else:
        params["sort"] = field
        arrow = ""

    url = f"?{urlencode(params, doseq=True)}"

    return mark_safe(f'<a href="{url}" class="hover:underline">{label}{arrow}</a>')


@register.inclusion_tag("_sortable_table_header.html", takes_context=True)
def render_table_header(context: RequestContext, table_fields: dict[str, str]) -> dict:
    return {
        "request": context["request"],
        "table_fields": table_fields,
    }
