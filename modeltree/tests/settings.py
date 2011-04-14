from django.conf.global_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

MODELTREES = {
    'default': {
        'model': 'tests.Employee'
    }
}

INSTALLED_APPS = ('modeltree',)
