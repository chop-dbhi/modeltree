import os
import sys
import django
from django.core import management

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'


django.setup()

apps = sys.argv[1:]

prefix = 'tests.cases.'

if not apps:
    apps = [
        prefix + 'core',
        prefix + 'proxy',
        prefix + 'generic',
        prefix + 'regressions',
    ]

management.call_command('test', *apps)
