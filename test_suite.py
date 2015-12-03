import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

import django
from django.core import management

django.setup()

apps = sys.argv[1:]

prefix = 'tests.cases.'

if not apps:
    apps = [
        prefix + 'core',
        prefix + 'proxy',
        prefix + 'regressions',
    ]

management.call_command('test', *apps)
