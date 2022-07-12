from django import forms


class CustomFilterForm(forms.Form):
    """
    Base class for filter forms
    """

    def __init__(self, **kwargs):
        r"""
        Initialize the custom filter form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        super().__init__(**kwargs)

        # If no values for some fields are supplied, use the initial values
        self.data = self.data.copy()
        for name in self.declared_fields:
            if name not in self.data:
                initial = self.fields[name].initial
                if isinstance(initial, list):
                    self.data.setlist(name, initial)
                else:
                    self.data[name] = initial

    @property
    def is_enabled(self):
        """
        This function determines whether the filters are applied.

        :return: Whether filtering should be performed
        :rtype: bool
        """
        return self.is_valid() and self.has_changed()

    @property
    def filters_visible(self):
        """
        This function determines whether the filter form is visible by default.

        :return: Whether any filters (other than search) were changed
        :rtype: bool
        """
        return self.is_enabled and self.changed_data != ["query"]
