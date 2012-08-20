DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'modeltree.db',
    }
}

INSTALLED_APPS = (
    'modeltree',
    'tests.cases.tree',
    'tests.cases.query',
    'tests.cases.utils',
)
