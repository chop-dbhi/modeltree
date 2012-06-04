from django.db import models
from django.db.models import FieldDoesNotExist
from django.db.models.sql.constants import QUERY_TERMS, LOOKUP_SEP
from modeltree.tree import trees, ModelDoesNotExist, ModelNotRelated, ModelNotUnique


class InvalidLookup(Exception):
    pass


def _resolve(app_name=None, model_name=None, field_name=None, operator=None, mtree=None):
    """Generates a lookup string for use with the ``QuerySet`` API.

    Arguments:

        ``app_name`` - For cases when the ``model_name`` is ambiguous (two
        apps containing a model of the same name), this must be specified.

        ``model_name`` - Generates the path up to the model, but not including
        any specific field on that model. If none is supplied, the model is
        assumed to be the root model of the ``ModelTree`` being used.

        ``field_name`` - The name of a field to include relative to the model
        being joined to.

        ``mtree`` - The ``ModelTree`` instance to be used for resolving the
        path.
    """
    model = mtree.get_model(model_name, app_name, local=True)

    # Lookups for fields on the root model should not have the model
    # explicitly defined. This is to prevent confusion.
    if model_name and model is mtree.root_model:
        raise InvalidLookup('Explicit lookups for the root model are not '
            'allowed. For "self" relationships use the corresponding '
            'related name.')

    if field_name:
        try:
            field = mtree.get_field(field_name, model=model)
            lookup = mtree.query_string_for_field(field, operator=operator)
        except FieldDoesNotExist:
            raise InvalidLookup('Field "{0}" not found on model "{0}".'.format(field_name, model_name))
    else:
        lookup = mtree.query_string(model)
    return lookup


def resolve_lookup(path, tree=None):
    """Resolves a model field path and returns a lookup string for use
    with the ``QuerySet`` API.

    Arguments:

        ``path`` - A model field path to be parsed and resolved into
        a fully qualified lookup path.

        ``tree`` - The alias of a ``ModelTree`` instance to be used for
        resolving the path. If none is supplied, the default ``ModelTree``
        instance will be used.

    Examples (relative to the Project model):

        'title' => 'employees__title'
        'title__salary' => 'employees__title__salary'
        'title__salary__gt' => 'employees__title__salary__gt'
    """

    # No path, nothing to resolve
    if not path:
        raise ValueError('A path must be provided.')

    # Tokenize by the default separator that Django uses
    toks = path.split(LOOKUP_SEP)
    num_toks = len(toks)

    # If there are more tokens than a fully-qualified modeltree lookup requires,
    # the `path` is assumed to be a normal Django lookup. This is merely a
    # shortcut to prevent unnecessary processing.
    if num_toks > 4:
        return path

    # Starting tokens for full qualified path.
    app_name = model_name = field_name = operator = None

    # Get the `ModelTree` instance these lookups are relative to
    mtree = trees[tree]

    # Check for a field lookup operator. If it is supplied, a `field_name` must
    # also be specified.
    if num_toks > 1 and toks[-1] in QUERY_TERMS:
        operator = toks.pop()
        num_toks -= 1

    # Attempt to infer what the single token is. By default, a local or
    # related field will be checked for, and will fallback to a model name.
    # If neither can be resolved, this is not a valid lookup.
    if num_toks == 1:
        # Exception thrown when no field on the modeltree root model is found
        try:
            mtree.get_field(toks[0])
            field_name = toks[0]
        except FieldDoesNotExist:
            # Exception thrown when a related model is not found or the model
            # name is ambiguous.
            try:
                mtree.get_model(model_name=toks[0])
                model_name = toks[0]
            except ModelNotRelated:
                raise InvalidLookup('No field or related model corresponds to "{0}".'.format(model_name))
            except ModelNotUnique, e:
                raise InvalidLookup(e.message)

    # Two tokens may be a (model, field) pair or (app, model) pair. The
    # latter implies the primary key field of the found model. If neither
    # match, this means the first token must be a related field name that
    # spans other relationships.
    elif num_toks == 2:
        try:
            mtree.get_model(model_name=toks[0])
            model_name, field_name = toks
        except (ModelNotRelated, ModelNotUnique):
            try:
                mtree.get_model(model_name=toks[1])
                app_name, model_name = toks
            except (ModelNotRelated, ModelDoesNotExist):
                pass

    # Assume all three qualified tokens are supplied
    elif num_toks == 3:
        app_name, model_name, field_name = toks

    # Perform a check
    if model_name or field_name:
        try:
            return _resolve(app_name, model_name, field_name, operator, mtree)
        except (ValueError, FieldDoesNotExist):
            pass

    # Fallback to returning the path as is for cross-relation lookups
    return path


class M(models.Q):
    def __init__(self, tree=None, *args, **kwargs):
        nargs = []
        nkwargs = {}

        for key in args:
            if not isinstance(key, models.Q):
                key = resolve_lookup(key, tree=tree)
            nargs.append(key)

        # iterate over each kwarg and perform the conversion
        for key, value in kwargs.iteritems():
            lookup = resolve_lookup(key, tree=tree)
            nkwargs[lookup] = value

        return super(M, self).__init__(*nargs, **nkwargs)
