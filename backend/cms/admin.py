"""
File routing to the admin region
"""


from django.contrib import admin
from .models import Region, Language, LanguageTreeNode, Page, PageTranslation, Organization

admin.site.register(Region)
admin.site.register(Language)
admin.site.register(LanguageTreeNode)
admin.site.register(Page)
admin.site.register(PageTranslation)
admin.site.register(Organization)
