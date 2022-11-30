"""
This module contains all constants representing the period choices for the Matomo API
(See https://developer.matomo.org/api-reference/reporting-api).
"""
from django.utils.translation import gettext_lazy as _


#: Daily
DAY = "day"
#: Weekly
WEEK = "week"
#: Monthly
MONTH = "month"
#: Yearly
YEAR = "year"

#: Choices to use these constants in a database field
CHOICES = (
    (DAY, _("Daily")),
    (WEEK, _("Weekly")),
    (MONTH, _("Monthly")),
    (YEAR, _("Yearly")),
)
