#!/bin/sh

DJANGO_SETTINGS_MODULE='modeltree.tests.settings' PYTHONPATH=. coverage run ../bin/django-admin.py test modeltree
coverage html
