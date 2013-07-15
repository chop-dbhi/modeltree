---
layout: default
title: "Jekyll Docs Template"
---

<div class=lead>ModelTree is a layer that sits atop the Django ORM providing APIs for dynamically generating QuerySets at runtime. It deterministically constructs all the necessary joins between tables based on the relationships defined across models.</div>


### Example

Here are a set of models representing an office setting:

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
```

In most cases the way relationships are traversed (the SQL joins that occurs) are predictable, thus we can simply assume the shortest "path" between models. A new `ModelTree` instance is created for the _root_ model of interest, say `Office`. We can print the traversal paths of all related models using the `print_path()` method.

```python
>>> from modeltree.tree import trees
>>> mt = trees.create(Office)
>>> mt
<ModelTree for Office>

>>> mt.print_path()
 "Office"
.... "Employee"
........ "Project"
........ "Title"
.... "Meeting"
```

The hierarchy above shows the relationships relative to the `Office` model. We can easily query relative to the Office model. Let's ask the question, _"show me all the offices that have employees with the salary greater than 50,000"_. We need to use a special class here inspired by the `Q` class:

```python
from modeltree.utils import M

# Pass the modeltree as the first argument, followed by the lookup.. notice
# however that the lookup seems wrong.. read more below
m = M(mt, title__salary__gt=50000)

# Pass it as you normally would a Q object
queryset = Office.objects.filter(m)
```

The result?

```sql
SELECT "tests_office"."id", "tests_office"."location"
FROM "tests_office"
    INNER JOIN "tests_employee" ON ("tests_office"."id" = "tests_employee"."office_id")
    INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id")
WHERE "tests_title"."salary" > 50000
```

The lookup keyword argument `title__salary__gt=50000` may look incorrect since the `Office` model does not have a field `title`. The `M` defines a superset of the lookup syntax and supports direct lookups based on app, model, and field, e.g. `<app>__<model>__<field>__<operator>=<value>`. The `<app>` and `<operator>` portions are optional; `<app>` is only required if there is an ambigiously named model, i.e. two apps have a model of the same name. `<operator>` is optional since Django defaults to the `exact` operator internally if none is specified.
