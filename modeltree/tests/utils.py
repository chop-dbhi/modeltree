from django.test import TestCase
from modeltree.utils import M

__all__ = ('MTestCase',)

class MTestCase(TestCase):

    def test_variations(self):
        tests = [
            # basic, no operator
            (M(office__location='Outer Space'),
                "(AND: ('office__location', 'Outer Space'))"),
            # full, no operator
            (M(tests__office__location='Outer Space'),
                "(AND: ('office__location', 'Outer Space'))"),
            # full, operator
            (M(tests__office__location__iexact='Outer Space'),
                "(AND: ('office__location__iexact', 'Outer Space'))"),

            # alternate root, basic, no operator 
            (M('project', title__salary=100000),
                "(AND: ('employees__title__salary', 100000))"),
            # alternate root, basic, operator 
            (M('project', title__salary__gt=100000),
                "(AND: ('employees__title__salary__gt', 100000))"),
            # alternate root, full, no operator
            (M('project', tests__title__salary=100000),
                "(AND: ('employees__title__salary', 100000))"),

            # complex
            (M('project', title__salary=100000) & M(office__location='Outer Space'),
                "(AND: ('employees__title__salary', 100000), ('office__location', 'Outer Space'))"),

            (M('project', title__salary=100000) | M(office__location='Outer Space'),
                "(OR: ('employees__title__salary', 100000), ('office__location', 'Outer Space'))"),
        ]

        for m, s in tests:
            self.assertEqual(str(m), s)
