import inspect
import warnings

import six
from django.apps import apps
from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, ManyToManyRel, ManyToOneRel
from django.db.models.expressions import Col
from django.db.models.sql.constants import INNER, LOUTER
from django.db.models.sql.datastructures import Join, BaseTable
from django.utils.datastructures import MultiValueDict

__all__ = ('ModelTree',)


MODELTREE_DEFAULT_ALIAS = 'default'


class ModelTreeError(Exception):
    pass


class ModelLookupError(ModelTreeError):
    pass


class ModelNotUnique(ModelLookupError):
    pass


class ModelDoesNotExist(ModelLookupError):
    pass


class ModelNotRelated(ModelLookupError):
    pass


@six.python_2_unicode_compatible
class ModelTreeNode(object):
    def __init__(self, model, parent=None, relation=None, reverse=None,
                 related_name=None, accessor_name=None, nullable=False,
                 depth=0):

        """Defines attributes of a `model' and the relationship to the
        parent model.

            `model` - the model this node represents

            `parent` - a reference to the parent ModelTreeNode

            `relation'` - denotes the _kind_ of relationship with the
            following possibilities: 'manytomany', 'onetoone', or 'foreignkey'.

            `reverse` - denotes whether this node was derived from a
            forward relationship (an attribute lives on the parent model) or
            a reverse relationship (an attribute lives on this model).

            `related_name` - is the query string representation which is used
            when querying via the ORM.

            `accessor_name` - can be used when accessing the model object's
            attributes e.g. getattr(obj, accessor_name). this is relative to
            the parent model.

            `nullable` - flags whether the relationship is nullable. this can
            be implied by being a many-to-many or reversed foreign key.

            `depth` - the depth of this node relative to the root (zero-based
            index)

        """

        self.model = model

        self.app_name = model._meta.app_label
        self.model_name = model._meta.object_name
        self.db_table = model._meta.db_table
        self.pk_column = model._meta.pk.column

        self.parent = parent
        self.parent_model = parent and parent.model or None

        self.relation = relation
        self.reverse = reverse

        self.related_name = related_name
        self.accessor_name = accessor_name
        self.nullable = nullable
        self.depth = depth

        self.children = []

    def __str__(self):
        name = 'ModelTreeNode: {0}'.format(self.model_name)

        if self.parent:
            name += ' via {0}'.format(self.parent_model.__name__)

        return name

    def __repr__(self):
        return '<{0}>'.format(self)

    @property
    def m2m_db_table(self):
        related_field = self.parent_model._meta.get_field(self.related_name)
        if self.reverse:
            return related_field.field.m2m_db_table()
        else:
            return related_field.m2m_db_table()

    def get_joins(self):
        """Returns a BaseTable and a list of Join objects that need to be added
        to a QuerySet object that properly joins this model and the parent.
        """
        # These arguments should match the spec of the Join object.
        # See https://github.com/django/django/blob/1.8.7/django/db/models/sql/query.py#L896  # noqa
        join_args = {
            'table_name': None,
            'parent_alias': None,
            'table_alias': None,
            'join_type': None,
            'join_field': None,
            'nullable': self.nullable,
        }

        joins = []

        related_field = self.parent_model._meta.get_field(self.related_name)
        # Setup two connections for m2m.
        if self.relation == 'manytomany':
            path = related_field.get_path_info()

            copy1 = join_args.copy()
            copy1.update({
                'join_field': path[0].join_field,
                'parent_alias': self.parent.db_table,
                'table_name': self.m2m_db_table,
                'join_type': LOUTER,
            })

            copy2 = join_args.copy()
            copy2.update({
                'join_field': path[1].join_field,
                'parent_alias': self.m2m_db_table,
                'table_name': self.db_table,
                'join_type': LOUTER,
            })
            joins.append(Join(**copy1))
            joins.append(Join(**copy2))
        else:
            copy = join_args.copy()
            copy.update({
                'table_name': self.db_table,
                'parent_alias': self.parent.db_table,
                'join_field': related_field,
                'join_type': LOUTER if self.nullable else INNER,
            })

            joins.append(Join(**copy))

        return BaseTable(self.parent.db_table, alias=None), joins

    def remove_child(self, model):
        "Removes a child node for a given model."
        for i, node in enumerate(self.children):
            if node.model is model:
                return self.children.pop(i)


