try:
    # Django 1.5+
    from django.db.models.constants import LOOKUP_SEP
except ImportError:
    # Django <= 1.4
    from django.db.models.sql.constants import LOOKUP_SEP  # noqa
