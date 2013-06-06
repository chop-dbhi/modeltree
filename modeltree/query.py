from django.db.models import query
from modeltree.tree import trees
from modeltree.utils import M


class ModelTreeQuerySet(query.QuerySet):
    def __init__(self, model=None, query=None, using=None):
        self.tree = trees[model]
        super(ModelTreeQuerySet, self).__init__(self.tree.root_model, query, using)

    # Override to ensure no additional modeltrees are created during clone
    def _clone(self, klass=None, setup=False, **kwargs):
        if klass is None:
            klass = self.__class__
        query = self.query.clone()
        if self._sticky_filter:
            query.filter_is_sticky = True
        c = klass(model=self.tree, query=query, using=self._db)
        c._for_write = self._for_write
        c._prefetch_related_lookups = self._prefetch_related_lookups[:]
        c.__dict__.update(kwargs)
        if setup and hasattr(c, '_setup_query'):
            c._setup_query()
        return c

    def _filter_or_exclude(self, negate, *args, **kwargs):
        return super(ModelTreeQuerySet, self)._filter_or_exclude(negate,
                M(self.tree, *args, **kwargs))

    def select(self, *fields, **kwargs):
        queryset = self._clone()
        return self.tree.add_select(queryset=queryset, *fields, **kwargs)

    def raw(self):
        compiler = self.query.get_compiler(self.db)
        return compiler.results_iter()
