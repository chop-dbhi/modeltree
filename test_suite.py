import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

import django
from django.core import management

if django.VERSION >= (1, 7):
    django.setup()

apps = sys.argv[1:]

# Django 1.6 and beyond require the full path to the test modules while
# Django 1.5 and earlier could get by with just the module name so we inject
# a prefix if the Django version is 1.6 or higher.
if django.VERSION < (1, 6):
    prefix = ''
else:
    prefix = 'tests.cases.'

if not apps:
    apps = [
        prefix + 'core',
        prefix + 'proxy',
        prefix + 'regressions',
    ]

management.call_command('test', *apps)
