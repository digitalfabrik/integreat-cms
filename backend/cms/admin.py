"""
File routing to the admin site
"""


from django.contrib import admin

from .models import Site, Language, Page, PageTranslation

admin.site.register(Site)
admin.site.register(Language)
admin.site.register(Page)
admin.site.register(PageTranslation)
