"""
Django model decorators can be used to modify inherited fields of abstract models.
"""


def modify_fields(**kwargs):
    r"""
    This decorator can be used to override properties of inherited django model fields.

    :param \**kwargs: A mapping from model fields to their overridden key/value pairs
    :type \**kwargs: dict

    :return: The decorated class
    :rtype: type
    """

    def wrap(cls):
        """
        The inner function for this decorator

        :param cls: Django request
        :type cls: ~django.http.HttpRequest

        :return: The decorated model class
        :rtype: type
        """
        for field, prop_dict in kwargs.items():
            for prop, val in prop_dict.items():
                setattr(cls._meta.get_field(field), prop, val)
        return cls

    return wrap
