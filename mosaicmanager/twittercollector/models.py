from django.db import models
from django.contrib.contenttypes.models import ContentType

from social.apps.django_app.default.models import UserSocialAuth

from mosaicrenderer.models import Mosaic, MosaicSourceImage

class TweeterBlocklist(models.Model):
    """
    Sometimes people are trolls.
    This should stop existing mosaics from these people
    being addressable, or their tweets being shown
    It should block them from all future renders
    """
    #this is the current maximum size twitter allows
    username = models.CharField(max_length=15)


class TweetMosaicSource(MosaicSourceImage):
    #probaby tweet message
    tweet_id = models.CharField(max_length=128)
    user_id = models.CharField(max_length=128)
    message = models.TextField(default="",
                               help_text="maybe not always the full message/post")
    
    username = models.CharField(max_length=128)

    image_url = models.URLField(blank=True, help_text="url to IMAGE")
    geo = models.CharField(max_length=128)

    
class TwitterMosaic(Mosaic):

    twitter_search = models.TextField(blank=True)
    collector = models.ForeignKey(
        UserSocialAuth, blank=True, null=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'provider': 'twitter'},
        help_text=("Which account will collect the tweets, under a quota. "
                   "Using the same account for more than one active mosaic split your "
                   "tweet quota between the two queries (i.e. you will "
                   "get half as many tweets/hour or less)"
        )
    )

    @classmethod
    def start_collectors(cls):
        #start all collectors for active mosaics that are not running
        pass
    
    def start_collector(self):
        """
        Starts a collector process
        """
        #inputs: collector token+secret + ?twitter creds + module_for_processing data
        #plus run with creating a /tmp/pid
        subprocess.Popen(['../foo.py'])
        pass

    def collector_running(self):
        "True if not running, False, if not"
        return 0
    
