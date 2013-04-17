from django.test import TestCase

from modeltree.tree import trees
from .models import Specimen, Link, Subject


class Test(TestCase):
    """Wrong primary key used when constructing joins.
    https://github.com/cbmi/modeltree/issues/6
    """
    def test(self):
        mt = trees.create(Specimen)

        qs, alias = mt.add_joins(Link)
        self.assertEqual(str(qs.query), 'SELECT "specimen"."ALIQUOT_ID" FROM "specimen" LEFT OUTER JOIN "link" ON ("specimen"."ALIQUOT_ID" = "link"."ALIQUOT_ID")')

        qs, alias = mt.add_joins(Subject)
        self.assertEqual(str(qs.query), 'SELECT "specimen"."ALIQUOT_ID" FROM "specimen" LEFT OUTER JOIN "link" ON ("specimen"."ALIQUOT_ID" = "link"."ALIQUOT_ID") LEFT OUTER JOIN "subject" ON ("link"."study_id" = "subject"."study_id")')
