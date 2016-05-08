from django.db import models

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


class TwitterCollector(models.Model):
    access_token = models.TextField()
    access_token_secret = models.TextField()


class TweetMosaicSource(MosaicSourceImage):
    #probaby tweet message
    message = models.TextField(default="",
                               help_text="maybe not always the full message/post")
    
    useralias = models.CharField(max_length=128,
                                 help_text="aka username of service")

    link = models.URLField(blank=True)
    #
    geo = models.CharField(max_length=128)

    
class TwitterMosaic(Mosaic):

    twitter_search = models.TextField(blank=True)
    collector = models.ForeignKey(TwitterCollector, blank=True)

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
    
