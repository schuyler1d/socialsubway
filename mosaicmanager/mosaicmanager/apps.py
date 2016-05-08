from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "mosaicmanager"
    verbose_name = "Mosaic Manager"

    def ready(self):
        #1. make sure that for all active Mosaics, there's a process running
        pass
