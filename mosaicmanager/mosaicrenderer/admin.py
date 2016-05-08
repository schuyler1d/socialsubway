from django.contrib import admin

from .models import *

#should be read-only
admin.site.register(MosaicRender)
