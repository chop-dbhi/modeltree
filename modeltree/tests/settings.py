DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'modeltree.db',
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

COVERAGE_MODULES = (
    'modeltree.managers',
    'modeltree.query',
    'modeltree.tree',
    'modeltree.utils',
)

TEST_RUNNER = 'modeltree.tests.coverage_test.CoverageTestRunner'
