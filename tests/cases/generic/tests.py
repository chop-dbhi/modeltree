from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from modeltree.tree import ModelTree


class ProxyModelTestCase(TestCase):
    def setUp(self):
        self.tree = ModelTree(model='generic.GenericModel')

    def test_content_type_fk(self):
        f = ContentType._meta.pk

        qs = self.tree.query_string_for_field(f)
        self.assertEqual(qs, 'content_type__id')
