import os

MYSQL_USER = os.environ.get('MYSQL_USER')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')

POSTGRESQL_USER = os.environ.get('POSTGRESQL_USER')
POSTGRESQL_PASSWORD = os.environ.get('POSTGRESQL_PASSWORD')

_DATABASES = {
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'modeltree_tests.db'),
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'modeltree_tests',
        'USER': MYSQL_USER,
        'PASSWORD': MYSQL_PASSWORD,
        'HOST': '127.0.0.1',
    },
    'postgresql': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'modeltree_tests',
        'USER': POSTGRESQL_USER,
        'PASSWORD': POSTGRESQL_PASSWORD,
        'HOST': '127.0.0.1',
    }
}

# Get the selected database as an environment variable.
BACKEND = os.environ.get('DATABASE', 'sqlite')

DATABASES = {'default': _DATABASES[BACKEND]}

MODELTREES = {
    'default': {
        'model': 'tests.Employee'
    },
    'project': {
        'model': 'tests.Project'
    },
}

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'modeltree',

    'tests',
    'tests.cases.core',
    'tests.cases.proxy',
    'tests.cases.generic',
    'tests.cases.regressions',
)

SECRET_KEY = 'abc123'
