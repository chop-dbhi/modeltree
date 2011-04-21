from django.db import models
from django.db.models import loading
from django.db.models.sql.constants import QUERY_TERMS, LOOKUP_SEP

from modeltree import trees

class AmbiguousField(Exception):
    pass


class M(models.Q):
    def __init__(self, using=None, **kwargs):
        nkwargs = {}

        if using is None:
            tree = trees.default
        else:
            tree = trees[using]

        for key, value in kwargs.items():
            toks = key.split(LOOKUP_SEP)

            app_label = model_label = field_name = operator = None

            # set operator if exists
            if len(toks) > 1:
                if toks[-1] in QUERY_TERMS:
                    operator = toks.pop(-1)

            # field_name
            field_name = toks.pop(-1)
            # model_label
            model_label = toks.pop(-1)

            # app_label also specified
            if toks:
                app_label = toks

            field = self._get_field(app_label, model_label, field_name)

            skey = tree.query_string_for_field(field, operator=operator)
            nkwargs[skey] = value

        return super(M, self).__init__(**nkwargs)

    def _get_field(self, app_label=None, model_label=None, field_name=None):
        if app_label:
            model = models.get_model(app_label, model_label)
        else:
            model = None
            # attempt to find the model based on the label. since we don't
            # have the app label, if a model of the same name exists multiple
            # times, we need to throw an error.
            for app, app_models in iter(loading.cache.app_models.items()):
                if model_label in app_models:
                    if model is not None:
                        raise ValueError('the model name %s is not unique. '
                            'specify the app as well in lookup string.' % model_label)
                    model = app_models[model_label]

        if model is None:
            raise ValueError, 'no model found with name %s' % model_label

        # let the FieldDoesNotExist error bubble up
        return model._meta.get_field_by_name(field_name)[0]
