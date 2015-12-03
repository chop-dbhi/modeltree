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

        # Django 1.6 decided it likes to put extra whitespace around parens
        # for some reason so we do all the comparisons here after removing
        # all whitespace from the strings to avoid test failures because of
        # arbitrary whitespace from Django >= 1.6.
        self.assertEqual(
            str(qs.query).replace(' ', ''),
            'SELECT "specimen"."ALIQUOT_ID" FROM "specimen" LEFT OUTER JOIN '
            '"link" ON ("specimen"."ALIQUOT_ID" = "link"."ALIQUOT_ID")'
            .replace(' ', ''))

        qs, alias = mt.add_joins(Subject)
        self.assertEqual(
            str(qs.query).replace(' ', ''),
            'SELECT "specimen"."ALIQUOT_ID" FROM "specimen" LEFT OUTER JOIN '
            '"link" ON ("specimen"."ALIQUOT_ID" = "link"."ALIQUOT_ID") LEFT '
            'OUTER JOIN "subject" ON ("link"."study_id" = '
            '"subject"."study_id")'
            .replace(' ', ''))
