from django.apps import AppConfig


class TailwindThemeConfig(AppConfig):
    """
    This class is just a wrapper around the tailwind theme for
    the integreat backend, containing a tailwind config and
    a scss file for custom styles.
    """

    name = "tailwind_theme"
