from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured
from modeltree.tree import MODELTREE_DEFAULT_ALIAS, trees
from modeltree.utils import print_traversal_tree


class Command(BaseCommand):
    """
    SYNOPSIS::

        python manage.py modeltree preview [alias | app.model]

    DESCRIPTION:

        Preview the traversal tree for defined ModelTree or bare model.

    OPTIONS:

        None

    """

    help = 'Preview the traversal tree for defined ModelTree or bare model.'

    def handle(self, *args, **options):
        if not args:
            alias = MODELTREE_DEFAULT_ALIAS
        else:
            alias = args[0]

        try:
            tree = trees[alias]
        except ImproperlyConfigured, e:
            raise CommandError(e.message)

        print_traversal_tree(tree)
