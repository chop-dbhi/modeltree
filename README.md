# ModelTree

[![Build Status](https://travis-ci.org/cbmi/modeltree.png?branch=master)](https://travis-ci.org/cbmi/modeltree) [![Coverage Status](https://coveralls.io/repos/cbmi/modeltree/badge.png)](https://coveralls.io/r/cbmi/modeltree) [![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/cbmi/modeltree/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

ModelTree is a layer that sits atop of the Django ORM providing APIs for
dynamically generating QuerySets at runtime. It manages figuring out all
necessary joins between tables based on the relationships defined in each
Model. The models below are all related in some way:

## Install

Install using [Pip](http://pypi.python.org/pypi/pip) or easy_install:

```bash
pip install modeltree
```

## Setup

Add it to `INSTALLED_APPS` in your project settings:

```python
INSTALLED_APPS = (
    ...
    'modeltree',
)
```

Define a default modeltree in your project settings:

```python
MODELTREES = {
    'default': {
        'model': 'myapp.SomeModel',
    }
}
```

See how it looks by previewing the traversal tree:

```bash
python manage.py modeltree preview
```

## The API

Let's start with a few example models:

```python
from django.db import models

class Office(models.Model):
    location = models.CharField(max_length=50)


class Title(models.Model):
    name = models.CharField(max_length=50)
    salary = models.IntegerField()


class Employee(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    title = models.ForeignKey(Title)
    office = models.ForeignKey(Office)
    is_manager = models.BooleanField(default=False)


class Project(models.Model):
    name = models.CharField(max_length=50)
    employees = models.ManyToManyField(Employee)
    manager = models.OneToOneField(Employee, related_name='managed_projects')
    due_date = models.DateField()


class Meeting(models.Model):
    attendees = models.ManyToManyField(Employee)
    project = models.ForeignKey(Project, null=True)
    office = models.ForeignKey(Office)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
```

In most cases the way relationships are traversed (the SQL joins that
occurs) are predictable. Thus we can determine the shortest "path" between
models.

```python
>>> from modeltree.tree import trees
>>> from modeltree.utils import print_traversal_tree
>>> mt = trees.create(Office)
>>> mt
<ModelTree for Office>

>>> print_traversal_tree(mt)
Office
....Employee (via employee_set)
........Project (via project_set)
........Title (via title)
....Meeting (via meeting_set)
```

The hierarchy above shows the relationships relative to the ``Office`` model.
We can easily query relative to the Office model.

Let's ask the question, "show me all the offices that have employees with the
salary greater than 50,000". We need to use a special class here inspired by
the ``Q`` class:

```python
>>> from modeltree.utils import M
>>> m = M(mt, title__salary__gt=50000)
>>> queryset = Office.objects.filter(m)
>>> str(queryset.query)
'SELECT "tests_office"."id", "tests_office"."location" FROM "tests_office" INNER
JOIN "tests_employee" ON ("tests_office"."id" = "tests_employee"."office_id")
INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id")
WHERE "tests_title"."salary" > 50000 '
```

The lookup keyword argument ``title__salary__gt=50000`` is a bit different than
the normal lookups. This syntax is ``<app>__<model>__<field>__<operator>=<value>``.
The ``<app>`` and ``<operator>`` portions are optional. ``<app>`` is only required
if there is an ambigiously named model, i.e. two apps have a model of the same
name.

Since we are supplying the ModelTree instance with the lookup, it knows to
build the QuerySet relative to the Office model.
