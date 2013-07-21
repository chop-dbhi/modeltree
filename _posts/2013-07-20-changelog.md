---
layout: page
title: "Changelog"
category: dev
date: 2013-07-20 11:49:18
order: 1
---

#### 1.1.7

- Implement `ModelTree.__contains__` hook for checking for _pre-defined_ modeltrees

#### 1.1.6

- Fix `ModelTreeQuerySet.raw` method to use `compiler.results_iter` instead of constructing a `RawQuery`
    - See [#8](https://github.com/cbmi/modeltree/issues/8) and [cbmi/avocado#98](https://github.com/cbmi/avocado/issues/98) for the details

#### 1.1.5

- Add support for Django 1.5
- Fix Python 2.6 compatibility

#### 1.1.4

- Add improved support for defining [routes]({% post_url 2013-07-20-routes %})
- Annotate modeltree instances with it's alias if one exists
    - This prevents initializing redundant modeltrees for the same root model

#### 1.1.3

- Fix incorrect primary key field name on right-hand side of join
    - See [#6](https://github.com/cbmi/modeltree/issues/6)

#### 1.1.2

- Fix bug that lowercased the `app_name` when building a modeltree
    - App names correspond to Python package names which are (of course) case senstitive

#### 1.1.1

- Abstract out `print_travesal_tree` from `ModelTree.print_path`
- Improve modeltree creation logic
- Prevent relationships with a non-active related name from being traversed
    - See [#4](https://github.com/cbmi/modeltree/issues/4)

#### 1.1.0

- Add `ModelTree.query_condition` method for convenience
- Rename package on PyPi to just "modeltree" (from "django-modeltree")

#### 1.0.0

- Initial release
