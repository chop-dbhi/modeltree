# flake8: noqa: F405
from django.test import TestCase
from modeltree.tree import ModelTree
from tests.models import *  # noqa

__all__ = ('RouterTestCase', 'FieldRouterTestCase')


def compare_paths(self, tree, expected_paths):
    for i, model in enumerate(self.models):
        path = [n.model for n in tree._node_path(model)]
        self.assertEqual(path, expected_paths[i])


def compare_paths_with_accessor(self, tree, expected_paths):
    for i, model in enumerate(self.models):
        path = [(n.model, n.accessor_name) for n in tree._node_path(model)]
        self.assertEqual(path, expected_paths[i])


class RouterTestCase(TestCase):
    def setUp(self):
        self.models = [A, B, C, D, E, F, G, H, I, J, K]

    def test_default(self):
        tree = ModelTree(A)

        expected_paths = [
            [],
            [B],
            [C],
            [B, D],
            [B, D, E],
            [B, D, F],
            [B, G],
            [B, G, H],
            [B, G, H, I],
            [B, D, E, J],
            [B, D, E, J, K],
        ]

        compare_paths(self, tree, expected_paths)

    def test_required(self):
        "D from C rather than B (default)"

        kwargs = {
            'required_routes': [{
                'target': 'tests.D',
                'source': 'tests.C'
            }],
        }

        tree = ModelTree(A, **kwargs)

        self.assertEqual(tree._required_joins, {(C, D): None})

        self.assertTrue(tree._join_allowed(C, D))
        self.assertFalse(tree._join_allowed(B, D))

        expected_paths = [
            [],
            [B],
            [C],
            [C, D],
            [C, D, E],
            [C, D, F],
            [B, G],
            [B, G, H],
            [B, G, H, I],
            [C, D, E, J],
            [C, D, E, J, K],
        ]

        compare_paths(self, tree, expected_paths)

    def test_excluded(self):
        "Prevent D from B (go through C)"

        kwargs = {
            'excluded_routes': [
                {
                    'target': 'tests.D',
                    'source': 'tests.B'
                },
            ],
        }

        tree = ModelTree(A, **kwargs)

        self.assertEqual(tree._excluded_joins, {(B, D): None})

        self.assertTrue(tree._join_allowed(C, D))
        self.assertFalse(tree._join_allowed(B, D))

        expected_paths = [
            [],
            [B],
            [C],
            [C, D],
            [C, D, E],
            [C, D, F],
            [B, G],
            [B, G, H],
            [B, G, H, I],
            [C, D, E, J],
            [C, D, E, J, K],
        ]

        compare_paths(self, tree, expected_paths)

    def test_required_long(self):
        "G from H rather than D or B."

        kwargs = {
            'required_routes': [{
                'target': 'tests.G',
                'source': 'tests.H'
            }],
        }

        tree = ModelTree(A, **kwargs)

        self.assertEqual(tree._required_joins, {(H, G): None})

        self.assertTrue(tree._join_allowed(H, G))
        self.assertFalse(tree._join_allowed(B, G))
        self.assertFalse(tree._join_allowed(D, G))

        expected_paths = [
            [],
            [B],
            [C],
            [B, D],
            [B, D, E],
            [B, D, F],
            [B, D, F, H, G],
            [B, D, F, H],
            [B, D, F, H, I],
            [B, D, E, J],
            [B, D, E, J, K],
        ]

        compare_paths(self, tree, expected_paths)

    def test_required_excluded_combo_long(self):
        "G from H (rather than D or B), not F from D, not D from B"

        kwargs = {
            'required_routes': [{
                'target': 'tests.G',
                'source': 'tests.H'
            }],
            'excluded_routes': [{
                'target': 'tests.D',
                'source': 'tests.B',
            }, {
                'target': 'tests.F',
                'source': 'tests.D',
            }],
        }

        tree = ModelTree(A, **kwargs)

        self.assertEqual(tree._required_joins, {(H, G): None})

        self.assertEqual(tree._excluded_joins, {(B, D): None, (D, F): None})

        self.assertTrue(tree._join_allowed(C, D))
        self.assertFalse(tree._join_allowed(B, D))
        self.assertTrue(tree._join_allowed(H, G))
        self.assertTrue(tree._join_allowed(H, F))
        self.assertFalse(tree._join_allowed(B, G))
        self.assertFalse(tree._join_allowed(D, G))
        self.assertFalse(tree._join_allowed(D, F))

        expected_paths = [
            [],
            [B],
            [C],
            [C, D],
            [C, D, E],
            [C, D, E, J, F],
            [C, D, E, J, F, H, G],
            [C, D, E, J, F, H],
            [C, D, E, J, F, H, I],
            [C, D, E, J],
            [C, D, E, J, K],
        ]

        compare_paths(self, tree, expected_paths)


