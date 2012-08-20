# ModelTree

ModelTree is a layer that sits atop of the Django ORM providing APIs for
dynamically generating QuerySets at runtime. It manages figuring out all
necessary joins between tables based on the relationships defined in each
Model.

In most cases the way relationships are traversed (the SQL joins that
occurs) are predictable. Thus we can determine the shortest "path" between
models. For cases where this is not the case, a _router_ can be defined
to enforce a join path.

## Example

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
    office = models.ForeignKey(Office, related_name='employees')
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

Since relationships are explicitly defined models, these fields can be
introspected to determine all paths relative to a given model.

```python
>>> from modeltree.tree import trees
>>> mt = trees.create(Office)
>>> mt
<ModelTree for Office>

>>> print mt
Office
....Employee
........Project
........Title
....Meeting
```

The hierarchy above shows the relationships and their relative depths to the
`Office` model.

Let's ask the question, _show me all the offices that have employees with the
salary greater than 50,000_. We can use a special class here inspired by
the [`Q`][Q] class:

```python
>>> from modeltree.utils import M
>>> m = M(mt, title__salary__gt=50000)
>>> queryset = Office.objects.filter(m)
>>> print str(queryset.query)
SELECT "tests_office"."id", "tests_office"."location"
FROM "tests_office" INNER JOIN "tests_employee"
    ON ("tests_office"."id" = "tests_employee"."office_id")
INNER JOIN "tests_title"
    ON ("tests_employee"."title_id" = "tests_title"."id")
WHERE "tests_title"."salary" > 50000
```

A keen eye would notice that the `title__salary__gt=50000` does not include
any join through `employees`. The lookup syntax has been extended to support 
normal lookups as well as supporting `<app>__<model>__<field>__<operator>=<value>`.
The `<app>` and `<operator>` portions are optional. `<app>` is only required
if there is an ambigiously named model, i.e. two apps have a model of the same
name.

Since we are supplying the `ModelTree` instance with the lookup, it knows to
build the QuerySet relative to the `Office` model.


## Routers

Mimicked after Django's own [database routers][], a ModelTree router allows
enforcing join paths taken between model relationships. Each
route is made up of four components. Assuming some model hierarchy
exists as shown below..

```
   A
 /   \
|     C
B     |
|     D
 \   /
   E 
```

..the traversal path from `A` to `E` is ambiguous. It could
go from `A` &rarr; `B` &rarr; `E` or `A` &rarr; `C` &rarr; `D` &rarr; `E`.
By default, the shortest path is always choosen to reduce the number of joins
necessary, but if `D` did not exist..

```
   A
 /   \
B     C
 \   /
   E
```

..both paths only require two joins, thus the path that gets traversed
first will only be the chosen one.

To explicitly choose a path, a router can be defined. Below is a template
class that implements all methods, but all methods are optional. If nothing
is returned from all methods, the default behavior will occur.

```python
class Router(object):
    def source_model_for_join(self, target, root):
        pass

    def field_for_join(self, source, target, root):
        pass

    def allow_source_model(self, source, target, root):
        pass

    def allow_join_field(self, field, source, target, root):
        pass
```

- `source_model_for_join` - If there is an ambiguous path to a `target`, a
model class can be returned to enforce the which model `target` will be joined
from. Note, if a model is returned, it must directly related to the `target`
model.

- `field_for_join` - This is typically useful in the circumstance that
multiple relationships are defined on `target` to the same `source` model and
a particular path is preferred over another. 

- `allow_source_model` - This is analogous to `source_model_for_join`, but
must return `True` or `False` as to whether a `source` model is allowed to join
to `target`. Note, this does not enforce exclusivity between two models like
`source_model_for_join` does.

- `allow_join_field` - This is analogous to `field_for_join`, but
must return `True` or `False` as to whether `field` may be used to join
`source` and `target`.


[Q]: https://docs.djangoproject.com/en/dev/topics/db/queries/#complex-lookups-with-q-objects
[database routers]: https://docs.djangoproject.com/en/dev/topics/db/multi-db/#automatic-database-routing
