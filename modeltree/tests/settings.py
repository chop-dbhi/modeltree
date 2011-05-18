DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'modeltree_tests.db',
    }
}

MODELTREES = {
    'default': {
        'model': 'tests.Employee'
    },
    'project': {
        'model': 'tests.Project'
    }
}

INSTALLED_APPS = (
    'modeltree',
    'modeltree.tests'
)
