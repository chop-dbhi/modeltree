from django.db.models import query
from django.db.models.sql import RawQuery

from modeltree.tree import trees

class ModelTreeQuerySet(query.QuerySet):
    def __init__(self, alias=None, model=None, query=None, using=None):
        if alias:
            modeltree = trees[alias]
        elif model:
            modeltree = trees.create(model)
        else:
            modeltree = trees.default

        self.modeltree = modeltree

        model = modeltree.root_model
        super(ModelTreeQuerySet, self).__init__(model, query, using)

    def select(self, *fields, **kwargs):
        include_pk = kwargs.get('inclue_pk', True)

        if include_pk:
            fields = [self.model._meta.pk] + list(fields)

        queryset = self._clone()
        queryset = self.modeltree.add_select(fields, queryset)
        sql, params = queryset.query.get_compiler(self.db).as_sql()

        return RawQuery(sql, self.db, params)

