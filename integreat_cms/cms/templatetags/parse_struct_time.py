from datetime import datetime
from time import mktime

from django import template

register = template.Library()


@register.filter
def parse_struct_time(struct_time):
    """
    Converts timestamp to datetime and returns date only

    :param struct_time: timestamp received from rss feed
    :type struct_time: time.struct_time
    :return: proper parsed date
    :rtype: datetime.date
    """
    return datetime.fromtimestamp(mktime(struct_time)).date()
