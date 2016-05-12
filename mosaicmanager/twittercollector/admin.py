from django.contrib import admin
from django.http import HttpResponse

from .models import *

class TwitterMosaicAdmin(admin.ModelAdmin):

    fieldsets = (
           (None, {'fields': (
               'twitter_search', 'collector',
               'slug', 'status', 'target_image', 'title',
               'minimum_image_count', 'incremental_update_count',

               #'created_at', 'modified_at', 'last_render'               
               
           )}),
        )


admin.site.register(TweeterBlocklist)
admin.site.register(TweetMosaicSource)
admin.site.register(TwitterMosaic, TwitterMosaicAdmin)

