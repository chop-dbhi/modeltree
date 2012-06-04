from django.db.models import query
from django.db.models.sql import RawQuery
from modeltree.tree import trees
from modeltree.utils import M


class ModelTreeQuerySet(query.QuerySet):
    def __init__(self, model=None, query=None, using=None):
        self.modeltree = trees[model]
        model = self.modeltree.root_model
        super(ModelTreeQuerySet, self).__init__(model, query, using)

    def _filter_or_exclude(self, negate, *args, **kwargs):
        return super(ModelTreeQuerySet, self)._filter_or_exclude(negate,
                M(self.modeltree, *args, **kwargs))

    def select(self, *fields, **kwargs):
        include_pk = kwargs.get('inclue_pk', True)

        if include_pk:
            fields = [self.model._meta.pk] + list(fields)

        queryset = self._clone()
        queryset = self.modeltree.add_select(queryset=queryset, *fields)
        sql, params = queryset.query.get_compiler(self.db).as_sql()

        return RawQuery(sql, self.db, params)