class ModelTree(object):
    """A class to handle building and parsing a tree structure given a model.

        `root_model` - The root or "reference" model for the tree. Everything
        is relative to the root model.

        `exclude` - A list of models that are to be excluded from this tree.
        This is typically used to exclude models not intended to be exposed
        through this API.

        `routes` - Explicitly defines a join path between two models. Each
        route is made up of four components. Assuming some model hierarchy
        exists as shown below..

                                ModelA
                                /    \
                            ModelB  ModelC
                               |      |
                               \    ModelD
                                \    /
                                ModelE

        ..the traversal path from ModelA to ModelE is ambiguous. It could
        go from A -> B -> E or A -> C -> D -> E. By default, the shortest
        path is always choosen to reduce the number of joins necessary, but
        if ModelD did not exist..

                                ModelA
                                 /  \
                            ModelB  ModelC
                                 \  /
                                ModelE

        ..both paths only require two joins, thus the path that gets traversed
        first will only be the choosen one.

        To explicitly choose a path, a route can be defined. Taking the form::

            {
                'source': 'app1.model1',
                'target': 'app1.model2',
                'field': None,
                'symmetrical': None,
            }

        The `source` model defines the model where the join is being created
        from (the left side of the join). The `target` model defines the
        target model (the right side of the join). `field` is optional,
        but explicitly defines the model field that will be used for the join.
        This is useful if there are more than one foreign key relationships on
        between target and source. Finally, `symmetrical` is an optional
        boolean that ensures when the target and source models switch sides,
        the same join occurs on the same field.

        Routes are typically used for defining explicit join paths, but
        sometimes it is necessary to exclude join paths. For example if there
        are three possible paths and one should never occur.

        A modeltree config can have `required_routes` and `excluded_routes`
        entries, which are lists of routes in the above format.

        A required route is defined as follows: a join to the specified target
        model is only allowed from the specified source model.  A model can
        only be specified as a target once in the list of required routes.
        Note that the use of the `symmetrical` property of a route
        implicitly adds another route with target and source models swapped,
        so a model can be a target either directly or indirectly.  A single
        source model can participate in multiple required routes.

        An excluded route is more obvious: joining from the specified source
        model to the specified target model is not allowed.

    """                                                           # noqa: W605
    def __init__(self, model=None, **kwargs):
        if model is None and 'root_model' in kwargs:
            warnings.warn('The "root_model" key has been renamed to "model"',
                          DeprecationWarning)
            model = kwargs.get('root_model')

        if not model:
            raise TypeError('No "model" defined')

        excluded_models = kwargs.get('excluded_models', ())
        required_routes = kwargs.get('required_routes')

        if not excluded_models and 'exclude' in kwargs:
            warnings.warn('The "exclude" key has been renamed to '
                          '"excluded_models"', DeprecationWarning)

            excluded_models = kwargs.get('exclude', ())

        if not required_routes and 'routes' in kwargs:
            warnings.warn('The "routes" key has been renamed to '
                          '"required_routes"', DeprecationWarning)

            required_routes = kwargs.get('routes')

        excluded_routes = kwargs.get('excluded_routes')

        self.root_model = self.get_model(model, local=False)
        self.alias = kwargs.get('alias', None)

        # Models completely excluded from the tree
        self.excluded_models = [self.get_model(label, local=False)
                                for label in excluded_models]

        # Build the routes that are allowed/preferred
        self._required_joins = self._build_routes(
            required_routes,
            allow_redundant_targets=False)

        # Build the routes that are excluded
        self._excluded_joins = self._build_routes(excluded_routes)

        # cache each node relative their models
        self._nodes = {}

        # cache all app names relative to their model names i.e. supporting
        # multiple apps with models of the same name
        self._model_apps = MultiValueDict({})

        # cache (app, model) pairs with the respective model class
        self._models = {}

        self._build()

    def __repr__(self):
        return u'<ModelTree for {0}>'.format(self.root_model.__name__)

    def _get_local_model(self, model_name, app_name=None):
        "Attempts to get a model from local cache."
        if not app_name:
            app_names = self._model_apps.getlist(model_name)
            # No apps found with this model
            if not app_names:
                return

            # Multiple apps found for this model
            if len(app_names) > 1:
                raise ModelNotUnique('The model "{0}" is not unique. '
                                     'Specify the app name as well.'
                                     .format(model_name))

            app_name = app_names[0]

        try:
            return self._models[(app_name, model_name)]
        except KeyError:
            pass

    def _get_model(self, model_name, app_name=None):
        "Attempts to get a model from application cache."
        model = None

        # If an app name is supplied we can reduce it down to only models
        # within that particular app.
        if app_name:
            model = apps.get_model(app_name, model_name)
        else:
            # Attempt to find the model based on the name. Since we don't
            # have the app name, if a model of the same name exists multiple
            # times, we need to throw an error.
            for app, app_models in apps.app_models.items():
                if model_name in app_models:
                    if model is not None:
                        raise ModelNotUnique('The model "{0}" is not unique. '
                                             'Specify the app name as well.'
                                             .format(model_name))

                    model = app_models[model_name]

        return model

    def get_model(self, model_name=None, app_name=None, local=True):
        """A few variations are handled here for increased flexibility:

            - if a model class is given, simply echo the model back

            - if a app-model label e.g. 'library.book', is passed, the
            standard app_models cache is used

            - if `app_name` and `model_name` is provided, the standard
            app_models cache is used

            - if only `model_name` is supplied, attempt to find the model
            across all apps. if the model is found more than once, an error
            is thrown

            - if `local` is true, only models related to this `ModelTree`
            instance are searched through
        """
        model = None

        if not (app_name or model_name):
            return self.root_model

        # model class
        if inspect.isclass(model_name) and \
                issubclass(model_name, models.Model):
            # set it initially for either local and non-local
            model = model_name

            # additional check to ensure the model exists locally, reset to
            # None if it does not
            if local and model not in self._nodes:
                model = None

        # handle string-based arguments
        else:
            # handle the syntax 'library.book'
            if model_name:
                if '.' in model_name:
                    app_name, model_name = model_name.split('.', 1)
                model_name = model_name.lower()

            if local:
                model = self._get_local_model(model_name, app_name)
            else:
                model = self._get_model(model_name, app_name)

        # both mechanisms above may result in no model being found
        if model is None:
            if local:
                raise ModelNotRelated('No model found named "{0}"'
                                      .format(model_name))
            else:
                raise ModelDoesNotExist('No model found named "{0}"'
                                        .format(model_name))

        return model

    def get_field(self, name, model=None):
        if model is None:
            model = self.root_model
        return model._meta.get_field(name)

    def _build_routes(self, routes, allow_redundant_targets=True):
        """Routes provide a means of specifying JOINs between two tables.

        routes - a collection of dicts defining source->target mappings
                 with optional `field` specifier and `symmetrical` attribute.

        allow_redundant_targets - whether two routes in this collection
                 are allowed to have the same target - this should NOT
                 be allowed for required routes.
        """
        routes = routes or ()
        joins = {}
        targets_seen = set()

        for route in routes:
            if isinstance(route, dict):
                source_label = route.get('source')
                target_label = route.get('target')
                field_label = route.get('field')
                symmetrical = route.get('symmetrical')
            else:
                warnings.warn('Routes are now defined as dicts',
                              DeprecationWarning)
                source_label, target_label, field_label, symmetrical = route

            # get models
            source = self.get_model(source_label, local=False)
            target = self.get_model(target_label, local=False)

            field = None

            # get field
            if field_label:
                model_name, field_name = field_label.split('.', 1)
                model_name = model_name.lower()

                # determine which model the join field specified exists on
                if model_name == source.__name__.lower():
                    field = self.get_field(field_name, source)
                elif model_name == target.__name__.lower():
                    field = self.get_field(field_name, target)
                else:
                    raise TypeError('model for join field, "{0}", '
                                    'does not exist'.format(field_name))

                if isinstance(field, (ManyToOneRel, ManyToManyRel)):
                    field = field.field

            if not allow_redundant_targets:
                if target in targets_seen:
                    raise ValueError('Model {0} cannot be the target of '
                                     'more than one route in this list'
                                     .format(target_label))
                else:
                    targets_seen.add(target)

            # The `joins` hash defines pairs which are explicitly joined
            # via the specified field.  If no field is defined, then the
            # join field is implied or does not matter; the route is reduced
            #  to a straight lookup.
            joins[(source, target)] = field

            if symmetrical:
                if not allow_redundant_targets:
                    if source in targets_seen:
                        raise ValueError('Model {0} cannot be the target of '
                                         'more than one route in this list'
                                         .format(source_label))
                    else:
                        targets_seen.add(source)

                joins[(target, source)] = field

        return joins

    def _join_allowed(self, source, target, field=None):
        """Checks if the join between `source` and `target` via `field`
        is allowed.
        """
        join = (source, target)

        # No circles
        if target == source:
            return False

        # Prevent join to excluded models
        if target in self.excluded_models:
            return False

        # Never go back through the root
        if target == self.root_model:
            return False

        # Apply excluded joins if any
        if join in self._excluded_joins:
            _field = self._excluded_joins[join]
            if not _field:
                return False
            elif _field and _field == field:
                return False

        # Check if the join is allowed by a required rule
        for (_source, _target), _field in self._required_joins.items():
            if _target == target:
                if _source != source:
                    return False

                # If a field is supplied, check to see if the field is allowed
                # for this join.
                if field and _field and _field != field:
                    return False

        return True

    def _add_node(self, parent, model, relation, reverse, related_name,
                  accessor_name, nullable, depth):
        """Adds a node to the tree only if a node of the same `model' does not
        already exist in the tree with smaller depth. If the node is added, the
        tree traversal continues finding the node's relations.

        Conditions in which the node will fail to be added:

            - a reverse relationship is blocked via the '+'
            - the model is excluded completely
            - the model is going back the same path it came from
            - the model is circling back to the root_model
            - the model does not come from an explicitly declared parent model
        """
        # Reverse relationships
        if reverse and '+' in related_name:
            return

        node_hash = self._nodes.get(model, None)

        # don't add node if a path with a shorter depth exists. this is applied
        # after the correct join has been determined. generally if a route is
        # defined for relation, this will never be an issue since there would
        # only be one path available. if a route is not defined, the shorter
        # path will be found
        if not node_hash or node_hash['depth'] > depth:
            if node_hash:
                node_hash['parent'].remove_child(model)

            node = ModelTreeNode(model, parent, relation, reverse,
                                 related_name, accessor_name, nullable, depth)

            self._nodes[model] = {
                'parent': parent,
                'depth': depth,
                'node': node,
            }

            node = self._find_relations(node, depth)
            parent.children.append(node)

    def _find_relations(self, node, depth=0):
        """Finds all relations given a node."""
        depth += 1

        model = node.model

        # NOTE: the many-to-many relations are evaluated first to prevent
        # 'through' models being bound as a ForeignKey relationship.
        fields = sorted(model._meta.get_fields(), reverse=True,
                        key=lambda f: bool(f.many_to_many))

        # determine relational fields to determine paths
        forward_fields = [
            f for f in fields
            if (f.one_to_one or f.many_to_many or f.many_to_one)
            and (f.concrete or not f.auto_created)
            and f.rel is not None  # Generic foreign keys do not define rel.
            and self._join_allowed(f.model, f.rel.to, f)
        ]
        reverse_fields = [
            f for f in fields
            if (f.one_to_many or f.one_to_one or f.many_to_many)
            and (not f.concrete and f.auto_created)
            and self._join_allowed(f.model, f.related_model, f.field)
        ]

        def get_relation_type(f):
            if f.one_to_one:
                return 'onetone'
            elif f.many_to_many:
                return 'manytomany'
            elif f.one_to_many or f.many_to_one:
                return 'foreignkey'

        # Iterate over forward relations
        for f in forward_fields:
            null = f.many_to_many or f.null
            kwargs = {
                'parent': node,
                'model': f.rel.to,
                'relation': get_relation_type(f),
                'reverse': False,
                'related_name': f.name,
                'accessor_name': f.name,
                'nullable': null,
                'depth': depth,
            }
            self._add_node(**kwargs)

        # Iterate over reverse relations.
        for r in reverse_fields:
            kwargs = {
                'parent': node,
                'model': r.related_model,
                'relation': get_relation_type(r),
                'reverse': True,
                'related_name': r.field.related_query_name(),
                'accessor_name': r.get_accessor_name(),
                'nullable': True,
                'depth': depth,
            }
            self._add_node(**kwargs)

        return node

    def _build(self):
        node = ModelTreeNode(self.root_model)
        self._root_node = self._find_relations(node)

        self._nodes[self.root_model] = {
            'parent': None,
            'depth': 0,
            'node': self._root_node,
        }

        # store local cache of all models in this tree by name
        for model in self._nodes:
            model_name = model._meta.object_name.lower()
            app_name = model._meta.app_label

            self._model_apps.appendlist(model_name, app_name)
            self._models[(app_name, model_name)] = model

    @property
    def root_node(self):
        "Returns the `root_node` and implicitly builds the tree."
        if not hasattr(self, '_root_node'):
            self._build()
        return self._root_node

    def _node_path_to_model(self, model, node, path=[]):
        "Returns a list representing the path of nodes to the model."
        if node.model == model:
            return path

        for child in node.children:
            mpath = self._node_path_to_model(model, child, path + [child])
            # TODO why is this condition here?
            if mpath:
                return mpath

    def _node_path(self, model):
        "Returns a list of nodes thats defines the path of traversal."
        model = self.get_model(model)
        return self._node_path_to_model(model, self.root_node)

    def get_joins(self, model):
        """Returns a list of JOIN connections that can be manually applied to a
        QuerySet object. See `.add_joins()`

        This allows for the ORM to handle setting up the JOINs which may be
        different depending on the QuerySet being altered.
        """
        node_path = self._node_path(model)

        joins = []
        for i, node in enumerate(node_path):
            # ignore each subsequent first join in the set of joins for a
            # given model
            table, path_joins = node.get_joins()
            if i == 0:
                joins.append(table)
            joins.extend(path_joins)

        return joins

    def query_string(self, model):
        nodes = self._node_path(model)
        return str('__'.join(n.related_name for n in nodes))

    def query_string_for_field(self, field, operator=None, model=None):
        """Takes a `models.Field` instance and returns a query string relative
        to the root model.
        """
        if model:
            if model._meta.proxy and \
                    model._meta.proxy_for_model is not field.model:
                raise ModelTreeError('proxied model must be the field model')

        else:
            model = field.model

        # When an explicit reverse field is used, simply use it directly
        if isinstance(field, (ManyToManyRel, ManyToOneRel)):
            toks = [field.field.related_query_name()]
        else:
            path = self.query_string(model)

            if path:
                toks = [path, field.name]
            else:
                toks = [field.name]

        if operator is not None:
            toks.append(operator)

        return str('__'.join(toks))

    def query_condition(self, field, operator, value, model=None):
        "Conveniece method for constructing a `Q` object for a given field."
        lookup = self.query_string_for_field(field, operator=operator,
                                             model=model)
        return Q(**{lookup: value})

    def add_joins(self, model, queryset=None):
        """Sets up all necessary joins up to the given model on the queryset.
        Returns the alias to the model's database table.
        """
        if queryset is None:
            clone = self.get_queryset()
        else:
            clone = queryset._clone()

        alias = None

        for i, join in enumerate(self.get_joins(model)):
            if isinstance(join, BaseTable):
                alias_map = clone.query.alias_map
                if join.table_alias in alias_map or \
                        join.table_name in alias_map:
                    continue
            alias = clone.query.join(join)

        # this implies the join is redundant and occurring on the root model's
        # table
        if alias is None:
            alias = clone.query.get_initial_alias()

        return clone, alias

    def add_select(self, *fields, **kwargs):
        "Replaces the `SELECT` columns with the ones provided."
        if 'queryset' in kwargs:
            queryset = kwargs.pop('queryset')
        else:
            queryset = self.get_queryset()

        queryset.query.default_cols = False
        include_pk = kwargs.pop('include_pk', True)

        if include_pk:
            fields = [self.root_model._meta.pk] + list(fields)

        aliases = []

        for pair in fields:
            if isinstance(pair, (list, tuple)):
                model, field = pair
            else:
                field = pair
                model = field.model

            queryset, alias = self.add_joins(model, queryset)

            aliases.append(Col(alias, field, field))

        if aliases:
            queryset.query.select = aliases

        return queryset

    def get_queryset(self):
        "Returns a QuerySet relative to the `root_model`."
        return self.root_model._default_manager.get_queryset()


