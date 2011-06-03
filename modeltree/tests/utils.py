from django.test import TestCase
from modeltree.utils import resolve, M

__all__ = ('ModelFieldResolverTestCase', 'MTestCase')

class ModelFieldResolverTestCase(TestCase):

    def test_standard(self):
        tests = [
            ('office', 'office'),
            ('office__location', 'office__location'),
            ('tests__office__location', 'office__location'),
            ('tests__office__location__iexact', 'office__location__iexact'),
        ]

        for p, l in tests:
            self.assertEqual(resolve(p), l)

    def test_local(self):
        tests = [
            ('first_name', 'first_name'),
            ('office', 'office'),
        ]

        for p, l in tests:
            self.assertEqual(resolve(p, local=True), l)

    def test_using(self):
        using = 'project'
        tests = [
            ('title__salary', 'employees__title__salary'),
            ('title__salary__gt', 'employees__title__salary__gt'),
            ('tests__title__salary', 'employees__title__salary'),
        ]

        for p, l in tests:
            self.assertEqual(resolve(p, using=using), l)


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
