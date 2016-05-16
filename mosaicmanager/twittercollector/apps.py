from django.apps import AppConfig
from django.conf import settings


class TwitterCollectorConfig(AppConfig):
    """
    loading this config (by including 
    'twittercollector.apps.TwitterCollectorConfig' in
    settings.INSTALLED_APPS) will automatically start
    processes for active twitter collectors as subprocesses
    and make sure they remain present while Django is running.

    If you just want the schema, without running the
    processes (e.g. if you will run the processes on a
    different machine, or managed differently), then 
    just include 'twittercollector' in INSTALLED_APPS instead
    """
    
    name = 'twittercollector'

    def ready(self):
        #1. make sure that for all active Mosaics, there's a process running
        print('sky sky sky')
        print('settings', settings)
    
