from django.utils.translation import ugettext_lazy as _


DRAFT = 'DRAFT'
REVIEW = 'REVIEW'
PUBLIC = 'PUBLIC'

CHOICES = (
    (DRAFT, _('Draft')),
    (REVIEW, _('Pending Review')),
    (PUBLIC, _('Public')),
)
