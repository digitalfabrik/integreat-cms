from __future__ import annotations

from datetime import datetime
from time import mktime
from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from datetime import date
    from time import struct_time

register = template.Library()


@register.filter
def parse_struct_time(struct_time: struct_time) -> date:
    """
    Converts timestamp to datetime and returns date only

    :param struct_time: timestamp received from rss feed
    :return: proper parsed date
    """
    return datetime.fromtimestamp(mktime(struct_time)).date()
