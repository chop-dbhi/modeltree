from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


class ModelJoinRouter(object):
    def __init__(self, routers):
        self.routers = []
        for r in routers:
            if isinstance(r, basestring):
                try:
                    module_name, klass_name = r.rsplit('.', 1)
                    module = import_module(module_name)
                except ImportError, e:
                    raise ImproperlyConfigured('Error importing model router {0}: "{1}"'.format(klass_name, e))
                try:
                    router_class = getattr(module, klass_name)
                except AttributeError:
                    raise ImproperlyConfigured('Module "{0}" does not define a model router named "{1}"'.format(module, klass_name))
                else:
                    router = router_class()
            else:
                router = r
            self.routers.append(router)

    def source_model_for_relation(self, source, root):
        """Returns the preferred model or model name as the `source` model when
        traversing the path to `target`.
        """
        for router in self.routers:
            try:
                method = router.source_model_for_relation
            except AttributeError:
                # If the router doesn't have a method, skip to the next one.
                pass
            else:
                model_name = method(source, root)
                if model_name is not None:
                    return model_name

    def join_field_for_relation(self, target, source, root):
        """Returns the preferred join field or field name between the `source` and
        `target` models. If this returns a field name, `join_allowed` will be
        ignored.
        """
        for router in self.routers:
            try:
                method = router.join_field_for_relation
            except AttributeError:
                # If the router doesn't have a method, skip to the next one.
                pass
            else:
                field_name = method(target, source, root)
                if field_name is not None:
                    return field_name

    def allow_source_model(self, target, source, root):
        """Defines whether traversing from the `source` model to the `target`
        model is allowed.
        """
        for router in self.routers:
            try:
                method = router.allow_source_model
            except AttributeError:
                # If the router doesn't have a method, skip to the next one.
                pass
            else:
                allow = method(target, source, root)
                if allow is not None:
                    return allow
        # Prevent circular traversals back to the `source` and to the `root`
        if target is source or target is root:
            return False

    def allow_join_field(self, field_name, target, source, root):
        """Defines whether traversing from the `source` model to the `target`
        model through `field` is allowed.
        """
        for router in self.routers:
            try:
                method = router.allow_source_model
            except AttributeError:
                # If the router doesn't have a method, skip to the next one.
                pass
            else:
                allow = method(field_name, target, source, root)
                if allow is not None:
                    return allow

