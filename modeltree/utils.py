from django.db import models
from django.db.models.sql.constants import QUERY_TERMS, LOOKUP_SEP

from modeltree.tree import trees

class ModelFieldResolver(object):
    def _resolve(self, app_name=None, model_name=None, field_name=None,
        operator=None, tree=None):

        """Generates a lookup string for use with the ``QuerySet`` API.

        Arguments:

            ``app_name`` - For cases when the ``model_name`` is ambiguous (two
            apps containing a model of the same name), this must be specified.

            ``model_name`` - Generates the path up to the model, but not including
            any specific field on that model. If none is supplied, the model is
            assumed to be the root model of the ``ModelTree`` being used.

            ``field_name`` - The name of a field to include relative to the model
            being joined to.

            ``tree`` - The ``ModelTree`` instance to be used for resolving the
            path.
        """
        model = tree.get_model(app_name, model_name, local=True)

        if field_name:
            # attempt to get the field object these components represent
            field = tree.get_field(field_name, model=model)
            lookup = tree.query_string_for_field(field, operator=operator)
        else:
            lookup = tree.query_string(model)

        return lookup

    def resolve(self, path, local=False, using=None):
        """Resolves a model field path and returns a lookup string for use
        with the ``QuerySet`` API.

        Arguments:

            ``path`` - A model field path to be parsed and resolved into
            a fully qualified lookup path.

            ``local`` - The typical use of the resolver is for relationships,
            but for when a lookup generated for a local field (on the root
            model) is desired, this flag must be set to ``True``.

            ``using`` - The alias of a ``ModelTree`` instance to be used for
            resolving the path. If none is supplied, the default ``ModelTree``
            instance will be used.

        Examples (relative to the Project model):

            'title' => 'employees__title'
            'title__salary' => 'employees__title__salary'
            'title__salary__gt' => 'employees__title__salary__gt'
        """
        tree = trees[using]

        # split by the default separator
        toks = path.split(LOOKUP_SEP)
        app_name = model_name = field_name = operator = None

        # catch basic errors up front
        if local and len(toks) > 2:
            raise ValueError, '%s is not a valid query lookup' % path

        if not local and len(toks) > 4:
             raise ValueError, '%s is not a valid query lookup' % path

        # if an operator is supplied, a field_name must also be specified
        if toks[-1] in QUERY_TERMS:
            operator = toks.pop()

        if local:
           field_name = toks.pop()
        else:
            if len(toks) == 3:
                app_name, model_name, field_name = toks
            elif len(toks) == 2:
                try:
                    model_name = tree.get_model(*toks, local=True)
                    app_name = toks[0]
                except ValueError:
                    model_name, field_name = toks
            else:
                model_name = toks.pop()

        return self._resolve(app_name, model_name, field_name, operator, tree)


resolver = ModelFieldResolver()
resolve = resolver.resolve


class M(models.Q):
    def __init__(self, using=None, *args, **kwargs):
        nargs = []
        nkwargs = {}

        for key in iter(args):
            if not isinstance(key, models.Q):
                key = resolve(key, using=using)
            nargs.append(key)

        # iterate over each kwarg and perform the conversion
        for key, value in iter(kwargs.items()):
            lookup = resolve(key, using=using)
            nkwargs[lookup] = value

        return super(M, self).__init__(*nargs, **nkwargs)


