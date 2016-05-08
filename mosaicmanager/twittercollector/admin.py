from django.contrib import admin
from django.http import HttpResponse

from .models import *

admin.site.register(TweeterBlocklist)
admin.site.register(TwitterCollector)
admin.site.register(TweetMosaicSource)
admin.site.register(TwitterMosaic)

