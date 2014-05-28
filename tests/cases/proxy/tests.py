from django.test import TestCase
from modeltree.tree import ModelTree
from .models import TargetProxy


class ProxyModelTestCase(TestCase):
    def setUp(self):
        self.tree = ModelTree(model='proxy.Root')

    def test_without_model(self):
        f = TargetProxy._meta.pk

        qs = self.tree.query_string_for_field(f)
        self.assertEqual(qs, 'standard_path__id')

    def test_with_model(self):
        f = TargetProxy._meta.pk

        qs = self.tree.query_string_for_field(f, model=TargetProxy)
        self.assertEqual(qs, 'proxy_path__id')
