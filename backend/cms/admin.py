"""
File routing to the admin site
"""


from django.contrib import admin

from .models import Site
from .models import Language

admin.site.register(Site)
admin.site.register(Language)
