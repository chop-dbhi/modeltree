from django.db import models
from modeltree.query import ModelTreeQuerySet

class ModelTreeManager(models.Manager):
    def get_query_set(self):
        return ModelTreeQuerySet(model=self.model, using=self.db)

    def select(self, *args, **kwargs):
        return self.get_query_set().select(*args, **kwargs)
