from django.conf import settings
from modeltree.node import ModelTree, MODELTREE_DEFAULT_ALIAS

class LazyModelTrees(object):
    "Lazily evaluates ``ModelTree`` instances defined in settings."
    def __init__(self, modeltrees):
        self.modeltrees = modeltrees
        self._modeltrees = {}

    @property
    def default(self):
        return self[MODELTREE_DEFAULT_ALIAS]

    def __getitem__(self, alias):
        if alias not in self._modeltrees:
            try:
                kwargs = self.modeltrees[alias]
            except KeyError:
                raise KeyError, 'no modeltree settings defined for "%s"' % alias

            self._modeltrees[alias] = ModelTree(**kwargs)
        return self._modeltrees[alias]

trees = LazyModelTrees(getattr(settings, 'MODELTREES', {}))
