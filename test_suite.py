import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'modeltree.tests.settings'

from django.core import management
management.call_command('test', 'modeltree')
