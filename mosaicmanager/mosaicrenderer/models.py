from django.db import models

from django.contrib.contenttypes.models import ContentType


"""
Should we store every tweet we use?  That will help with the block list.  And really, it's pretty small in terms of data.  It will also allow for easier moderation.

How to accomodate image uploading when people want to do that?

"""


class MosaicSourceImage(models.Model):
    "Probably a tweet"
    image = models.ImageField(null=True,
                              width_field='image_height',
                              height_field='image_width')
    content_type = models.ForeignKey(ContentType,
                                     editable=False,
                                     blank=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)

    def save(self, *args, **kw):
        self.content_type = ContentType.objects.get_for_model(self)
        super(MosaicSourceImage, self).save(*args, **kw)
    

class Mosaic(models.Model):

    content_type = models.ForeignKey(ContentType,
                                     editable=False,
                                     blank=True)

    slug = models.CharField(max_length=128, db_index=True)
    status = models.IntegerField(choices=(
        (1, 'active'),
        (2, 'paused'), #don't search for new tweets, or expose uploader
        (5, 'completed'),
    ))

    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    target_image = models.ImageField(blank=True,
                                     width_field='image_height',
                                     height_field='image_width')
    title = models.TextField(blank=True)
    
    minimum_image_count = models.PositiveIntegerField()
    incremental_update_count = models.PositiveIntegerField()

    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True)
    last_render = models.DateTimeField(null=True, blank=True)

    source_images = models.ManyToManyField(MosaicSourceImage,
                                           related_name="mosaics")

    public_url = models.URLField(blank=True, null=True)


    def save(self, *args, **kw):
        self.content_type = ContentType.objects.get_for_model(self)
        super(Mosaic, self).save(*args, **kw)
    

class MosaicRender(models.Model):
    
    final_image = models.ImageField(blank=True,
                                    width_field='image_height',
                                    height_field='image_width')
    mosaic = models.ForeignKey(Mosaic, db_index=True)
    source_images = models.ManyToManyField(MosaicSourceImage,
                                           through='SourcePosition',
                                           related_name="renders")
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)

    tiles_x = models.PositiveIntegerField(null=True)
    tiles_y = models.PositiveIntegerField(null=True)

    
class SourcePosition(models.Model):
    render = models.ForeignKey(MosaicRender)
    source_image = models.ForeignKey(MosaicSourceImage)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
