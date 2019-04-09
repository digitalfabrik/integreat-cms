from django.contrib import admin

from federation.models import CMSCache, RegionCache


admin.site.register(CMSCache)
admin.site.register(RegionCache)
