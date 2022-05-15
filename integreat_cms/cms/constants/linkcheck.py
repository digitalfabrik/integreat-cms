from django.utils.translation import ugettext_lazy as _

LINKCHECK_STATUS_TRANSLATIONS = [
    _("Broken external hash anchor"),
    _("Broken internal link"),
    _("Broken internal hash anchor"),
    _("Broken redirect"),
    _("Email link (not automatically checked)"),
    _("Empty link"),
    _("Failed to parse HTML for anchor"),
    _("Invalid URL"),
    _("Link to within the same page (not automatically checked)"),
    _("Missing Document"),
    _("Other Error: The read operation timed out"),
    _("Page OK but anchor can't be checked"),
    _("Phone number (not automatically checked)"),
    _("URL Not Yet Checked"),
    _("Working file link"),
    _("Working internal hash anchor"),
    _("Working internal link"),
    _("Working redirect"),
]