class LazyModelTrees(object):
    "Lazily evaluates `ModelTree` instances defined in settings."
    def __init__(self, modeltrees):
        self.modeltrees = modeltrees
        self._modeltrees = {}
        self._model_aliases = {}

    def __getitem__(self, alias):
        return self._get_or_create(alias)

    def __contains__(self, alias):
        "Checks in pre-defined definitions as well as initialized trees."
        return alias in self.modeltrees or alias in self._modeltrees

    def __len__(self):
        "Returns the number of initialized trees."
        return len(self._modeltrees)

    def __nonzero__(self):
        return True

    def _get_model_label(self, model):
        model_name = model._meta.model_name

        return '{0}.{1}'.format(model._meta.app_label, model_name)

    def _get_or_create(self, alias=None, **kwargs):
        # Echo back an existing modeltree
        if isinstance(alias, ModelTree):
            return alias

        if alias is None:
            alias = MODELTREE_DEFAULT_ALIAS

        # Qualified app.model label
        elif isinstance(alias, six.string_types) and '.' in alias:
            app_name, model_name = alias.split('.', 1)
            model = apps.get_model(app_name, model_name)

            # If this corresponds to a model, update kwargs
            if model is not None:
                # Get the non-label if it exists, fallback to alias provided
                alias = self._model_aliases.get(model, alias)
                kwargs = {'model': model}

        # Model class, get or generate alias
        elif inspect.isclass(alias) and issubclass(alias, models.Model):
            model = alias
            alias = self._model_aliases.get(model,
                                            self._get_model_label(model))
            kwargs = {'model': model}

        # Check if the modeltree is defined after parsing the alias
        if alias in self._modeltrees:
            return self._modeltrees[alias]

        # Override kwargs if settings exists for this alias. If nothing
        # exists, raise an error.
        kwargs = self.modeltrees.get(alias, kwargs)
        if not kwargs:
            raise ImproperlyConfigured('No modeltree settings defined '
                                       'for "{0}"'.format(alias))

        return self._create(alias, **kwargs)

    def _create(self, alias, **kwargs):
        tree = ModelTree(alias=alias, **kwargs)
        self._modeltrees[alias] = tree
        self._model_aliases[tree.root_model] = alias
        return self._modeltrees[alias]

    def create(self, alias, model=None, **kwargs):
        if inspect.isclass(alias) and issubclass(alias, models.Model):
            model = alias
            alias = self._get_model_label(model)
        kwargs['model'] = model
        return self._create(alias, **kwargs)

    @property
    def default(self):
        return self._get_or_create()


trees = LazyModelTrees(getattr(settings, 'MODELTREES', {}))
