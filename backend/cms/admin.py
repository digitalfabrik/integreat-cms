"""
File routing to the admin site
"""


from django.contrib import admin

from .models import Site

admin.site.register(Site)
