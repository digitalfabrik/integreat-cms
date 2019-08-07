"""
File routing to the admin region
"""


from django.contrib import admin
from .models import Region
from .models import Language
from .models import LanguageTreeNode
from .models import Page
from .models import PageTranslation
from .models import POI
from .models import POITranslation
from .models import Organization

admin.site.register(Region)
admin.site.register(Language)
admin.site.register(LanguageTreeNode)
admin.site.register(Page)
admin.site.register(PageTranslation)
admin.site.register(POI)
admin.site.register(POITranslation)
admin.site.register(Organization)
