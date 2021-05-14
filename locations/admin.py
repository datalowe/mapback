from django.contrib import admin

from .models import Location, MarkerIcon, MarkerSignificance

for mod in [Location, MarkerIcon, MarkerSignificance]:
    admin.site.register(mod)
