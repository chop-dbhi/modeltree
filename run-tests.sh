#!/bin/sh

ARGS="$@"

if [ ! $ARGS ]; then
    ARGS="modeltree regressions"
fi

DJANGO_SETTINGS_MODULE='modeltree.tests.settings' PYTHONPATH=. coverage run `which django-admin.py` test $ARGS
coverage html
