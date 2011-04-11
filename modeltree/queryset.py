from django.db.models import query
from modeltree.node import MODELTREE_DEFAULT_ALIAS
from modeltree import trees

class ModelTreeQuerySet(query.QuerySet):
    def __init__(self, alias=None, query=None, using=None):
        if alias is None:
            alias = MODELTREE_DEFAULT_ALIAS
        model = trees[alias].root_model

        super(ModelTreeQuerySet, self).__init__(model, query, using)

