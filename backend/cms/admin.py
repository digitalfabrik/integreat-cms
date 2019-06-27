"""
File routing to the admin site
"""


from django.contrib import admin
from .models import Site, Language, LanguageTreeNode, Page, PageTranslation, Organization

admin.site.register(Site)
admin.site.register(Language)
admin.site.register(LanguageTreeNode)
admin.site.register(Page)
admin.site.register(PageTranslation)
admin.site.register(Organization)
