---
layout: page
title: "Lookup Syntax"
category: ref
date: 2013-07-21 12:00:01
order: 1
---

Modeltree supports a superset of Django's [field lookup syntax](https://docs.djangoproject.com/en/1.5/topics/db/queries/#field-lookups-intro) making it transparent to perform highly relational queries. The syntax defined as follows:

```
[app__]model__field[__operator]
```

- The `model` and `field` names are required
    - See [ticket #9](https://github.com/cbmi/modeltree/issues/9) which proposes support for `field` only lookups
- The `app` portion is not required unless the `model` name is ambigious
    - That is to say, two or more models that are related to the root model have the same name. Specifying `app` differentiates which model class should be used since a model names within an app must be unique.
- The `operator` is also optional. The default Django behavior is to use the `exact` operator if none is supplied.

A typical field lookup in Django looks as follows:

```python
offices = Office.objects.filter(employee__title__salary__gt=50000)
```

This explicitly defines the path of the joins that are occurring. `Office` is related to `employee` which is related to `title` which contains the field `salary`.

Using a modeltree lookup (assuming a [`ModelTreeManager`]({% post_url 2013-07-21-managers %}) is being used), it can be reduced to:

```python
offices = Office.objects.filter(title__salary__gt=50000)
```

This can be thought of as a **flat lookup** since it removes the need to specify the intermediate relationships, i.e. `employee`. It only requires the last model and field in the path to be specified. It will attempt to resolve the flat lookup then fallback to Django's default bahavior if the lookup cannot be resolved. For example, if `Employee` was the base model rather than `Office`, the same lookup would be valid both in the flat lookup and the default lookup syntax.

```python
# Valid for either lookup syntax
Employee.objects.filter(title__salary__gt=50000)
```

#### Aside

The flat syntax may look funny and even a bit confusing since `Office` does not contain the `title` relationship. The explicitness of Django's lookup syntax is certainly more concrete, but when thinking about constructing queries, the conditions themselves are generally the first priority `salary > 50000`. It is less desirable to have to think about _how_ model _A_ is related to model _B_. 

Furthermore, this may seem not useful for a simple data model, but for highly relational/nested data, the flat lookup makes for a powerful foundation for higher level APIs (see [projects using ModelTree]({% post_url 2013-07-21-projects %})).
