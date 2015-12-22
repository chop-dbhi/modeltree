from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models


class GenericModel(models.Model):
    content_type = models.ForeignKey(
        'contenttypes.ContentType', blank=True, null=True)
    object_id = models.PositiveIntegerField(
        db_index=True, blank=True, null=True)
    reference_object = GenericForeignKey('content_type', 'object_id')
