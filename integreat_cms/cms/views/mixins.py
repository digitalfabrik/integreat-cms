"""
This module contains mixins for our views
"""
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
)


class StaffRequiredMixing(UserPassesTestMixin):
    """
    A mixin that can be used for class-based views that require that the user is either superuser or staff member
    """

    def test_func(self):
        """
        The test the user has to pass

        :return: Whether the user has passed the test
        :rtype: bool
        """
        return self.request.user.is_superuser or self.request.user.is_staff
