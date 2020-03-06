from django import template
from ..utils.media_utils import get_thumbnail

register = template.Library()


@register.simple_tag
def generate_thumbnail(document, width, height, crop):
    return get_thumbnail(document.file, width, height, crop)
