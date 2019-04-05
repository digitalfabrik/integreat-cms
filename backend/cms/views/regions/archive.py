"""
Functionality for providing archive with all pages
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def archive(request):
    """View for creating and rendering archive page
    Args:
        request : Object representing the user request
    Returns:
        Rendered HTML : Archive Page rendered by archive.html template and page context
    """

    return render(request, 'regions/archive.html',
                  {'current_menu_item': 'regions'})
