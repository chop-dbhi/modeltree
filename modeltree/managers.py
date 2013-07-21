from django.db import models
from modeltree.query import ModelTreeQuerySet


class ModelTreeManager(models.Manager):
    def __init__(self, tree=None, *args, **kwargs):
        super(ModelTreeManager, self).__init__(*args, **kwargs)
        self.tree = tree or self.model

    def get_query_set(self):
        return ModelTreeQuerySet(model=self.tree, using=self.db)

    def select(self, *args, **kwargs):
        return self.get_query_set().select(*args, **kwargs)
