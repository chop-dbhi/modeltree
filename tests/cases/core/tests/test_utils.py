from django.test import TestCase
from modeltree.utils import resolve_lookup, M, InvalidLookup
from tests.models import Office, Title, Employee, Project, Meeting


__all__ = ('LookupResolverTestCase', 'MTestCase')


class LookupResolverTestCase(TestCase):
    def test_invalid_model(self):
        tests = [
            ('tests__office', Office),
            ('title', Title),
            ('tests__title', Title),
            ('employee', Employee),
            ('tests__employee', Employee),
            ('project', Project),
            ('tests__project', Project),
            ('meeting', Meeting),
            ('tests__meeting', Meeting),
            # Blocked accessor via '+'
            ('managed_projects', Employee),
        ]

        for lookup, tree in tests:
            self.assertRaises(InvalidLookup, resolve_lookup, lookup, tree)

    def test_invalid_local(self):
        tests = [
            ('office__id', Office),
            ('tests__office__id', Office),
            ('office__location', Office),
            ('tests__office__location', Office),
            ('title__id', Title),
            ('tests__title__id', Title),
            ('title__name', Title),
            ('tests__title__name', Title),
            ('title__salary', Title),
            ('tests__title__salary', Title),
            ('employee__id', Employee),
            ('tests__employee__id', Employee),
            ('employee__first_name', Employee),
            ('tests__employee__first_name', Employee),
            ('employee__last_name', Employee),
            ('tests__employee__last_name', Employee),
            ('project__id', Project),
            ('tests__project__id', Project),
            ('project__name', Project),
            ('tests__project__name', Project),
            ('project__due_date', Project),
            ('tests__project__due_date', Project),
            ('meeting__id', Meeting),
            ('tests__meeting__id', Meeting),
            ('meeting__start_time', Meeting),
            ('tests__meeting__start_time', Meeting),
            ('meeting__end_time', Meeting),
            ('tests__meeting__end_time', Meeting),
        ]

        for lookup, tree in tests:
            self.assertRaises(InvalidLookup, resolve_lookup, lookup, tree)

    def test_not_found(self):
        tests = [
            ('name', Office),
            ('salary', Office),

            ('first_name', Office),
            ('last_name', Office),
            # Also a model name, no exception thrown
            # ('title', Office),
            # Above lookup takes precedence
            # ('office', Office),
            ('manager', Office),

            # Redundant
            # ('name', Office),
            ('employees', Office),
            # Redundant
            # ('manager', Office),
            ('due_date', Office),

            ('attendees', Office),
            # Also a model name, no exception thrown
            # ('project', Office),
            # Above lookup takes precedence
            # ('office', Office),
            ('start_time', Office),
            ('end_time', Office),
        ]

        for lookup, tree in tests:
            self.assertRaises(InvalidLookup, resolve_lookup, lookup, tree)

    def test_local(self):
        tests = [
            ('id', Office, 'id'),
            ('location', Office, 'location'),
            ('id', Title, 'id'),
            ('name', Title, 'name'),
            ('salary', Title, 'salary'),
            ('id', Employee, 'id'),
            ('first_name', Employee, 'first_name'),
            ('last_name', Employee, 'last_name'),
            ('id', Project, 'id'),
            ('name', Project, 'name'),
            ('due_date', Project, 'due_date'),
            ('id', Meeting, 'id'),
            ('start_time', Meeting, 'start_time'),
            ('end_time', Meeting, 'end_time'),
        ]

        for lookup, tree, path in tests:
            self.assertEqual(resolve_lookup(lookup, tree=tree), path)

    def test_fk(self):
        tests = [
            ('title', Employee, 'title'),
            ('office', Employee, 'office'),
            ('manager', Employee, 'manager'),
            ('manager', Project, 'manager'),
            ('project', Meeting, 'project'),
            ('office', Meeting, 'office'),
        ]

        for lookup, tree, path in tests:
            self.assertEqual(resolve_lookup(lookup, tree=tree), path)

    def test_reverse_fk(self):
        tests = [
            ('employee', Office, 'employee'),
            ('meeting', Office, 'meeting'),
            ('employee', Title, 'employee'),
            ('managed_employees', Employee, 'managed_employees'),
            ('meeting', Project, 'meeting'),
        ]

        for lookup, tree, path in tests:
            self.assertEqual(resolve_lookup(lookup, tree=tree), path)

    def test_m2m(self):
        tests = [
            ('employees', Project, 'employees'),
            ('attendees', Meeting, 'attendees'),
        ]

        for lookup, tree, path in tests:
            self.assertEqual(resolve_lookup(lookup, tree=tree), path)

    def test_reverse_m2m(self):
        tests = [
            ('project', Employee, 'project'),
            ('meeting', Employee, 'meeting'),
        ]

        for lookup, tree, path in tests:
            self.assertEqual(resolve_lookup(lookup, tree=tree), path)

    def test_arbitrary(self):
        tests = [
            ('employee__id', Office, 'employee__id'),
            ('tests__employee__id', Office, 'employee__id'),
            ('title__id', Office, 'employee__title__id'),
            ('tests__title__id', Office, 'employee__title__id'),
            ('title__name', Office, 'employee__title__name'),
            ('tests__title__name', Office, 'employee__title__name'),
            ('title__salary', Office, 'employee__title__salary'),
            ('tests__title__salary', Office, 'employee__title__salary'),
            ('employee__first_name', Office, 'employee__first_name'),
            ('tests__employee__first_name', Office, 'employee__first_name'),
            ('employee__last_name', Office, 'employee__last_name'),
            ('tests__employee__last_name', Office, 'employee__last_name'),
            ('employee__title', Office, 'employee__title'),
            ('tests__employee__title', Office, 'employee__title'),
            ('employee__office', Office, 'employee__office'),
            ('tests__employee__office', Office, 'employee__office'),
            ('employee__manager', Office, 'employee__manager'),
            ('tests__employee__manager', Office, 'employee__manager'),
            ('project__id', Office, 'employee__project__id'),
            ('tests__project__id', Office, 'employee__project__id'),
            ('project__name', Office, 'employee__project__name'),
            ('tests__project__name', Office, 'employee__project__name'),
            ('project__manager', Office, 'employee__project__manager'),
            ('tests__project__manager', Office, 'employee__project__manager'),
            ('project__due_date', Office, 'employee__project__due_date'),
            ('tests__project__due_date', Office,
             'employee__project__due_date'),
            ('project__employees', Office, 'employee__project__employees'),
            ('tests__project__employees', Office,
             'employee__project__employees'),
            ('meeting__id', Office, 'meeting__id'),
            ('tests__meeting__id', Office, 'meeting__id'),
            ('meeting__project', Office, 'meeting__project'),
            ('tests__meeting__project', Office, 'meeting__project'),
            ('meeting__office', Office, 'meeting__office'),
            ('tests__meeting__office', Office, 'meeting__office'),
        ]

        for lookup, tree, path in tests:
            self.assertEqual(resolve_lookup(lookup, tree=tree), path)


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
            (M('project', title__salary=100000) &
             M(office__location='Outer Space'),
             "(AND: ('employees__title__salary', 100000), "
             "('office__location', 'Outer Space'))"),

            (M('project', title__salary=100000) |
             M(office__location='Outer Space'),
             "(OR: ('employees__title__salary', 100000), "
             "('office__location', 'Outer Space'))"),
        ]

        for m, s in tests:
            self.assertEqual(str(m), s)
