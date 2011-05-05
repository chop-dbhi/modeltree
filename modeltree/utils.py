from django.db import models
from django.db.models import loading
from django.db.models.sql.constants import QUERY_TERMS, LOOKUP_SEP

from modeltree import trees, ModelTree

class M(models.Q):
    def __init__(self, using=None, **kwargs):
        lookups = {}

        # determine the modeltree instance this should be constructed
        # relative to
        if using is None:
            tree = trees.default
        elif isinstance(using, ModelTree):
            tree = using
        else:
            tree = trees[using]

        # iterate over each kwarg and perform the conversion
        for key, value in iter(kwargs.items()):
            # split by the default separator
            toks = key.split(LOOKUP_SEP)

            if len(toks) > 4:
                raise ValueError, '%s is not a valid query lookup' % key

            app_name = model_name = field_name = operator = None

            # set operator if it exists and is valid
            if len(toks) > 2 and toks[-1] in QUERY_TERMS:
                operator = toks.pop(-1)

            # pop off the required parts
            field_name = toks.pop(-1)
            model_name = toks.pop(-1)

            # if any tokens are left, we have the name of the app
            if len(toks) > 0:
                app_name = toks.pop(-1)

            # attempt to get the field object these components represent
            field = self._get_field(app_name, model_name, field_name)

            skey = tree.query_string_for_field(field, operator=operator)
            lookups[skey] = value

        # apply 
        return super(M, self).__init__(**lookups)

    def _get_field(self, app_name=None, model_name=None, field_name=None):
        if app_name:
            model = models.get_model(app_name, model_name)
        else:
            model = None
            # attempt to find the model based on the label. since we don't
            # have the app label, if a model of the same name exists multiple
            # times, we need to throw an error.
            for app, app_models in iter(loading.cache.app_models.items()):
                if model_name in app_models:
                    if model is not None:
                        raise ValueError('the model name %s is not unique. '
                            'specify the app as well in lookup string.' % model_name)
                    model = app_models[model_name]

        if model is None:
            raise ValueError, 'no model found with name %s' % model_name

        # let the FieldDoesNotExist error bubble up
        return model._meta.get_field_by_name(field_name)[0]
