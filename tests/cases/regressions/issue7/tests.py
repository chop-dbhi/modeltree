from django.test import TestCase
from modeltree.tree import trees
from .models import A, B, C


class Test(TestCase):
    """Wrong foreign key used when constructing joins.
    https://github.com/cbmi/modeltree/issues/7
    """
    def test_fk(self):
        mt = trees.create(A)

        joins = mt.get_joins(B)
        lhs, rhs = joins[1]['connection'][2][0]
        self.assertEqual((lhs, rhs), ('study_id', 'study_id'))

        mt = trees.create(B)
        joins = mt.get_joins(A)
        lhs, rhs = joins[1]['connection'][2][0]
        self.assertEqual((lhs, rhs), ('study_id', 'study_id'))

    def test_m2m(self):
        mt = trees.create(B)

        joins = mt.get_joins(C)
        lhs, rhs = joins[1]['connection'][2][0]
        self.assertEqual((lhs, rhs), ('id', 'study_id'))

        lhs, rhs = joins[2]['connection'][2][0]
        self.assertEqual((lhs, rhs), ('some_c_id', 'c_id'))

        mt = trees.create(C)

        joins = mt.get_joins(B)
        lhs, rhs = joins[1]['connection'][2][0]
        self.assertEqual((lhs, rhs), ('c_id', 'some_c_id'))

        lhs, rhs = joins[2]['connection'][2][0]
        self.assertEqual((lhs, rhs), ('study_id', 'id'))
