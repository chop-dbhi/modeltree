import sys
import inspect
from django.db import models
from django.conf import settings
from django.db.models import Q, loading
from django.db.models.related import RelatedObject
from django.core.exceptions import ImproperlyConfigured
from django.utils.datastructures import MultiValueDict

__all__ = ('ModelTree',)

MODELTREE_DEFAULT_ALIAS = 'default'


class ModelLookupError(Exception):
    pass


class ModelNotUnique(ModelLookupError):
    pass


class ModelDoesNotExist(ModelLookupError):
    pass


class ModelNotRelated(ModelLookupError):
    pass


class ModelTreeNode(object):
    def __init__(self, model, parent=None, relation=None, reverse=None,
        related_name=None, accessor_name=None, nullable=False, depth=0):

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

            `nullable` - flags whether the relationship is nullable. this can be
            implied by being a many-to-many or reversed foreign key.

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

    def __unicode__(self):
        return unicode(str(self))

    def __repr__(self):
        return '<{0}>'.format(self)

    @property
    def m2m_db_table(self):
        f = getattr(self.parent_model, self.accessor_name)
        if self.reverse:
            return f.related.field.m2m_db_table()
        else:
            return f.field.m2m_db_table()

    @property
    def m2m_field(self):
        f = getattr(self.parent_model, self.accessor_name)
        if self.reverse:
            return f.related.field.m2m_column_name()
        else:
            return f.field.m2m_column_name()

    @property
    def m2m_reverse_field(self):
        f = getattr(self.parent_model, self.accessor_name)
        if self.reverse:
            return f.related.field.m2m_reverse_name()
        else:
            return f.field.m2m_reverse_name()

    @property
    def foreignkey_field(self):
        f = getattr(self.parent_model, self.accessor_name)
        if self.reverse:
            return f.related.field.column
        else:
            return f.field.column

    def get_joins(self, **kwargs):
        """Returns a list of connections that need to be added to a
        QuerySet object that properly joins this model and the parent.
        """
        kwargs.setdefault('nullable', self.nullable)
        kwargs.setdefault('outer_if_first', self.nullable)

        joins = []
        # setup initial FROM clause
        copy = kwargs.copy()
        copy['connection'] = (None, self.parent.db_table, None, None)
        joins.append(copy)

        # setup two connections for m2m
        if self.relation == 'manytomany':
            c1 = (
                self.parent.db_table,
                self.m2m_db_table,
                self.parent.pk_column,
                self.m2m_reverse_field if self.reverse else \
                    self.m2m_field,
            )

            c2 = (
                self.m2m_db_table,
                self.db_table,
                self.m2m_field if self.reverse else \
                    self.m2m_reverse_field,
                self.pk_column,
            )

            copy = kwargs.copy()
            copy['connection'] = c1
            joins.append(copy)

            copy = kwargs.copy()
            copy['connection'] = c2
            joins.append(copy)

        else:
            c1 = (
                self.parent.db_table,
                self.db_table,
                self.parent.pk_column if self.reverse else \
                    self.foreignkey_field,
                self.foreignkey_field if self.reverse else \
                    self.parent.pk_column,
            )

            copy = kwargs.copy()
            copy['connection'] = c1
            joins.append(copy)

        return joins

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

            (<source>, <target>, <join_field>, <symmetrical>)

        The `source` model defines the model where the join is being created
        from (the left side of the join). The `target` model defines the
        target model (the right side of the join). `join_field` is optional,
        but explicitly defines the model field that will be joined across. this
        is useful if there are more than one foreign key relationships on the
        target model. Finally, `symmetrical` is an optional boolean that
        ensures when the target and source models switch sides, the same join
        occurs on the same field.
    """
    def __init__(self, model, exclude=(), routes=()):
        self.root_model = self.get_model(model, local=False)

        self.exclude = [self.get_model(label, local=False) \
            for label in exclude]

        self._routes, self._tos = self._build_routes(routes)

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
                    'Specify the app name as well.'.format(model_name))

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
            model = models.get_model(app_name, model_name)
        else:
            # Attempt to find the model based on the name. Since we don't
            # have the app name, if a model of the same name exists multiple
            # times, we need to throw an error.
            for app, app_models in loading.cache.app_models.items():
                if model_name in app_models:
                    if model is not None:
                        raise ModelNotUnique('The model "{0}" is not unique. '
                            'Specify the app name as well.'.format(model_name))
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
        if inspect.isclass(model_name) and issubclass(model_name, models.Model):
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
                    app_name, model_name = model_name.split('.')
                model_name = model_name.lower()

            if app_name:
                app_name = app_name.lower()

            if local:
                model = self._get_local_model(model_name, app_name)
            else:
                model = self._get_model(model_name, app_name)

        # both mechanisms above may result in no model being found
        if model is None:
            if local:
                raise ModelNotRelated('No model found named "{0}"'.format(model_name))
            else:
                raise ModelDoesNotExist('No model found named "{0}"'.format(model_name))

        return model

    def get_field(self, name, model=None):
        if model is None:
            model = self.root_model
        return model._meta.get_field_by_name(name)[0]

    def _build_routes(self, routes):
        "Routes provide a means of specifying JOINs between two tables."
        rts = {}
        tos = {}

        if routes:
            for route in routes:

                source_label, target_label, join_field, symmetrical = route

                # get models
                source = self.get_model(source_label, local=False)
                target = self.get_model(target_label, local=False)

                field = None

                # get field
                if join_field is not None:
                    model_name, field_name = join_field.split('.')
                    model_name = model_name.lower()

                    # determine which model the join field specified exists on
                    if model_name == source.__name__.lower():
                        field = self.get_field(field_name, source)
                    elif model_name == target.__name__.lower():
                        field = self.get_field(field_name, target)
                    else:
                        raise TypeError('model for join_field, "{0}", '
                            'does not exist'.format(field_name))

                # the `rts` hash defines pairs which are explicitly joined
                # via the specified field
                if field:
                    rts[(source, target)] = field
                    if symmetrical:
                        rts[(target, source)] = field

                # if no field is defined, then the join field is implied or
                # does not matter. the route is reduced to a straight lookup
                else:
                    tos[target] = source

        return rts, tos

    def _filter_one2one(self, field):
        """Tests if the field is a OneToOneField.

        If a route exists for this field's model and it's target model, ensure
        this is the field that should be used to join the the two tables.
        """
        if isinstance(field, models.OneToOneField):
            # route has been defined with a specific field required
            tup = (field.model, field.rel.to)
            # skip if not the correct field
            if not self._routes.has_key(tup) or self._routes.get(tup) is field:
                return field

    def _filter_related_one2one(self, rel):
        """Tests if this RelatedObject represents a OneToOneField.

        If a route exists for this field's model and it's target model, ensure
        this is the field that should be used to join the the two tables.
        """
        field = rel.field
        if isinstance(field, models.OneToOneField):
            # route has been defined with a specific field required
            tup = (rel.model, field.model)
            # skip if not the correct field
            if not self._routes.has_key(tup) or self._routes.get(tup) is field:
                return rel

    def _filter_fk(self, field):
        """Tests if this field is a ForeignKey.

        If a route exists for this field's model and it's target model, ensure
        this is the field that should be used to join the the two tables.
        """
        if isinstance(field, models.ForeignKey):
            # route has been defined with a specific field required
            tup = (field.model, field.rel.to)
            # skip if not the correct field
            if not self._routes.has_key(tup) or self._routes.get(tup) is field:
                return field

    def _filter_related_fk(self, rel):
        """Tests if this RelatedObject represents a ForeignKey.

        If a route exists for this field's model and it's target model, ensure
        this is the field that should be used to join the the two tables.
        """
        field = rel.field
        if isinstance(field, models.ForeignKey):
            # route has been defined with a specific field required
            tup = (rel.model, field.model)
            # skip if not the correct field
            if not self._routes.has_key(tup) or self._routes.get(tup) is field:
                return rel

    def _filter_m2m(self, field):
        """Tests if this field is a ManyToManyField.

        If a route exists for this field's model and it's target model, ensure
        this is the field that should be used to join the the two tables.
        """
        if isinstance(field, models.ManyToManyField):
            # route has been defined with a specific field required
            tup = (field.model, field.rel.to)
            # skip if not the correct field
            if not self._routes.has_key(tup) or self._routes.get(tup) is field:
                return field

    def _filter_related_m2m(self, rel):
        """Tests if this RelatedObject represents a ManyToManyField.

        If a route exists for this field's model and it's target model, ensure
        this is the field that should be used to join the the two tables.
        """
        field = rel.field
        if isinstance(field, models.ManyToManyField):
            # route has been defined with a specific field required
            tup = (rel.model, field.model)
            # given this route, check if this is the correct field to JOIN on.
            if not self._routes.has_key(tup) or self._routes.get(tup) is field:
                return rel

    def _add_node(self, parent, model, relation, reverse, related_name,
        accessor_name, nullable, depth):
        """Adds a node to the tree only if a node of the same `model' does not
        already exist in the tree with smaller depth. If the node is added, the
        tree traversal continues finding the node's relations.

        Conditions in which the node will fail to be added:

            - the model is excluded completely
            - the model is going back the same path it came from
            - the model is circling back to the root_model
            - the model does not come from an explicitly declared parent model
        """
        exclude = set(self.exclude + [parent.parent_model, self.root_model])

        # ignore excluded models and prevent circular paths
        if model in exclude:
            return

        # if a route exists, only allow the model to be added if coming from the
        # specified parent.model
        if self._tos.has_key(model) and self._tos.get(model) is not parent.model:
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

            self._nodes[model] = {'parent': parent, 'depth': depth,
                'node': node}

            node = self._find_relations(node, depth)
            parent.children.append(node)

    def _find_relations(self, node, depth=0):
        """Finds all relations given a node.

        NOTE: the many-to-many relations are evaluated first to prevent
        'through' models being bound as a ForeignKey relationship.
        """
        depth += 1

        model = node.model

        # determine relational fields to determine paths
        forward_fields = model._meta.fields
        reverse_fields = model._meta.get_all_related_objects()

        forward_o2o = filter(self._filter_one2one, forward_fields)
        reverse_o2o = filter(self._filter_related_one2one, reverse_fields)

        forward_fk = filter(self._filter_fk, forward_fields)
        reverse_fk = filter(self._filter_related_fk, reverse_fields)

        forward_m2m = filter(self._filter_m2m, model._meta.many_to_many)
        reverse_m2m = filter(self._filter_related_m2m, model._meta.get_all_related_many_to_many_objects())

        # iterate m2m relations
        for f in forward_m2m:
            kwargs = {
                'parent': node,
                'model': f.rel.to,
                'relation': 'manytomany',
                'reverse': False,
                'related_name': f.name,
                'accessor_name': f.name,
                'nullable': True,
                'depth': depth,
            }
            self._add_node(**kwargs)

        # iterate over related m2m fields
        for r in reverse_m2m:
            kwargs = {
                'parent': node,
                'model': r.model,
                'relation': 'manytomany',
                'reverse': True,
                'related_name': r.field.related_query_name(),
                'accessor_name': r.get_accessor_name(),
                'nullable': True,
                'depth': depth,
            }
            self._add_node(**kwargs)

        # iterate over one2one fields
        for f in forward_o2o:
            kwargs = {
                'parent': node,
                'model': f.rel.to,
                'relation': 'onetoone',
                'reverse': False,
                'related_name': f.name,
                'accessor_name': f.name,
                'nullable': False,
                'depth': depth,
            }
            self._add_node(**kwargs)

        # iterate over related one2one fields
        for r in reverse_o2o:
            kwargs = {
                'parent': node,
                'model': r.model,
                'relation': 'onetoone',
                'reverse': True,
                'related_name': r.field.related_query_name(),
                'accessor_name': r.get_accessor_name(),
                'nullable': False,
                'depth': depth,
            }
            self._add_node(**kwargs)

        # iterate over fk fields
        for f in forward_fk:
            kwargs = {
                'parent': node,
                'model': f.rel.to,
                'relation': 'foreignkey',
                'reverse': False,
                'related_name': f.name,
                'accessor_name': f.name,
                'nullable': f.null,
                'depth': depth,
            }
            self._add_node(**kwargs)

        # iterate over related foreign keys
        for r in reverse_fk:
            kwargs = {
                'parent': node,
                'model': r.model,
                'relation': 'foreignkey',
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

    def get_joins(self, model, **kwargs):
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
            if i > 0:
                joins.extend(node.get_joins(**kwargs)[1:])
            else:
                joins.extend(node.get_joins(**kwargs))
        return joins

    def query_string(self, model):
        nodes = self._node_path(model)
        return str('__'.join(n.related_name for n in nodes))

    def query_string_for_field(self, field, operator=None):
        """Takes a `models.Field` instance and returns a query string relative
        to the root model.
        """
        # When an explicit reverse field is used, simply use it directly
        if isinstance(field, RelatedObject):
            path = [field.field.related_query_name()]
        else:
            nodes = self._node_path(field.model)
            path = [n.related_name for n in nodes] + [field.name]

        if operator is not None:
            path.append(operator)
        return str('__'.join(path))

    def query_condition(self, field, operator, value):
        "Conveniece method for constructing a `Q` object for a given field."
        lookup = self.query_string_for_field(field, operator)
        return Q(**{lookup: value})

    def add_joins(self, model, queryset=None, **kwargs):
        """Sets up all necessary joins up to the given model on the queryset.
        Returns the alias to the model's database table.
        """
        if queryset is None:
            clone = self.get_queryset()
        else:
            clone = queryset._clone()

        alias = None
        for i, join in enumerate(self.get_joins(model, **kwargs)):
            alias = clone.query.join(**join)

        # this implies the join is redudant and occuring on the root model's
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

        include_pk = kwargs.pop('include_pk', True)

        if include_pk:
            fields = [self.root_model._meta.pk] + list(fields)

        aliases = []

        for field in fields:
            queryset, alias = self.add_joins(field.model, queryset, **kwargs)
            aliases.append((alias, field.column))

        if aliases:
            queryset.query.select = aliases
        return queryset

    def get_queryset(self):
        "Returns a QuerySet relative to the `root_model`."
        return self.root_model._default_manager.get_query_set()

    def print_path(self, node=None, depth=0):
        "Traverses the entire tree and prints a hierarchical view to stdout."
        if node is None:
            node = self.root_node

        if node:
            sys.stdout.write('.' * depth * 4)
            sys.stdout.write(' {0}\n'.format(node.model_name))

        if node.children:
            depth += 1
            for x in node.children:
                self.print_path(x, depth)


class LazyModelTrees(object):
    "Lazily evaluates `ModelTree` instances defined in settings."
    def __init__(self, modeltrees):
        self.modeltrees = modeltrees
        self._modeltrees = {}

    def __getitem__(self, alias):
        if alias is None:
            return self.default

        if isinstance(alias, ModelTree):
            return alias

        if inspect.isclass(alias) and issubclass(alias, models.Model):
            return self.create(alias)

        # determine the modeltree instance this should be constructed
        # relative to
        if alias not in self._modeltrees:
            try:
                kwargs = self.modeltrees[alias]
            except KeyError:
                raise ImproperlyConfigured('No modeltree settings defined for "{0}"'.format(alias))

            self._modeltrees[alias] = ModelTree(**kwargs)
        return self._modeltrees[alias]

    @property
    def default(self):
        return self[MODELTREE_DEFAULT_ALIAS]

    def create(self, model):
        if model not in self._modeltrees:
            self._modeltrees[model] = ModelTree(model)
        return self._modeltrees[model]


trees = LazyModelTrees(getattr(settings, 'MODELTREES', {}))
