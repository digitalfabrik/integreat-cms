from django.db import models

from ...constants import feedback_emotions


class Feedback(models.Model):
    """
    Database model representing feedback from app-users.

    :param id: The database id of the feedback
    :param emotion: Whether the feedback is positive or negative (choices: :mod:`cms.constants.feedback_emotions`)
    :param comment: A comment describing the feedback
    :param is_technical: Whether or not the feedback is targeted at the developers
    :param read_status: Whether or not the feedback is marked as read
    :param created_date: The date and time when the feedback was created
    :param last_updated: The date and time when the feedback was last updated
    """

    emotion = models.CharField(max_length=3, choices=feedback_emotions.CHOICES)
    comment = models.CharField(max_length=1000)
    is_technical = models.BooleanField()
    read_status = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple

        :param permissions: The custom permissions for this model
        :type permissions: tuple
        """
        default_permissions = ()
        permissions = (
            ('view_feedback', 'Can view feedback'),
        )
