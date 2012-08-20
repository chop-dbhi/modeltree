#!/bin/sh

DJANGO_SETTINGS_MODULE='tests.settings' PYTHONPATH=. coverage run ../bin/django-admin.py test tree query utils 
coverage html
