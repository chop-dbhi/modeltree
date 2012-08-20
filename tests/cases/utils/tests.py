from cStringIO import StringIO
from django.test import TestCase
from modeltree.utils import print_tree
from modeltree.tree import ModelTree
from .models import Office


class UtilTestCase(TestCase):
    def test_print_tree(self):
        buff = StringIO()
        mt = ModelTree(Office)
        print_tree(mt, buff)
        buff.seek(0)
        self.assertEqual(buff.read(), 'Office\n....Employee\n........Project\n........Title\n....Meeting\n')