class FieldRouterTestCase(TestCase):
    def setUp(self):
        self.models = [A, B, C, D, E, F, G, H, I, J, K]

    def test_default(self):
        tree = ModelTree(A)

        expected_paths = [
            [],
            [(B, 'b_set')],
            [(C, 'c_set')],
            [(B, 'b_set'), (D, 'd_set')],
            [(B, 'b_set'), (D, 'd_set'), (E, 'e_set')],
            [(B, 'b_set'), (D, 'd_set'), (F, 'f')],
            [(B, 'b_set'), (G, 'g_set')],
            [(B, 'b_set'), (G, 'g_set'), (H, 'h_set')],
            [(B, 'b_set'), (G, 'g_set'), (H, 'h_set'), (I, 'i_set')],
            [(B, 'b_set'), (D, 'd_set'), (E, 'e_set'), (J, 'j_set')],
            [(B, 'b_set'), (D, 'd_set'), (E, 'e_set'), (J, 'j_set'),
             (K, 'k_set')],
        ]

        compare_paths_with_accessor(self, tree, expected_paths)

    def test_required_field(self):
        kwargs = {
            'required_routes': [{
                'target': 'tests.E',
                'source': 'tests.D',
                'field': 'D.e1_set',
            }],
        }

        tree = ModelTree(A, **kwargs)

        expected_paths = [
            [],
            [(B, 'b_set')],
            [(C, 'c_set')],
            [(B, 'b_set'), (D, 'd_set')],
            [(B, 'b_set'), (D, 'd_set'), (E, 'e1_set')],
            [(B, 'b_set'), (D, 'd_set'), (F, 'f')],
            [(B, 'b_set'), (G, 'g_set')],
            [(B, 'b_set'), (G, 'g_set'), (H, 'h_set')],
            [(B, 'b_set'), (G, 'g_set'), (H, 'h_set'), (I, 'i_set')],
            [(B, 'b_set'), (D, 'd_set'), (E, 'e1_set'), (J, 'j_set')],
            [(B, 'b_set'), (D, 'd_set'), (E, 'e1_set'), (J, 'j_set'),
             (K, 'k_set')],
        ]

        compare_paths_with_accessor(self, tree, expected_paths)

    def test_excluded_overlapping(self):
        "Prevent D from B and D from F (go through C)"

        kwargs = {
            'excluded_routes': [
                {
                    'target': 'tests.D',
                    'source': 'tests.B'
                },
                {
                    'target': 'tests.D',
                    'source': 'tests.F',
                }
            ],
        }

        tree = ModelTree(A, **kwargs)

        self.assertEqual(tree._excluded_joins, {(B, D): None,
                                                (F, D): None})

        self.assertTrue(tree._join_allowed(C, D))
        self.assertFalse(tree._join_allowed(B, D))
        self.assertFalse(tree._join_allowed(F, D))

        expected_paths = [
            [],
            [B],
            [C],
            [C, D],
            [C, D, E],
            [C, D, F],
            [B, G],
            [B, G, H],
            [B, G, H, I],
            [C, D, E, J],
            [C, D, E, J, K],
        ]

        compare_paths(self, tree, expected_paths)

    def test_required_collision(self):
        """Prevent two rules requiring the same target, e.g.
        C->D and B->D"""

        kwargs = {
            'required_routes': [{
                'target': 'tests.D',
                'source': 'tests.C'
            }, {
                'target': 'tests.D',
                'source': 'tests.B'
            }],
        }

        with self.assertRaises(ValueError):
            ModelTree(A, **kwargs)
